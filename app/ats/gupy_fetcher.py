import time
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup

from app.core.logging import logger
from app.models.enums import ItemTypeEnum, PlatformEnum, ScopeEnum, TimeFilterEnum, WorkModelEnum
from app.models.job import JobItem

GUPY_SEARCH_URL = "https://portal.gupy.io/api/job-search/jobs"
HEADERS_PADRAO = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "application/json",
}


def _limpar_html_descricao(texto_html: str | None) -> str:
    if not texto_html:
        return ""
    sopa = BeautifulSoup(texto_html, "html.parser")
    return sopa.get_text(separator=" ", strip=True)


def _verificar_recencia(
    data_iso: str | None,
    filtro_tempo: TimeFilterEnum,
) -> bool:
    dias_limite = filtro_tempo.dias_maximos
    if dias_limite is None or not data_iso:
        return True

    try:
        data_limpa = data_iso.replace("Z", "+00:00")
        data_publicacao = datetime.fromisoformat(data_limpa)
        agora = datetime.now(UTC)
        dias_diferenca = (agora - data_publicacao).total_seconds() / 86400.0
    except Exception:
        return True
    else:
        return dias_diferenca <= dias_limite


def _formatar_data_postagem(data_iso: str | None) -> str:
    if not data_iso:
        return "Recente"
    try:
        data_limpa = data_iso.replace("Z", "+00:00")
        data_obj = datetime.fromisoformat(data_limpa)
        return data_obj.strftime("%d/%m/%Y")
    except Exception:
        return data_iso[:10] if len(data_iso) >= 10 else "Recente"


def _determinar_modelo_trabalho(modalidade_str: str) -> WorkModelEnum:
    texto = modalidade_str.lower()
    if "remote" in texto:
        return WorkModelEnum.REMOTO
    if "hybrid" in texto:
        return WorkModelEnum.HIBRIDO
    return WorkModelEnum.PRESENCIAL


def _converter_item_gupy(
    item: dict,
    filtro_tempo: TimeFilterEnum,
    apenas_remoto: bool,
) -> JobItem | None:
    data_publicacao_iso = item.get("publishedDate")
    if not _verificar_recencia(data_publicacao_iso, filtro_tempo):
        return None

    titulo = (item.get("name") or "").strip()
    if not titulo:
        return None

    empresa = (item.get("careerPageName") or "N/A").strip()
    cidade = item.get("city") or ""
    estado = item.get("state") or ""
    localizacao = f"{cidade}/{estado}" if (cidade and estado) else (cidade or estado or "Brasil")

    modelo_trabalho = _determinar_modelo_trabalho(item.get("workplaceType") or "")
    if apenas_remoto and modelo_trabalho != WorkModelEnum.REMOTO:
        return None

    link_vaga = item.get("jobUrl") or item.get("careerPageUrl") or ""
    descricao_bruta = item.get("description") or ""
    descricao_limpa = _limpar_html_descricao(descricao_bruta)
    job_id = str(item.get("id") or "")

    return JobItem(
        job_id=f"gupy_{job_id}",
        tipo=ItemTypeEnum.JOB,
        plataforma=PlatformEnum.GUPY,
        escopo=ScopeEnum.NACIONAL,
        titulo=titulo,
        empresa=empresa,
        localizacao=localizacao,
        data_postagem=_formatar_data_postagem(data_publicacao_iso),
        modelo_trabalho=modelo_trabalho,
        link=link_vaga,
        descricao_resumida=descricao_limpa[:300],
        descricao_completa=descricao_limpa,
    )


def buscar_vagas_gupy_por_query(
    termo_busca: str,
    filtro_tempo: TimeFilterEnum,
    apenas_remoto: bool,
    max_paginas: int,
    timeout: int,
) -> list[JobItem]:
    vagas_coletadas: list[JobItem] = []
    tamanho_pagina = 100

    for numero_pagina in range(max_paginas):
        offset = numero_pagina * tamanho_pagina
        parametros: dict[str, str | int] = {
            "jobName": termo_busca,
            "limit": tamanho_pagina,
            "offset": offset,
        }
        if apenas_remoto:
            parametros["workplaceType"] = "remote"

        try:
            resposta = requests.get(
                GUPY_SEARCH_URL,
                params=parametros,
                headers=HEADERS_PADRAO,
                timeout=timeout,
            )
            if resposta.status_code != 200:
                logger.warning(f"⚠️ [GUPY] Falha ao consultar '{termo_busca}' (página {numero_pagina}): Status {resposta.status_code}")
                break

            dados = resposta.json()
            itens_vagas = dados.get("data", [])
            if not itens_vagas:
                break

            for item in itens_vagas:
                vaga_convertida = _converter_item_gupy(
                    item=item,
                    filtro_tempo=filtro_tempo,
                    apenas_remoto=apenas_remoto,
                )
                if vaga_convertida:
                    vagas_coletadas.append(vaga_convertida)

            if len(itens_vagas) < tamanho_pagina:
                break

            time.sleep(0.15)
        except Exception as erro:
            logger.error(f"❌ [GUPY] Erro ao buscar vagas para '{termo_busca}' (offset={offset}): {erro}")
            break

    return vagas_coletadas
