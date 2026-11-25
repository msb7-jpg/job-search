import contextlib
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from tqdm import tqdm

from app.core.config import Settings
from app.core.logging import logger
from app.models.job import JobItem
from app.models.match import LlmEvaluation
from app.tailor.models import DEFAULT_MASTER_PROFILE_PATH, load_master_profile

CURRICULO_FALLBACK = "Software Engineer candidate profile not yet configured."


def carregar_texto_curriculo(caminho_curriculo: Path) -> str:
    master_profile_path = caminho_curriculo.parent / "master_profile.json"
    if not master_profile_path.exists():
        master_profile_path = DEFAULT_MASTER_PROFILE_PATH

    if master_profile_path.exists():
        try:
            profile_text = load_master_profile(master_profile_path).to_llm_summary_text().strip()
            if profile_text:
                return profile_text
        except Exception as erro:
            logger.warning(f"⚠️ [LLM-JUDGE] Falha ao ler master_profile.json: {erro}")

    if caminho_curriculo.exists():
        try:
            texto = caminho_curriculo.read_text(encoding="utf-8").strip()
            if texto:
                return texto[:3500]
        except Exception as erro:
            logger.warning(f"⚠️ [LLM-JUDGE] Não foi possível ler '{caminho_curriculo}': {erro}")
    return CURRICULO_FALLBACK


