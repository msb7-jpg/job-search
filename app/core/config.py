import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.models.enums import ProxyStrategyEnum, TimeFilterEnum

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    # Diretórios e Banco de Dados
    project_root: Path = PROJECT_ROOT
    app_dir: Path = APP_DIR
    data_dir: Path = DATA_DIR
    database_path: Path = Field(default_factory=lambda: Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "job_search.db"))))

    # Filtros Globais de Busca e Provedores
    localizacao_linkedin: str = "Brazil"
    provedores_desabilitados: list[str] = Field(default_factory=list)
    filtro_tempo: TimeFilterEnum = TimeFilterEnum.ULTIMAS_24H
    filtro_tempo_ats: TimeFilterEnum = TimeFilterEnum.QUALQUER_DATA
    apenas_remoto: bool = True
    senioridade_filtro: str = "JUNIOR"
    threshold_minimo_match: int = 60
    max_paginas_jobs: int = 10
    max_paginas_gupy: int = 5
    max_workers_ats: int = 20
    enriquecer_detalhes_inhire: bool = True
    inhire_tenants_file: Path = Field(default_factory=lambda: APP_DIR / "providers" / "inhire" / "data" / "inhire_tenants.json")

    # Flags de Comportamento e Proxy
    usar_proxy: bool = True
    enriquecer_detalhes: bool = True
    estrategia_proxy: ProxyStrategyEnum = ProxyStrategyEnum.REACTIVE_CIRCUIT_BREAKER
    proxy_fallback_direto: bool = True
    proxy_min_ready_threshold: int = 15
    proxy_connect_timeout: float = 2.0
    proxy_read_timeout: float = 3.0
    proxy_ttl_seconds: int = 900
    proxy_tier_a_ttl_seconds: int = 1800
    proxy_tier_a_cache_file: Path = Field(default_factory=lambda: DATA_DIR / "proxy_tier_a.json")

    # Filtro Semântico LLM (Padrão Universal OpenAI-Compatible)
    usar_filtro_llm: bool = Field(default_factory=lambda: os.getenv("USAR_FILTRO_LLM", "true").lower() in ("true", "1", "yes"))
    llm_base_url: str = Field(
        default_factory=lambda: os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "http://127.0.0.1:8765/v1"
    )
    llm_model_name: str = Field(default_factory=lambda: os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL_NAME") or "gemini-3.8-flash")
    llm_api_key: str = Field(default_factory=lambda: os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "not-needed")
    llm_timeout: int = Field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT", "60")))
    llm_max_workers: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_WORKERS", "4")))
    max_anos_experiencia: int = Field(default_factory=lambda: int(os.getenv("MAX_ANOS_EXPERIENCIA", "2")))
    caminho_curriculo_md: Path = Field(
        default_factory=lambda: Path(os.getenv("CAMINHO_CURRICULO_MD", "/home/miguelsb/workspace/auto-apply/resume-pt.md"))
    )

    # Concorrência e HTTP
    max_workers_jobs: int = 25
    max_concurrency_proxies: int = 250
    http_timeout: int = 4
    http_max_retries: int = 3

    # Relatórios Executivos em PDF (Mantidos até a construção do Dashboard)
    output_pdf_report: Path = Field(
        default_factory=lambda: DATA_DIR / f"relatorio_vagas_qualificadas_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    )
    output_rejeitadas_pdf_report: Path = Field(
        default_factory=lambda: DATA_DIR / f"relatorio_vagas_rejeitadas_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    )


settings = Settings()
