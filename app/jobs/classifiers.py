from app.models.enums import SeniorityEnum, WorkModelEnum

BLOQUEADOS_SENIORIDADE_JUNIOR = [
    "senior",
    "sênior",
    "sr",
    "sr.",
    "ssr",
    "pleno",
    "pl",
    "pl.",
    "staff",
    "lead",
    "tech lead",
    "principal",
    "architect",
    "arquiteto",
    "arqueto",
    "especialista",
    "iii",
    "c2c",
    "us based",
    "us only",
    "no visa",
    "citizens only",
    "security clearance",
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


def pre_filtrar_job_bruto(
    titulo: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> bool:
    t_lower = titulo.lower()
    loc_lower = localizacao.lower()
    texto_basico = f"{t_lower} {loc_lower}"

    if senioridade_filtro == "JUNIOR" and any(p in t_lower for p in BLOQUEADOS_SENIORIDADE_JUNIOR):
        return False

    return not (apenas_remoto and any(p in texto_basico for p in BLOQUEADOS_PRESENCIAL))


def pre_filtrar_post_bruto(
    titulo: str,
    descricao: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> bool:
    texto = f"{titulo} {descricao} {localizacao}".lower()
    t_lower = titulo.lower()

    if senioridade_filtro == "JUNIOR":
        if any(p in t_lower for p in ["senior", "sênior", "sr", "sr.", "ssr", "pleno", "pl", "lead", "principal", "architect", "staff"]):
            return False

        termos_exclusao = ["security clearance", "citizens only", "us only", "us based", "c2c only"]
        if any(termo in texto for termo in termos_exclusao):
            return False

    if apenas_remoto:
        termos_presencial_estrito = ["100% presencial", "presencial apenas", "local only", "must be located in", "on-site only"]
        if any(termo in texto for termo in termos_presencial_estrito):
            return False

    return True


def classificar_senioridade(titulo: str, descricao: str, padrao_junior: bool) -> SeniorityEnum:
    t_lower = titulo.lower()
    d_lower = descricao.lower()

    if any(k in t_lower for k in ["estágio", "estagio", "intern", "trainee"]):
        return SeniorityEnum.ESTAGIO
    if any(k in t_lower for k in ["júnior", "junior", "jr", "entry level", "jr.", "nivel 1", "nível 1", "desenvolvedor 1"]):
        return SeniorityEnum.JUNIOR
    if any(k in t_lower for k in ["sênior", "senior", "sr", "sr.", "lead", "tech lead", "staff", "principal", "especialista", "iii"]):
        return SeniorityEnum.SENIOR
    if any(k in t_lower for k in ["pleno", "pl", "pl.", "ii"]):
        return SeniorityEnum.PLENO

    if any(k in d_lower for k in ["júnior", "junior", "jr.", "entry-level", "entry level", "sem experiência previa"]):
        return SeniorityEnum.JUNIOR
    if any(k in d_lower for k in ["sênior", "senior", "sr.", "tech lead", "arqueto", "architect"]):
        return SeniorityEnum.SENIOR
    if any(k in d_lower for k in ["pleno", "pl."]):
        return SeniorityEnum.PLENO

    return SeniorityEnum.JUNIOR if padrao_junior else SeniorityEnum.NAO_ESPECIFICADO


def classificar_modelo_trabalho(titulo: str, localizacao: str, descricao: str, padrao_remoto: bool) -> WorkModelEnum:
    texto = f"{titulo} {localizacao} {descricao}".lower()

    termos_hibrido = [
        "híbrido", "hibrido", "hybrid", "híbrida", "hibrida",
        "modelo híbrido", "modelo hibrido", "trabalho híbrido", "trabalho hibrido",
        "híbrido em", "hibrido em", "presencial/remoto", "remoto/presencial"
    ]
    termos_presencial = [
        "presencial", "on-site", "onsite", "escritório", "escritorio",
        "100% presencial", "modelo presencial", "trabalho presencial", "vaga presencial",
        "atuação presencial", "atuacao presencial", "alocação presencial"
    ]

    if any(k in texto for k in termos_hibrido):
        return WorkModelEnum.HIBRIDO
    if any(k in texto for k in termos_presencial):
        return WorkModelEnum.PRESENCIAL

    termos_remoto = ["remoto", "remote", "home office", "home-office", "teletrabalho", "work from home", "100% remoto"]
    if any(k in texto for k in termos_remoto):
        return WorkModelEnum.REMOTO

    return WorkModelEnum.REMOTO if padrao_remoto else WorkModelEnum.NAO_ESPECIFICADO