def _montar_headers_llm(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "not-needed":
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def verificar_servidor_llm_ativo(base_url: str, api_key: str = "not-needed", timeout: int = 3) -> tuple[bool, str | None]:
    """Verifica se o servidor OpenAI-Compatible responde ao endpoint /v1/models e lista o primeiro modelo."""
    url_modelos = f"{base_url.rstrip('/')}/models"
    headers = _montar_headers_llm(api_key)
    with contextlib.suppress(Exception):
        resposta = requests.get(url_modelos, headers=headers, timeout=timeout)
        if resposta.status_code == 200:
            dados = resposta.json()
            lista_modelos = dados.get("data", [])
            if isinstance(lista_modelos, list) and lista_modelos:
                primeiro_id = lista_modelos[0].get("id")
                return True, str(primeiro_id) if primeiro_id else None
            return True, None
    return False, None


def _extrair_json_resposta(texto_bruto: str) -> dict:
    # Remover blocos de pensamento <think>...</think> caso modelos de reasoning os emitam
    texto_limpo = re.sub(r"<think>.*?</think>", "", texto_bruto, flags=re.DOTALL).strip()
    # Remover cercas markdown ```json ... ```
    texto_limpo = re.sub(r"^```(?:json)?\s*", "", texto_limpo)
    texto_limpo = re.sub(r"\s*```$", "", texto_limpo).strip()

    try:
        return json.loads(texto_limpo)
    except Exception:
        correspondencia = re.search(r"\{.*\}", texto_limpo, flags=re.DOTALL)
        if correspondencia:
            try:
                return json.loads(correspondencia.group(0))
            except Exception:
                pass
    return {}


def avaliar_vaga_com_llm(
    vaga: JobItem,
    texto_curriculo: str,
    base_url: str,
    model_name: str,
    api_key: str,
    max_anos_experiencia: int,
    timeout: int,
) -> LlmEvaluation:
    descricao_vaga = (vaga.descricao_completa or vaga.descricao_resumida or "").strip()
    descricao_truncada = descricao_vaga[:3200] if descricao_vaga else "Sem descrição detalhada disponível."

    prompt_sistema = (
        "Você é um avaliador técnico rigoroso de vagas de engenharia de software.\n"
        "Sua função é proteger o tempo do candidato, aprovando SOMENTE vagas que sejam 100% fiéis ao nível de experiência, "
        "localização/modalidade e stack técnica dele.\n\n"
        f"=== CURRÍCULO DO CANDIDATO ===\n{texto_curriculo}\n\n"
        "=== REGRAS OBRIGATÓRIAS DE APROVAÇÃO (aprovado = true SOMENTE se cumprir TODAS as 4 regras) ===\n"
        f"1. EXPERIÊNCIA E SENIORIDADE (ATÉ {max_anos_experiencia} ANOS EXIGIDOS):\n"
        f"   - APROVE (aprovado = true, nivel_detectado = 'Júnior') se a vaga for Júnior, Entry-Level, Estágio, Trainee, "
        f"se pedir até {max_anos_experiencia} anos de experiência (ex: '1 ano', '2 anos', 'mínimo de 2 anos', '2+ years' onde o mínimo é 2), "
        "ou se NÃO especificar anos mínimos de experiência nem tiver 'Pleno'/'Sênior' no título.\n"
        f"   - REJEITE (aprovado = false) se a vaga exigir explicitamente {max_anos_experiencia + 1}+ anos de experiência (3+ anos, 4+ anos, 5+ anos), "
        "se tiver Pleno, Mid-Level, Sênior, Tech Lead, Staff no título/descrição, ou se exigir 'mentorar juniores' / 'subject matter expert'.\n"
        "2. MODALIDADE 100% REMOTA ACESSÍVEL DO BRASIL (OU PRESENCIAL EM RECIFE-PE):\n"
        "   - O candidato reside em Recife, PE, Brasil.\n"
        "   - A vaga deve ser 100% Remota viável a partir do Brasil (Remoto Nacional ou Remoto Internacional LATAM/Global) ou localizada em Recife/PE.\n"
        "   - REJEITE (aprovado = false) se a vaga for presencial/híbrida em outra cidade/estado (ex: São Paulo, Ijuí/RS, Serra/ES, Belo Horizonte) "
        "ou se for restrita a moradores de outros países (ex: Vietnã, Índia, Filipinas, Polônia, Alemanha, França, EUA Only, Security Clearance).\n"
        "3. STACK TÉCNICA COMPATÍVEL:\n"
        "   - A vaga deve envolver desenvolvimento de software compatível com Python (Django, FastAPI, Flask, IA/LLMs/LangChain, Dados) "
        "e/ou Full-Stack (Vue.js, React.js, TypeScript, JavaScript, Node.js).\n"
        "   - REJEITE (aprovado = false) se o foco principal obrigatório da vaga for outra tecnologia incompatível (ex: Go avançado, PHP, .NET/C#, Java exclusivo, Angular exclusivo sem Python, ou vaga não-técnica de Produto/PM/SEO).\n"
        "4. PROIBIDO TREINAMENTO/AVALIAÇÃO DE MODELOS DE IA E EMPRESAS FACTORY (ex: Micro1, Outlier, DataAnnotation, Invisible):\n"
        "   - REJEITE (aprovado = false) se a vaga for para treinar IA, avaliar prompts, RLHF, anotação de dados, human data platform, ou se a empresa for Micro1 (ou similar).\n"
        "   - O candidato busca EXCLUSIVAMENTE vagas de engenharia de software real em produto.\n\n"
        "Responda APENAS com um objeto JSON válido neste formato exato:\n"
        "{\n"
        '  "aprovado": true ou false,\n'
        '  "score_llm": 0 a 100,\n'
        '  "nivel_detectado": "Júnior", "Pleno", "Sênior", "Liderança" ou "Estágio",\n'
        '  "anos_experiencia_exigidos": numero inteiro ou null,\n'
        '  "remoto_viavel_brasil": true ou false,\n'
        '  "justificativa": "Frase curta e direta em português explicando a aprovação ou o motivo exato da rejeição"\n'
        "}"
    )

    prompt_usuario = (
        f"Avalie a vaga abaixo:\n"
        f"- Provedor: {vaga.provider}\n"
        f"- Título da Vaga: {vaga.titulo}\n"
        f"- Empresa: {vaga.empresa}\n"
        f"- Localização Informada: {vaga.localizacao}\n"
        f"- Modelo Classificado Inicialmente: {vaga.modelo_trabalho}\n"
        f"- Descrição da Vaga:\n{descricao_truncada}"
    )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ],
        "temperature": 0.1,
        "max_tokens": 800,
        "chat_template_kwargs": {"enable_thinking": False},
        "response_format": {"type": "json_object"},
    }

    url_chat = f"{base_url.rstrip('/')}/chat/completions"
    headers = _montar_headers_llm(api_key)

    try:
        resposta = requests.post(url_chat, headers=headers, json=payload, timeout=timeout)
        if resposta.status_code == 200:
            dados_resp = resposta.json()
            conteudo = dados_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            json_extraido = _extrair_json_resposta(conteudo)
            if json_extraido:
                aprovado_bool = bool(json_extraido.get("aprovado", False))
                remoto_bool = bool(json_extraido.get("remoto_viavel_brasil", True))
                anos_exigidos = json_extraido.get("anos_experiencia_exigidos")
                anos_int = int(anos_exigidos) if isinstance(anos_exigidos, int | float) else None

                # Trava de segurança determinística sobre o output do LLM
                if not remoto_bool:
                    aprovado_bool = False
                if anos_int is not None and anos_int > max_anos_experiencia:
                    aprovado_bool = False

                nivel_str = str(json_extraido.get("nivel_detectado") or "Não Identificado")
                if any(termo in nivel_str.lower() for termo in ["pleno", "sênior", "senior", "lider", "líder"]):
                    aprovado_bool = False

                empresa_nome = (vaga.empresa or "").lower()
                if "micro1" in empresa_nome or "micro 1" in empresa_nome:
                    aprovado_bool = False
                    json_extraido["justificativa"] = "Empresa Micro1 descartada por política do candidato (modelo de AI training)."

                score_val = int(json_extraido.get("score_llm", 75 if aprovado_bool else 25))
                score_val = max(0, min(100, score_val))

                return LlmEvaluation(
                    aprovado=aprovado_bool,
                    score_llm=score_val,
                    nivel_detectado=nivel_str,
                    anos_experiencia_exigidos=anos_int,
                    remoto_viavel_brasil=remoto_bool,
                    justificativa=str(json_extraido.get("justificativa") or ""),
                    status="APPROVED" if aprovado_bool else "REJECTED",
                )
    except Exception as erro:
        logger.warning(f"⚠️ [LLM-JUDGE] Erro ao avaliar vaga '{vaga.titulo}': {erro}")

    return LlmEvaluation(
        aprovado=False,
        score_llm=0,
        nivel_detectado=vaga.senioridade.value,
        anos_experiencia_exigidos=None,
        remoto_viavel_brasil=True,
        justificativa="Avaliação pendente (servidor LLM indisponível ou resposta inválida).",
        status="PENDING",
    )


