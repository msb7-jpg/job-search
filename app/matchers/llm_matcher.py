import contextlib
import json
import re
from pathlib import Path

import requests
from tqdm import tqdm

from app.core.config import Settings
from app.core.logging import logger
from app.models.job import JobItem
from app.models.match import LlmEvaluation

CURRICULO_FALLBACK = """
Candidato: Miguel Batista (Recife, PE, Brasil)
Experiência Profissional: ~2 anos de experiência (Nível Júnior / Entry-Level).
- Desenvolvedor Full-Stack no Projeto CIn Motorola (Abr 2025 - Presente): Python, Django, Vue 2/3 Composition API, TypeScript, GCP, Vertex AI Gemini, Docker, Pytest, Jenkins, GitLab CI.
- Desenvolvedor de Soluções na Masterboi (Jul 2024 - Abr 2025): Python, Django, Pandas, SQL, REST APIs, Docker, Linux, GitHub Actions, Selenium.
- Formação: Ciência da Computação na CESAR School (2023 - 2027) e Monitor Acadêmico (C, SQL, PostgreSQL, Python, Django).
Stack Principal: Python, FastAPI, Django, Flask, Vue.js (Vue 2/3), React.js (React 19), TypeScript, JavaScript, PostgreSQL, MySQL, Redis, RabbitMQ, Celery, LangChain, LangGraph, Vertex AI, PySpark, Databricks, Docker, Linux, AWS, GCP.
Idiomas: Português nativo, Inglês fluente (B2).
Disponibilidade: Busca vagas de nível Júnior (até 2 anos de experiência exigidos), 100% Remotas (Brasil ou Internacional LATAM/Global acessível do Brasil) ou em Recife-PE.
""".strip()


def carregar_texto_curriculo(caminho_curriculo: Path) -> str:
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
        "   - O candidato busca EXCLUSIVAMENTE vagas de engenharia de software real (backend e/ou full-stack em produto).\n\n"
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
        f"- Plataforma: {vaga.plataforma}\n"
        f"- Escopo: {vaga.escopo}\n"
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
                )
    except Exception as erro:
        logger.warning(f"⚠️ [LLM-JUDGE] Erro ao avaliar vaga '{vaga.titulo}': {erro}")

    return LlmEvaluation(
        aprovado=True,
        score_llm=70,
        nivel_detectado=vaga.senioridade.value,
        anos_experiencia_exigidos=None,
        remoto_viavel_brasil=True,
        justificativa="Aprovada pelo filtro heurístico (fallback de resposta do LLM).",
    )


def filtrar_vagas_com_llm_em_lote(
    vagas: list[JobItem],
    settings: Settings,
    rotulo_lote: str,
) -> tuple[list[JobItem], list[JobItem]]:
    if not vagas or not settings.usar_filtro_llm:
        return vagas, []

    ativo, modelo_detectado = verificar_servidor_llm_ativo(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=3,
    )

    if not ativo:
        logger.warning(
            f"⚠️ [LLM-JUDGE] Servidor LLM inativo em {settings.llm_base_url}. Mantendo filtro heurístico para lote '{rotulo_lote}'."
        )
        return vagas, []

    model_name = settings.llm_model_name or modelo_detectado or "gemini-3.8-flash"
    texto_curriculo = carregar_texto_curriculo(settings.caminho_curriculo_md)
    vagas_aprovadas_llm: list[JobItem] = []
    vagas_rejeitadas_llm: list[JobItem] = []

    logger.info(
        f"🧠 [LLM-JUDGE] Avaliando {len(vagas)} vagas de '{rotulo_lote}' via {settings.llm_base_url} ({model_name}) "
        f"contra seu currículo (Máx {settings.max_anos_experiencia} anos XP | 100% Remoto BR)..."
    )

    with tqdm(
        total=len(vagas),
        desc=f"🧠 [LLM] Julgando {rotulo_lote}",
        unit="vaga",
    ) as barra_llm:
        for vaga in vagas:
            avaliacao = avaliar_vaga_com_llm(
                vaga=vaga,
                texto_curriculo=texto_curriculo,
                base_url=settings.llm_base_url,
                model_name=model_name,
                api_key=settings.llm_api_key,
                max_anos_experiencia=settings.max_anos_experiencia,
                timeout=settings.llm_timeout,
            )
            if vaga.match_curriculo:
                vaga.match_curriculo.avaliacao_llm = avaliacao

            if avaliacao.aprovado:
                vagas_aprovadas_llm.append(vaga)
                logger.info(f"✅ [LLM-APPROVE] [{vaga.plataforma}] {vaga.titulo} ({vaga.empresa}) -> {avaliacao.justificativa}")
            else:
                vaga.camada_descarte = "LLM Judge Semântico (IA)"
                vaga.motivo_descarte = avaliacao.justificativa
                vagas_rejeitadas_llm.append(vaga)
                logger.info(
                    f"❌ [LLM-REJECT] [{vaga.plataforma}] {vaga.titulo} ({vaga.empresa}) "
                    f"[Nível: {avaliacao.nivel_detectado}] -> {avaliacao.justificativa}"
                )

            barra_llm.set_postfix(
                aprovadas=len(vagas_aprovadas_llm),
                rejeitadas=len(vagas_rejeitadas_llm),
            )
            barra_llm.update(1)

    logger.info(
        f"🧠 [LLM-JUDGE] Resultado '{rotulo_lote}': {len(vagas_aprovadas_llm)} vagas 100% fiéis aprovadas | "
        f"{len(vagas_rejeitadas_llm)} vagas descartadas pelo LLM."
    )
    return vagas_aprovadas_llm, vagas_rejeitadas_llm


