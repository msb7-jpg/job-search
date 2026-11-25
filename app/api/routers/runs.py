import json
import queue
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.api.run_manager import run_manager
from app.api.schemas import RunsOverviewResponse, ScrapeRunSchema, TriggerRunRequest
from app.db import count_pending_llm_jobs, list_scrape_runs
from app.pipeline import rejudge_pending_jobs, run_pipeline
from app.providers import ProviderRegistry

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("", response_model=RunsOverviewResponse)
def api_list_runs(session: Annotated[Session, Depends(get_db_session)]) -> RunsOverviewResponse:
    settings = get_settings()
    runs = list_scrape_runs(session, limit=25)
    pending_count = count_pending_llm_jobs(session)
    providers = [provider.provider_name for provider in ProviderRegistry.get_active_providers(settings)]

    return RunsOverviewResponse(
        runs=[
            ScrapeRunSchema(
                id=run_row.id,
                started_at=run_row.started_at,
                finished_at=run_row.finished_at,
                status=run_row.status,
                providers=json.loads(run_row.providers_json or "[]"),
                total_fetched=run_row.total_fetched,
                total_new=run_row.total_new,
                total_approved=run_row.total_approved,
                total_rejected=run_row.total_rejected,
                error_log=run_row.error_log,
            )
            for run_row in runs
        ],
        pending_llm_count=pending_count,
        available_providers=providers,
        is_running=run_manager.is_running,
        active_run_id=run_manager.active_run_id,
    )


@router.post("/trigger")
def api_trigger_run(payload: TriggerRunRequest) -> dict[str, str]:
    settings = get_settings().model_copy()
    settings.usar_proxy = payload.use_proxy
    settings.usar_filtro_llm = payload.use_llm

    run_id = run_manager.start_run(
        kind="scrape",
        target_fn=lambda: run_pipeline(
            settings=settings,
            providers_filter=payload.providers,
            skip_pdf=True,
        ),
    )
    if run_id is None:
        raise HTTPException(status_code=409, detail="Já existe uma execução em andamento.")
    return {"run_id": run_id, "status": "RUNNING"}


@router.post("/rejudge")
def api_trigger_rejudge() -> dict[str, str]:
    settings = get_settings().model_copy()
    run_id = run_manager.start_run(
        kind="rejudge",
        target_fn=lambda: rejudge_pending_jobs(settings=settings, skip_pdf=True),
    )
    if run_id is None:
        raise HTTPException(status_code=409, detail="Já existe uma execução em andamento.")
    return {"run_id": run_id, "status": "RUNNING"}


@router.get("/{run_id}/stream")
def api_stream_run_logs(run_id: str) -> StreamingResponse:
    subscription = run_manager.subscribe(run_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Execução não encontrada.")

    snapshot, live_queue, already_finished = subscription

    def _event_generator():
        for line in snapshot:
            yield f"data: {json.dumps({'type': 'log', 'line': line})}\n\n"

        if already_finished:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        while True:
            try:
                item = live_queue.get(timeout=15.0)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            if item is None:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            yield f"data: {json.dumps({'type': 'log', 'line': item})}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
