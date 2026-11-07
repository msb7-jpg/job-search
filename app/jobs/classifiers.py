import re

from app.models.enums import SeniorityEnum, WorkModelEnum

PADRAO_SENIORIDADE_BLOQUEADA_TITULO = re.compile(
    r"\b(?:"
    r"senior|sênior|sr|ssr|pleno|pl|staff|lead|tech\s+lead|"
    r"líder|lider|liderança|lideranca|principal|architect|arquiteto|arqueto|"
    r"especialista|middle|mid-level|mid/senior|founding|iii|ii|"
    r"engineer\s+2|developer\s+2|desenvolvedor\s+2"
    r")\b",
    re.IGNORECASE,
)

BLOQUEADOS_RESTRICAO_VAGA = [
    "c2c",
    "us based",
    "us only",
    "no visa",
    "citizens only",
    "security clearance",
    "top secret",
    "polygraph",
    "sci access",
    "(m/w/d)",
    "(f/m/d)",
    "(m/ž)",
    "(h/f)",
]

BLOQUEADOS_LOCALIZACAO_INCOMPATIVEL = [
    "vietnã",
    "vietnam",
    "hanói",
    "hanoi",
    "ho chi minh",
    "índia",
    "india",
    "bangalore",
    "bengaluru",
    "pune",
    "hyderabad",
    "chennai",
    "madras",
    "mumbai",
    "delhi",
    "noida",
    "gurugram",
    "itanagar",
    "carnataca",
    "maharashtra",
    "telanganá",
    "tamil nadu",
    "filipinas",
    "philippines",
    "manila",
    "makati",
    "cebu",
    "nigéria",
    "nigeria",
    "paquistão",
    "pakistan",
    "bangladesh",
    "cazaquistão",
    "kazakhstan",
    "almaty",
    "sérvia",
    "serbia",
    "novi sad",
    "polônia",
    "poland",
    "varsóvia",
    "poznan",
    "croácia",
    "croatia",
    "zagreb",
    "zagrebe",
    "alemanha",
    "germany",
    "munique",
    "bona",
    "suíça",
    "lugano",
    "frança",
    "paris",
    "ilha de frança",
    "altos do sena",
    "reino unido",
    "inglaterra",
    "birmingham",
    "espanha",
    "madri",
    "barcelona",
    "cuenca",
]

BLOQUEADOS_PRESENCIAL = [
    "presencial",
    "100% presencial",
    "onsite",
    "on-site",
    "híbrido",
    "hibrido",
    "hybrid",
    "local only",
    "must be located",
]

EMPRESAS_BLOQUEADAS = [
    "micro1",
    "micro 1",
    "invisible technologies",
    "invisible tech",
    "dataannotation",
    "data annotation",
    "alignerr",
    "outlier",
    "mindrift",
    "turing",
]

BLOQUEADOS_TREINAMENTO_IA = [
    "ai trainer",
    "train ai",
    "ai training",
    "trainer",
    "training ai",
    "model training",
    "rlhf",
    "data annotat",
    "data annotation",
    "prompt engineer",
    "prompt evaluation",
    "evaluate ai",
    "evaluating ai",
    "ai tutor",
    "ai model evaluation",
    "annotation",
    "ai data annotator",
    "human data platforms",
]

PADRAO_ANOS_EXPERIENCIA_ALTA = re.compile(
    r"(?:\b([3-9]|1[0-9])\s*\+?\s*(?:anos|years)\s+(?:de\s+)?(?:experiência|experience))"
    r"|(?:\b(?:experiência|experience)\s*(?:mínima|minima|of|:\s*)?\s*([3-9]|1[0-9])\s*\+?\s*(?:anos|years))",
    re.IGNORECASE,
)


def _verificar_empresa_ou_ia_bloqueada(titulo_minusculo: str, empresa_minusculo: str, descricao_minusculo: str) -> str | None:
    for emp_bloqueada in EMPRESAS_BLOQUEADAS:
        if emp_bloqueada in empresa_minusculo or emp_bloqueada in titulo_minusculo:
            return f"Empresa bloqueada por política do usuário: '{emp_bloqueada.title()}'"

    for termo_ia in BLOQUEADOS_TREINAMENTO_IA:
        if termo_ia in titulo_minusculo:
            return f"Vaga de treinamento/avaliação de modelos de IA no título: '{termo_ia}'"
        if descricao_minusculo and (
            termo_ia in descricao_minusculo
            and any(p in descricao_minusculo for p in ["rlhf", "trainer", "training ai", "human data platform", "prompt eval"])
        ):
            return f"Vaga de treinamento/anotação de modelos de IA detectada na descrição: '{termo_ia}'"
    return None