def executar_teste_llm() -> None:
    """Função standalone para testar conexão e avaliação com o endpoint configurado."""
    cfg = Settings()
    print("=" * 80)
    print("🧠 TESTE DE CONEXÃO E AVALIAÇÃO COM LLM JUDGE (OPENAI-COMPATIBLE)")
    print(f"🔗 Endpoint Base URL: {cfg.llm_base_url}")
    print(f"🤖 Modelo Configurado: {cfg.llm_model_name}")
    print("=" * 80)

    ativo, modelo_detectado = verificar_servidor_llm_ativo(cfg.llm_base_url, cfg.llm_api_key, timeout=4)
    if not ativo:
        print(f"❌ Erro: O servidor em {cfg.llm_base_url} não respondeu ao endpoint /models.")
        return

    print(f"✅ Conexão bem-sucedida! Servidor ativo (Modelo detectado: {modelo_detectado}).")

    # Vaga de teste realista
    vaga_teste = JobItem(
        job_id="test_001",
        titulo="Desenvolvedor Python Júnior (Remoto)",
        empresa="Tech Innovations Brasil",
        localizacao="Remoto - Brasil",
        link="https://linkedin.com/jobs/view/test-001",
        descricao_completa=(
            "Buscamos desenvolvedor Python Júnior com até 2 anos de experiência para atuar com Django, "
            "FastAPI e PostgreSQL em regime 100% remoto para todo o Brasil. Desejável conhecimento em Vue.js ou React."
        ),
    )

    curriculo = carregar_texto_curriculo(cfg.caminho_curriculo_md)
    print("\n🔍 Avaliando vaga de teste:")
    print(f"   Título: {vaga_teste.titulo}")
    print(f"   Empresa: {vaga_teste.empresa}")
    print(f"   Descrição: {vaga_teste.descricao_completa}")
    print("\n⏳ Enviando requisição para o LLM Judge...")

    inicio = __import__("time").perf_counter()
    resultado = avaliar_vaga_com_llm(
        vaga=vaga_teste,
        texto_curriculo=curriculo,
        base_url=cfg.llm_base_url,
        model_name=cfg.llm_model_name,
        api_key=cfg.llm_api_key,
        max_anos_experiencia=cfg.max_anos_experiencia,
        timeout=cfg.llm_timeout,
    )
    tempo_total = __import__("time").perf_counter() - inicio

    print("=" * 80)
    print("📊 RESULTADO DA AVALIAÇÃO:")
    print(f"   Aprovado: {'✅ SIM' if resultado.aprovado else '❌ NÃO'}")
    print(f"   Score LLM: {resultado.score_llm}/100")
    print(f"   Nível Detectado: {resultado.nivel_detectado}")
    print(f"   Anos de Experiência Exigidos: {resultado.anos_experiencia_exigidos}")
    print(f"   Remoto Viável no Brasil: {'Sim' if resultado.remoto_viavel_brasil else 'Não'}")
    print(f"   Justificativa: {resultado.justificativa}")
    print(f"   Tempo de Resposta: {tempo_total:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    executar_teste_llm()
