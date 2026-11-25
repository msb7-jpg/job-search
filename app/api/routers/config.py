from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.schemas import BlacklistCompanyRequest, BlacklistCompanyResponse
from app.core.user_config import (
    UserSearchConfig,
    add_company_to_blacklist,
    load_search_config,
    save_search_config,
)
from app.db import ignore_jobs_by_company

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=UserSearchConfig)
def api_get_config() -> UserSearchConfig:
    return load_search_config()


@router.put("", response_model=UserSearchConfig)
def api_update_config(payload: UserSearchConfig) -> UserSearchConfig:
    return save_search_config(payload)


@router.post("/blacklist", response_model=BlacklistCompanyResponse)
def api_blacklist_company(
    payload: BlacklistCompanyRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> BlacklistCompanyResponse:
    updated = add_company_to_blacklist(payload.company_name)
    ignored = 0
    if payload.ignore_existing:
        ignored = ignore_jobs_by_company(session, payload.company_name)
    return BlacklistCompanyResponse(
        blacklisted_companies=updated.blacklisted_companies,
        ignored_jobs_count=ignored,
    )
