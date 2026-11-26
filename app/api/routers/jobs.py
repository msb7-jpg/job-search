import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.schemas import (
    ApplicationSchema,
    JobDetailSchema,
    JobEvaluationSchema,
    JobListResponse,
    JobSummarySchema,
    SiblingJobSchema,
    TailoredResumeSummarySchema,
    UpdateJobStatusRequest,
)
from app.db import (
    JobRow,
    get_job_detail,
    get_latest_tailored_resume,
    list_jobs,
    update_application_status,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _serialize_job_summary(row: JobRow) -> JobSummarySchema:
    evaluation_schema = None
    if row.evaluation is not None:
        ev = row.evaluation
        evaluation_schema = JobEvaluationSchema(
            layer1_score=ev.layer1_score,
            matched_skills=json.loads(ev.matched_skills_json or "[]"),
            missing_skills=json.loads(ev.missing_skills_json or "[]"),
            llm_status=ev.llm_status,
            llm_approved=ev.llm_approved,
            llm_score=ev.llm_score,
            llm_reasoning=ev.llm_reasoning,
            discard_layer=ev.discard_layer,
            discard_reason=ev.discard_reason,
        )

    application_schema = None
    if row.application is not None:
        app_row = row.application
        application_schema = ApplicationSchema(
            status=app_row.status,
            notes=app_row.notes,
            applied_at=app_row.applied_at,
            updated_at=app_row.updated_at,
        )

    return JobSummarySchema(
        id=row.id,
        url_hash=row.url_hash,
        canonical_key=row.canonical_key,
        provider=row.provider,
        title=row.title,
        company=row.company,
        location=row.location,
        work_model=row.work_model,
        seniority=row.seniority,
        url=row.url,
        posted_at=row.posted_at,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
        evaluation=evaluation_schema,
        application=application_schema,
    )


@router.get("", response_model=JobListResponse)
def api_list_jobs(
    session: Annotated[Session, Depends(get_db_session)],
    status: str | None = Query(default=None),
    llm_status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    min_score: int | None = Query(default=None, ge=0, le=100),
    discard_layer: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> JobListResponse:
    rows, total = list_jobs(
        session,
        status=status,
        llm_status=llm_status,
        provider=provider,
        min_score=min_score,
        discard_layer=discard_layer,
        search=search,
        limit=limit,
        offset=offset,
    )
    return JobListResponse(
        items=[_serialize_job_summary(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobDetailSchema)
def api_get_job(job_id: int, session: Annotated[Session, Depends(get_db_session)]) -> JobDetailSchema:
    row, siblings = get_job_detail(session, job_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    summary = _serialize_job_summary(row)
    latest_tailored = get_latest_tailored_resume(session, job_id)
    tailored_schema = None
    if latest_tailored is not None:
        tailored_schema = TailoredResumeSummarySchema(
            id=latest_tailored.id,
            base_profile_version=latest_tailored.base_profile_version,
            diff=json.loads(latest_tailored.diff_json or "{}"),
            cover_letter_md=latest_tailored.cover_letter_md,
            qa_answers=json.loads(latest_tailored.qa_answers_json or "{}"),
            pdf_path=latest_tailored.pdf_path,
            verification_warnings=json.loads(latest_tailored.verification_warnings_json or "[]"),
            created_at=latest_tailored.created_at,
        )

    return JobDetailSchema(
        **summary.model_dump(),
        description_md=row.description_md or "",
        siblings=[
            SiblingJobSchema(
                id=sibling.id,
                provider=sibling.provider,
                title=sibling.title,
                company=sibling.company,
                location=sibling.location,
                url=sibling.url,
            )
            for sibling in siblings
        ],
        tailored_resume=tailored_schema,
    )


@router.patch("/{job_id}/status", response_model=ApplicationSchema)
def api_update_job_status(
    job_id: int,
    payload: UpdateJobStatusRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ApplicationSchema:
    try:
        app_row = update_application_status(
            session,
            job_id=job_id,
            status=payload.status,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if app_row is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    return ApplicationSchema(
        status=app_row.status,
        notes=app_row.notes,
        applied_at=app_row.applied_at,
        updated_at=app_row.updated_at,
    )
