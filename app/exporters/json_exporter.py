import json
from pathlib import Path

from app.core.logging import logger
from app.models.report import ProcessedDataOutput


def salvar_dados_brutos_json(dados: dict, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    logger.info(f"💾 Dados brutos persistidos com sucesso em '{caminho}'.")

def salvar_dados_processados_json(output: ProcessedDataOutput, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(output.model_dump_json(indent=4))
    logger.info(f"💾 Dados consolidados estruturados persistidos com sucesso em '{caminho}'.")
