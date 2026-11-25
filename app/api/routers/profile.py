from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_settings
from app.tailor.models import MasterProfile, ParsedResumeResult, load_master_profile, save_master_profile
from app.tailor.parser import ResumeParseError, extract_text_from_upload, parse_resume_with_llm

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=MasterProfile)
def api_get_profile() -> MasterProfile:
    return load_master_profile()


@router.put("", response_model=MasterProfile)
def api_update_profile(payload: MasterProfile) -> MasterProfile:
    return save_master_profile(payload)


@router.post("/parse", response_model=ParsedResumeResult)
async def api_parse_resume(
    raw_text: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> ParsedResumeResult:
    extracted = (raw_text or "").strip()
    if file is not None:
        content = await file.read()
        extracted = extract_text_from_upload(file.filename or "resume.txt", content)

    if not extracted:
        raise HTTPException(status_code=400, detail="Envie um arquivo (.pdf, .md, .txt) ou cole o texto do currículo.")

    try:
        return await run_in_threadpool(parse_resume_with_llm, extracted, get_settings())
    except ResumeParseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