def _verificar_localizacao_ou_restricao(texto_basico: str) -> str | None:
    for local_incompativel in BLOQUEADOS_LOCALIZACAO_INCOMPATIVEL:
        if local_incompativel in texto_basico:
            return f"Localização incompatível detectada no título/local: '{local_incompativel.title()}'"

    for restricao in BLOQUEADOS_RESTRICAO_VAGA:
        if restricao in texto_basico:
            return f"Restrição de contratação/vaga incompatível detectada: '{restricao}'"
    return None


def _verificar_senioridade_ou_modalidade(
    titulo_minusculo: str, texto_basico: str, senioridade_filtro: str, apenas_remoto: bool
) -> str | None:
    if senioridade_filtro == "JUNIOR":
        match_sen = PADRAO_SENIORIDADE_BLOQUEADA_TITULO.search(titulo_minusculo)
        if match_sen:
            return f"Senioridade incompatível detectada no título: '{match_sen.group(0).title()}'"

    if apenas_remoto:
        for palavra_bloqueada in BLOQUEADOS_PRESENCIAL:
            if palavra_bloqueada in texto_basico:
                return f"Modelo presencial/híbrido detectado no título/local: '{palavra_bloqueada.title()}'"
    return None


def avaliar_pre_filtro_job_bruto(
    titulo: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
    empresa: str = "",
    descricao: str = "",
) -> tuple[bool, str | None]:
    titulo_minusculo = (titulo or "").lower()
    localizacao_minusculo = (localizacao or "").lower()
    empresa_minusculo = (empresa or "").lower()
    descricao_minusculo = (descricao or "").lower()
    texto_basico = f"{titulo_minusculo} {localizacao_minusculo} {empresa_minusculo}"

    motivo_empresa_ia = _verificar_empresa_ou_ia_bloqueada(titulo_minusculo, empresa_minusculo, descricao_minusculo)
    if motivo_empresa_ia:
        return False, motivo_empresa_ia

    motivo_local = _verificar_localizacao_ou_restricao(texto_basico)
    if motivo_local:
        return False, motivo_local

    motivo_sen_mod = _verificar_senioridade_ou_modalidade(titulo_minusculo, texto_basico, senioridade_filtro, apenas_remoto)
    if motivo_sen_mod:
        return False, motivo_sen_mod

    return True, None


def pre_filtrar_job_bruto(
    titulo: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
    empresa: str = "",
    descricao: str = "",
) -> bool:
    aprovado, _motivo = avaliar_pre_filtro_job_bruto(
        titulo=titulo,
        localizacao=localizacao,
        apenas_remoto=apenas_remoto,
        senioridade_filtro=senioridade_filtro,
        empresa=empresa,
        descricao=descricao,
    )
    return aprovado


