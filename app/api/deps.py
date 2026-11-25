from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings, settings as default_settings
from app.db import init_db


@lru_cache(maxsize=4)
def _get_engine_for_path(db_path_str: str) -> Engine:
    return init_db(Path(db_path_str))


def get_settings() -> Settings:
    return default_settings


def get_db_session() -> Generator[Session]:
    cfg = get_settings()
    engine = _get_engine_for_path(str(cfg.database_path))
    with Session(engine) as session:
        yield session
