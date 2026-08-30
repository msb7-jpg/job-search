from app.models.enums import SeniorityEnum, WorkModelEnum


def pre_filtrar_job_bruto(titulo: str, localizacao: str, apenas_remoto: bool = True, senioridade_filtro: str = "JUNIOR") -> bool:
    t_lower = titulo.lower()
    loc_lower = localizacao.lower()
    texto_basico = f"{t_lower} {loc_lower}"

    if senioridade_filtro == "JUNIOR":
        bloqueados_senioridade = ["senior", "sênior", "sr.", "lead", "principal", "architect", "arqueto", "especialista", "iii"]
        if any(p in t_lower for p in bloqueados_senioridade):
            return False

    if apenas_remoto:
        bloqueados_presencial = ["presencial", "onsite", "100% presencial", "híbrido", "hibrido", "hybrid"]
        if any(p in texto_basico for p in bloqueados_presencial):
            return False

    return True

def classificar_senioridade(titulo: str, descricao: str, padrao_junior: bool = True) -> SeniorityEnum:
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

def classificar_modelo_trabalho(titulo: str, localizacao: str, descricao: str, padrao_remoto: bool = True) -> WorkModelEnum:
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