def pre_filtrar_post_bruto(
    titulo: str,
    descricao: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> bool:
    texto = f"{titulo} {descricao} {localizacao}".lower()
    titulo_minusculo = titulo.lower()

    if any(local_incompativel in texto for local_incompativel in BLOQUEADOS_LOCALIZACAO_INCOMPATIVEL):
        return False

    if senioridade_filtro == "JUNIOR":
        if PADRAO_SENIORIDADE_BLOQUEADA_TITULO.search(titulo_minusculo):
            return False

        if any(termo in texto for termo in BLOQUEADOS_RESTRICAO_VAGA):
            return False

    if apenas_remoto:
        termos_presencial_estrito = [
            "100% presencial",
            "presencial apenas",
            "local only",
            "must be located in",
            "on-site only",
        ]
        if any(termo in texto for termo in termos_presencial_estrito):
            return False

    return True


def classificar_senioridade(titulo: str, descricao: str, padrao_junior: bool) -> SeniorityEnum:
    titulo_minusculo = titulo.lower()
    descricao_minusculo = descricao.lower()

    # Remover falsos positivos onde vaga Sênior/Pleno menciona mentoria a juniores
    descricao_sem_mentoria = re.sub(
        r"\b(?:mentor(?:ing|ar)?|orientar|apoiar|coach(?:ing)?)\s+(?:desenvolvedores\s+|engenheiros\s+)?(?:júnior|junior|juniores|jr)\b",
        "",
        descricao_minusculo,
    )

    if any(palavra_chave in titulo_minusculo for palavra_chave in ["estágio", "estagio", "intern", "trainee"]):
        return SeniorityEnum.ESTAGIO

    if PADRAO_SENIORIDADE_BLOQUEADA_TITULO.search(titulo_minusculo):
        if re.search(r"\b(?:pleno|pl|middle|mid-level|ii|engineer\s+2|developer\s+2|desenvolvedor\s+2)\b", titulo_minusculo):
            return SeniorityEnum.PLENO
        return SeniorityEnum.SENIOR

    if re.search(r"\b(?:júnior|junior|jr|entry\s+level|nivel\s+1|nível\s+1|desenvolvedor\s+1|associate)\b", titulo_minusculo):
        return SeniorityEnum.JUNIOR

    # Avaliar descrição: checar exigências de Pleno/Sênior ANTES de assumir Júnior
    correspondencia_anos = PADRAO_ANOS_EXPERIENCIA_ALTA.search(descricao_sem_mentoria)
    if correspondencia_anos:
        anos_str = correspondencia_anos.group(1) or correspondencia_anos.group(2)
        anos_int = int(anos_str) if anos_str and anos_str.isdigit() else 3
        return SeniorityEnum.SENIOR if anos_int >= 5 else SeniorityEnum.PLENO

    indicadores_senior_desc = [
        "full stack sênior",
        "fullstack sênior",
        "desenvolvedor(a) sênior",
        "desenvolvedor sênior",
        "engenheiro sênior",
        "nível sênior",
        "perfil sênior",
        "senior developer",
        "senior software engineer",
        "tech lead",
        "liderança técnica",
        "líder técnico",
        "top secret clearance",
        "polygraph",
    ]
    if any(palavra_chave in descricao_sem_mentoria for palavra_chave in indicadores_senior_desc):
        return SeniorityEnum.SENIOR

    indicadores_pleno_desc = [
        "desenvolvedor(a) pleno",
        "desenvolvedor pleno",
        "backend python - pleno",
        "nível pleno",
        "perfil pleno",
        "mid-level",
        "mid/senior",
    ]
    if any(palavra_chave in descricao_sem_mentoria for palavra_chave in indicadores_pleno_desc):
        return SeniorityEnum.PLENO

    if any(
        palavra_chave in descricao_sem_mentoria
        for palavra_chave in [
            "nível júnior",
            "nivel junior",
            "vaga júnior",
            "vaga junior",
            "perfil júnior",
            "entry-level",
            "entry level",
            "sem experiência prévia",
            "recém-formado",
        ]
    ):
        return SeniorityEnum.JUNIOR

    return SeniorityEnum.JUNIOR if padrao_junior else SeniorityEnum.NAO_ESPECIFICADO


def classificar_modelo_trabalho(titulo: str, localizacao: str, descricao: str, padrao_remoto: bool) -> WorkModelEnum:
    texto = f"{titulo} {localizacao} {descricao}".lower()

    if any(local_incompativel in f"{titulo} {localizacao}".lower() for local_incompativel in BLOQUEADOS_LOCALIZACAO_INCOMPATIVEL):
        return WorkModelEnum.PRESENCIAL

    termos_hibrido = [
        "híbrido",
        "hibrido",
        "hybrid",
        "híbrida",
        "hibrida",
        "modelo híbrido",
        "modelo hibrido",
        "trabalho híbrido",
        "trabalho hibrido",
        "híbrido em",
        "hibrido em",
        "presencial/remoto",
        "remoto/presencial",
    ]
    termos_presencial = [
        "presencial",
        "on-site",
        "onsite",
        "escritório",
        "escritorio",
        "100% presencial",
        "modelo presencial",
        "trabalho presencial",
        "vaga presencial",
        "atuação presencial",
        "atuacao presencial",
        "alocação presencial",
        "position may be performed in the following locations",
        "top secret clearance",
        "polygraph examination",
    ]

    if any(palavra_chave in texto for palavra_chave in termos_hibrido):
        return WorkModelEnum.HIBRIDO
    if any(palavra_chave in texto for palavra_chave in termos_presencial):
        return WorkModelEnum.PRESENCIAL

    termos_remoto = ["remoto", "remote", "home office", "home-office", "teletrabalho", "work from home", "100% remoto"]
    if any(palavra_chave in texto for palavra_chave in termos_remoto):
        return WorkModelEnum.REMOTO

    return WorkModelEnum.REMOTO if padrao_remoto else WorkModelEnum.NAO_ESPECIFICADO