def filtrar_vagas_com_llm_em_lote(
    vagas: list[JobItem],
    settings: Settings,
    rotulo_lote: str,
) -> tuple[list[JobItem], list[JobItem], list[JobItem]]:
    """Avalia vagas em paralelo via LLM Judge. Retorna (aprovadas, rejeitadas, pendentes)."""
    if not vagas or not settings.usar_filtro_llm:
        return vagas, [], []

    ativo, modelo_detectado = verificar_servidor_llm_ativo(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=3,
    )

    if not ativo:
        logger.warning(
            f"⚠️ [LLM-JUDGE] Servidor LLM inativo em {settings.llm_base_url}. "
            f"Marcando {len(vagas)} vagas de '{rotulo_lote}' como PENDING para reavaliação futura."
        )
        for vaga in vagas:
            if vaga.match_curriculo:
                vaga.match_curriculo.avaliacao_llm = LlmEvaluation(
                    aprovado=False,
                    score_llm=0,
                    nivel_detectado=vaga.senioridade.value,
                    justificativa="Servidor LLM inativo durante a execução.",
                    status="PENDING",
                )
        return [], [], list(vagas)

    model_name = settings.llm_model_name or modelo_detectado or "gemini-3.8-flash"
    texto_curriculo = carregar_texto_curriculo(settings.caminho_curriculo_md)
    vagas_aprovadas_llm: list[JobItem] = []
    vagas_rejeitadas_llm: list[JobItem] = []
    vagas_pendentes_llm: list[JobItem] = []
    workers = max(1, min(settings.llm_max_workers, len(vagas)))

    logger.info(
        f"🧠 [LLM-JUDGE] Avaliando {len(vagas)} vagas de '{rotulo_lote}' (workers={workers}) via {settings.llm_base_url} ({model_name})..."
    )

    with (
        ThreadPoolExecutor(max_workers=workers) as executor,
        tqdm(total=len(vagas), desc=f"🧠 [LLM] Julgando {rotulo_lote}", unit="vaga") as barra_llm,
    ):
        futuros = {
            executor.submit(
                avaliar_vaga_com_llm,
                vaga=vaga,
                texto_curriculo=texto_curriculo,
                base_url=settings.llm_base_url,
                model_name=model_name,
                api_key=settings.llm_api_key,
                max_anos_experiencia=settings.max_anos_experiencia,
                timeout=settings.llm_timeout,
            ): vaga
            for vaga in vagas
        }
        for futuro in as_completed(futuros):
            vaga = futuros[futuro]
            avaliacao = futuro.result()
            if vaga.match_curriculo:
                vaga.match_curriculo.avaliacao_llm = avaliacao

            if avaliacao.status == "PENDING":
                vagas_pendentes_llm.append(vaga)
                logger.warning(f"⏳ [LLM-PENDING] [{vaga.provider}] {vaga.titulo} ({vaga.empresa}) -> {avaliacao.justificativa}")
            elif avaliacao.aprovado:
                vagas_aprovadas_llm.append(vaga)
                logger.info(f"✅ [LLM-APPROVE] [{vaga.provider}] {vaga.titulo} ({vaga.empresa}) -> {avaliacao.justificativa}")
            else:
                vaga.camada_descarte = "LLM Judge Semântico (IA)"
                vaga.motivo_descarte = avaliacao.justificativa
                vagas_rejeitadas_llm.append(vaga)
                logger.info(
                    f"❌ [LLM-REJECT] [{vaga.provider}] {vaga.titulo} ({vaga.empresa}) "
                    f"[Nível: {avaliacao.nivel_detectado}] -> {avaliacao.justificativa}"
                )

            barra_llm.set_postfix(
                aprovadas=len(vagas_aprovadas_llm),
                rejeitadas=len(vagas_rejeitadas_llm),
                pendentes=len(vagas_pendentes_llm),
            )
            barra_llm.update(1)

    logger.info(
        f"🧠 [LLM-JUDGE] Resultado '{rotulo_lote}': {len(vagas_aprovadas_llm)} aprovadas | "
        f"{len(vagas_rejeitadas_llm)} rejeitadas | {len(vagas_pendentes_llm)} pendentes."
    )
    return vagas_aprovadas_llm, vagas_rejeitadas_llm, vagas_pendentes_llm
