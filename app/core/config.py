from pathlib import Path

from pydantic import BaseModel, Field

from app.models.enums import TimeFilterEnum

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
class Settings(BaseModel):
    # Diretórios
    project_root: Path = PROJECT_ROOT
    app_dir: Path = APP_DIR
    data_dir: Path = DATA_DIR

    # Filtros de Busca
    filtro_tempo: TimeFilterEnum = TimeFilterEnum.ULTIMAS_24H
    apenas_remoto: bool = True
    senioridade_filtro: str = "JUNIOR"
    threshold_minimo_match: int = 60

    # Flags de Comportamento e Otimização
    usar_proxy: bool = True
    enriquecer_detalhes: bool = True

    # Concorrência e HTTP
    max_workers_jobs: int = 10
    max_concurrency_proxies: int = 200
    http_timeout: int = 20
    http_max_retries: int = 5

    # Arquivos de Saída
    output_raw_json: Path = Field(default_factory=lambda: DATA_DIR / "vagas_linkedin.json")
    output_processed_json: Path = Field(default_factory=lambda: DATA_DIR / "vagas_processadas.json")
    output_markdown_report: Path = Field(default_factory=lambda: DATA_DIR / "relatorio_matches.md")


settings = Settings()
