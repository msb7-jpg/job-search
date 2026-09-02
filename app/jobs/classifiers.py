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


def avaliar_pre_filtro_job_bruto(
    titulo: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> tuple[bool, str | None]:
    titulo_minusculo = titulo.lower()
    localizacao_minusculo = localizacao.lower()
    texto_basico = f"{titulo_minusculo} {localizacao_minusculo}"

    if senioridade_filtro == "JUNIOR" and any(
        palavra_bloqueada in titulo_minusculo for palavra_bloqueada in BLOQUEADOS_SENIORIDADE_JUNIOR
    ):
        return False, "senioridade_incompativel"

    if apenas_remoto and any(palavra_bloqueada in texto_basico for palavra_bloqueada in BLOQUEADOS_PRESENCIAL):
        return False, "modelo_presencial"

    return True, None


def pre_filtrar_job_bruto(
    titulo: str,
    localizacao: str,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> bool:
    aprovado, _motivo = avaliar_pre_filtro_job_bruto(
        titulo=titulo,
        localizacao=localizacao,
        apenas_remoto=apenas_remoto,
        senioridade_filtro=senioridade_filtro,
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

    if senioridade_filtro == "JUNIOR":
        if any(
            palavra_bloqueada in titulo_minusculo
            for palavra_bloqueada in ["senior", "sênior", "sr", "sr.", "ssr", "pleno", "pl", "lead", "principal", "architect", "staff"]
        ):
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
    titulo_minusculo = titulo.lower()
    descricao_minusculo = descricao.lower()

    if any(palavra_chave in titulo_minusculo for palavra_chave in ["estágio", "estagio", "intern", "trainee"]):
        return SeniorityEnum.ESTAGIO
    if any(
        palavra_chave in titulo_minusculo
        for palavra_chave in ["júnior", "junior", "jr", "entry level", "jr.", "nivel 1", "nível 1", "desenvolvedor 1"]
    ):
        return SeniorityEnum.JUNIOR
    if any(
        palavra_chave in titulo_minusculo
        for palavra_chave in ["sênior", "senior", "sr", "sr.", "lead", "tech lead", "staff", "principal", "especialista", "iii"]
    ):
        return SeniorityEnum.SENIOR
    if any(palavra_chave in titulo_minusculo for palavra_chave in ["pleno", "pl", "pl.", "ii"]):
        return SeniorityEnum.PLENO

    if any(
        palavra_chave in descricao_minusculo
        for palavra_chave in ["júnior", "junior", "jr.", "entry-level", "entry level", "sem experiência previa"]
    ):
        return SeniorityEnum.JUNIOR
    if any(
        palavra_chave in descricao_minusculo for palavra_chave in ["sênior", "senior", "sr.", "tech lead", "arqueto", "architect"]
    ):
        return SeniorityEnum.SENIOR
    if any(palavra_chave in descricao_minusculo for palavra_chave in ["pleno", "pl."]):
        return SeniorityEnum.PLENO

    return SeniorityEnum.JUNIOR if padrao_junior else SeniorityEnum.NAO_ESPECIFICADO


def classificar_modelo_trabalho(titulo: str, localizacao: str, descricao: str, padrao_remoto: bool) -> WorkModelEnum:
    texto = f"{titulo} {localizacao} {descricao}".lower()

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
    ]

    if any(palavra_chave in texto for palavra_chave in termos_hibrido):
        return WorkModelEnum.HIBRIDO
    if any(palavra_chave in texto for palavra_chave in termos_presencial):
        return WorkModelEnum.PRESENCIAL

    termos_remoto = ["remoto", "remote", "home office", "home-office", "teletrabalho", "work from home", "100% remoto"]
    if any(palavra_chave in texto for palavra_chave in termos_remoto):
        return WorkModelEnum.REMOTO

    return WorkModelEnum.REMOTO if padrao_remoto else WorkModelEnum.NAO_ESPECIFICADO
