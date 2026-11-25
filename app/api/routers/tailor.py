import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.db import JobRow, TailoredResumeRow, get_latest_tailored_resume, update_application_status
from app.tailor.models import TailoredDiff, load_master_profile
from app.tailor.renderer import render_tailored_resume_pdf
from app.tailor.service import TailorGenerationError, generate_tailored_diff, verify_tailored_diff

router = APIRouter(prefix="/api/jobs", tags=["tailor"])


class TailorRequest(BaseModel):
    include_cover_letter: bool = False


class PatchTailorRequest(BaseModel):
    diff: TailoredDiff
    cover_letter_md: str = ""


class TailorResponse(BaseModel):
    id: int
    job_id: int
    diff: TailoredDiff
    cover_letter_md: str
    qa_answers: dict[str, str]
    pdf_path: str | None = None
    page_count: int = 1
    verification_warnings: list[dict]


@router.post("/{job_id}/tailor", response_model=TailorResponse)
def api_tailor_job(
    job_id: int,
    payload: TailorRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> TailorResponse:
    job_row = session.get(JobRow, job_id)
    if job_row is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    profile = load_master_profile()
    try:
        diff, warnings = generate_tailored_diff(
            profile=profile,
            job_title=job_row.title,
            company=job_row.company,
            description_md=job_row.description_md or "",
            include_cover_letter=payload.include_cover_letter,
            settings=get_settings(),
        )
    except TailorGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pdf_path, page_count, overflow_warning = render_tailored_resume_pdf(
        job_id=job_id,
        profile=profile,
        diff=diff,
    )
    if overflow_warning is not None:
        warnings.append(overflow_warning)

    warnings_dicts = [warning.model_dump(mode="json") for warning in warnings]
    row = TailoredResumeRow(
        job_id=job_id,
        base_profile_version=profile.version,
        diff_json=json.dumps(diff.model_dump(mode="json"), ensure_ascii=False),
        cover_letter_md=diff.cover_letter_md,
        qa_answers_json=json.dumps(profile.qa_vault, ensure_ascii=False),
        pdf_path=str(pdf_path),
        verification_warnings_json=json.dumps(warnings_dicts, ensure_ascii=False),
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    if job_row.application and job_row.application.status in ("NEW", "SAVED"):
        update_application_status(session, job_id=job_id, status="TAILORING")

    return TailorResponse(
        id=row.id,
        job_id=job_id,
        diff=diff,
        cover_letter_md=row.cover_letter_md,
        qa_answers=profile.qa_vault,
        pdf_path=row.pdf_path,
        page_count=page_count,
        verification_warnings=warnings_dicts,
    )


@router.patch("/{job_id}/tailor", response_model=TailorResponse)
def api_update_tailor(
    job_id: int,
    payload: PatchTailorRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> TailorResponse:
    job_row = session.get(JobRow, job_id)
    if job_row is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    profile = load_master_profile()
    warnings = verify_tailored_diff(profile, payload.diff)
    pdf_path, page_count, overflow_warning = render_tailored_resume_pdf(
        job_id=job_id,
        profile=profile,
        diff=payload.diff,
    )
    if overflow_warning is not None:
        warnings.append(overflow_warning)

    warnings_dicts = [warning.model_dump(mode="json") for warning in warnings]
    latest = get_latest_tailored_resume(session, job_id)
    if latest is None:
        latest = TailoredResumeRow(job_id=job_id, base_profile_version=profile.version)
        session.add(latest)

    latest.diff_json = json.dumps(payload.diff.model_dump(mode="json"), ensure_ascii=False)
    latest.cover_letter_md = payload.cover_letter_md or payload.diff.cover_letter_md
    latest.qa_answers_json = json.dumps(profile.qa_vault, ensure_ascii=False)
    latest.pdf_path = str(pdf_path)
    latest.verification_warnings_json = json.dumps(warnings_dicts, ensure_ascii=False)
    session.commit()
    session.refresh(latest)

    return TailorResponse(
        id=latest.id,
        job_id=job_id,
        diff=payload.diff,
        cover_letter_md=latest.cover_letter_md,
        qa_answers=profile.qa_vault,
        pdf_path=latest.pdf_path,
        page_count=page_count,
        verification_warnings=warnings_dicts,
    )


@router.get("/{job_id}/resume.pdf")
def api_get_resume_pdf(
    job_id: int,
    session: Annotated[Session, Depends(get_db_session)],
) -> FileResponse:
    latest = get_latest_tailored_resume(session, job_id)
    if latest is None or not latest.pdf_path:
        raise HTTPException(status_code=404, detail="Currículo adaptado ainda não gerado para esta vaga.")

    pdf_file = Path(latest.pdf_path)
    if not pdf_file.exists():
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado no disco.")

    return FileResponse(
        path=pdf_file,
        media_type="application/pdf",
        filename=f"resume_job_{job_id}.pdf",
        headers={"Content-Disposition": f'inline; filename="resume_job_{job_id}.pdf"'},
    )
