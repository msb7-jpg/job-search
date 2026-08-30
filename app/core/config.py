from pathlib import Path

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SEARXNG_COMPOSE_DIR = PROJECT_ROOT / "searxng"

class Settings(BaseModel):
    # Diretórios
    project_root: Path = PROJECT_ROOT
    app_dir: Path = APP_DIR
    data_dir: Path = DATA_DIR
    searxng_compose_dir: Path = SEARXNG_COMPOSE_DIR

    # Filtros de Busca
    filtro_tempo: str = "r604800"  # Última semana (LinkedIn)
    apenas_remoto: bool = True
    senioridade_filtro: str = "JUNIOR"
    threshold_minimo_match: int = 60

    # Concorrência e HTTP
    max_workers_jobs: int = 10
    max_concurrency_proxies: int = 200
    http_timeout: int = 8
    http_max_retries: int = 8
    searxng_url: str = "http://localhost:8080/search"
    searxng_timeout: int = 15
    searxng_max_espera: int = 30

    # Arquivos de Saída
    output_raw_json: Path = Field(default_factory=lambda: DATA_DIR / "vagas_linkedin.json")
    output_processed_json: Path = Field(default_factory=lambda: DATA_DIR / "vagas_processadas.json")
    output_markdown_report: Path = Field(default_factory=lambda: DATA_DIR / "relatorio_matches.md")

settings = Settings()
