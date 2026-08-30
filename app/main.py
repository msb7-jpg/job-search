import json
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bs4 import BeautifulSoup
from pos_processamento import processar_vagas_com_curriculo
from posts_fetcher import buscar_posts_linkedin

from app.fetcher import requisicao_com_rotacao, rotator
from app.queries import Gringas, Nacionais

# Direcionamento do diretório de dados
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)




# Configurações de Filtro
FILTRO_TEMPO = "r604800"
APENAS_REMOTO = True
SENIORIDADE_FILTRO = "JUNIOR"




# ==========================================
# 2. FILTRAGEM PRÉVIA (SEM FAZER FETCH DUPLO)
# ==========================================
def pre_filtrar_item(item: dict) -> bool:
    """
    Descarta rapidamente itens com base no título e localização
    antes de gastar requisições buscando o conteúdo completo.
    """
    titulo = item.get("titulo", "").lower()
    loc = item.get("localizacao", "").lower()
    texto_basico = f"{titulo} {loc}"

    # Descarte de Senioridade incompatível se o filtro for JUNIOR
    if SENIORIDADE_FILTRO == "JUNIOR":
        palavras_bloqueadas_senioridade = ["senior", "sênior", "sr.", "lead", "principal", "architect", "arqueto", "especialista", "iii"]
        if any(p in titulo for p in palavras_bloqueadas_senioridade):
            return False

    # Descarte de Modalidade se for APENAS_REMOTO
    if APENAS_REMOTO:
        palavras_bloqueadas_presencial = ["presencial", "onsite", "100% presencial", "híbrido", "hibrido", "hybrid"]
        if any(p in texto_basico for p in palavras_bloqueadas_presencial):
            return False

    return True


def identificar_senioridade(titulo: str, descricao: str) -> str:
    """
    Classifica a senioridade da vaga com base no título e descrição completa.
    """
    t_lower = titulo.lower()
    d_lower = descricao.lower()

    if any(k in t_lower for k in ["estágio", "estagio", "intern", "trainee"]):
        return "Estágio"
    if any(k in t_lower for k in ["júnior", "junior", "jr", "entry level", "jr.", "nivel 1", "nível 1", "desenvolvedor 1"]):
        return "Júnior"
    if any(k in t_lower for k in ["sênior", "senior", "sr", "sr.", "lead", "tech lead", "staff", "principal", "especialista", "iii"]):
        return "Sênior"
    if any(k in t_lower for k in ["pleno", "pl", "pl.", "ii"]):
        return "Pleno"

    if any(k in d_lower for k in ["júnior", "junior", "jr.", "entry-level", "entry level", "sem experiência previa"]):
        return "Júnior"
    if any(k in d_lower for k in ["sênior", "senior", "sr.", "tech lead", "arqueto", "architect"]):
        return "Sênior"
    if any(k in d_lower for k in ["pleno", "pl."]):
        return "Pleno"

    return "Júnior" if SENIORIDADE_FILTRO == "JUNIOR" else "Não Especificado"


def identificar_modelo_trabalho(titulo: str, localizacao: str, descricao: str) -> str:
    """
    Classifica rigorosamente o modelo de trabalho descartando badges/menções de Híbrido ou Presencial.
    """
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
        return "Híbrido"

    if any(k in texto for k in termos_presencial):
        return "Presencial"

    termos_remoto = ["remoto", "remote", "home office", "home-office", "teletrabalho", "work from home", "100% remoto"]
    if any(k in texto for k in termos_remoto):
        return "Remoto"

    return "Remoto" if APENAS_REMOTO else "Não Especificado"


def obter_descricao_completa(job_id: str) -> str:
    """
    Busca o conteúdo completo da página da vaga (Aggressive Fetch).
    """
    if not job_id:
        return ""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        response = requisicao_com_rotacao(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            desc_elem = soup.find("div", class_="show-more-less-html__markup") or soup.find("section", class_="description")
            if desc_elem:
                return desc_elem.get_text(separator="\n").strip()
    except Exception:
        pass
    return ""


def buscar_vagas_linkedin_guest(
    keywords: str,
    location: str = "Brazil",
    filtro_tempo: str = FILTRO_TEMPO,
    apenas_remoto: bool = APENAS_REMOTO,
    senioridade_filtro: str = SENIORIDADE_FILTRO,
    max_paginas: int = 3
):
    """
    Busca vagas na API do LinkedIn aplicando filtros de recência (f_TPR), trabalho remoto (f_WT=2) e senioridade (f_E=2).
    """
    vagas = []
    filtro_remoto_param = "&f_WT=2" if apenas_remoto else ""
    filtro_senioridade_param = "&f_E=2" if senioridade_filtro == "JUNIOR" else ""

    for pagina in range(max_paginas):
        start = pagina * 25
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={urllib.parse.quote(keywords)}&location={urllib.parse.quote(location)}"
            f"&f_TPR={filtro_tempo}{filtro_remoto_param}{filtro_senioridade_param}&start={start}"
        )
        try:
            response = requisicao_com_rotacao(url)
            if not response or response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li")
            if not items:
                break

            for li in items:
                title_tag = li.find("h3", class_="base-search-card__title")
                company_tag = li.find("h4", class_="base-search-card__subtitle")
                location_tag = li.find("span", class_="job-search-card__location")
                link_tag = li.find("a", class_="base-card__full-link")
                date_tag = li.find("time", class_="job-search-card__listdate") or li.find("time", class_="job-search-card__listdate--new")

                if title_tag and link_tag:
                    link = link_tag["href"].split("?")[0]
                    titulo = title_tag.get_text().strip()
                    empresa = company_tag.get_text().strip() if company_tag else "N/A"
                    localizacao = location_tag.get_text().strip() if location_tag else location
                    data_postagem = date_tag.get_text().strip() if date_tag else "Recente"

                    match_id = re.search(r"-(\d+)(?:\?|$)", link)
                    job_id = match_id.group(1) if match_id else ""

                    vagas.append({
                        "job_id": job_id,
                        "titulo": titulo,
                        "empresa": empresa,
                        "localizacao": localizacao,
                        "data_postagem": data_postagem,
                        "senioridade": "Júnior" if senioridade_filtro == "JUNIOR" else "A determinar",
                        "modelo_trabalho": "Remoto" if apenas_remoto else "A determinar",
                        "link": link,
                        "descricao_resumida": f"{empresa} - {localizacao}",
                        "descricao_completa": ""
                    })
        except Exception as e:
            print(f"Erro ao buscar '{keywords}' em '{location}': {e}")
            break

    print(f"🔹 Busca concluída para '{keywords}' em '{location}': {len(vagas)} vagas encontradas.")
    return vagas


def buscar_vagas_completas():
    # 1. Executando Posts com as Queries Validadas
    print("🔎 1/2. Buscando Posts do LinkedIn via SearXNG (Nacional e Internacional)...")

    posts_nacionais = []
    for query in (Nacionais.POSTS_BE, Nacionais.POSTS_FS):
        posts_nacionais.extend(buscar_posts_linkedin(query, escopo="nacional"))

    posts_internacionais = []
    for query in (Gringas.POSTS_BE, Gringas.POSTS_FS):
        posts_internacionais.extend(buscar_posts_linkedin(query, escopo="internacional"))

    # Deduplicar posts por URL
    posts_nacionais_unique = list({post["link"]: post for post in posts_nacionais}.values())
    posts_internacionais_unique = list({post["link"]: post for post in posts_internacionais}.values())

    # 2. Queries de Vagas Formais (Jobs API)
    # As queries de jobs validadas devem ser usadas na busca do LinkedIn Guest.
    termos_jobs_br = [
        ("Python FastAPI Django PostgreSQL", "Brazil"),
        ("Python Vue React PostgreSQL", "Brazil"),
        ("Desenvolvedor Python Junior", "Brazil")
    ]
    termos_jobs_gringa = [
        (Gringas.JOBS_BE, "Remote"),
        (Gringas.JOBS_FS, "Remote")
    ]

    print("🔎 2/2. Buscando Vagas Formais (Jobs) no LinkedIn Guest API...")
    jobs_nacionais_brutos = []
    for keyword, location in termos_jobs_br:
        jobs_nacionais_brutos.extend(buscar_vagas_linkedin_guest(keyword, location, FILTRO_TEMPO, APENAS_REMOTO, SENIORIDADE_FILTRO))

    jobs_internacionais_brutos = []
    for keyword, location in termos_jobs_gringa:
        jobs_internacionais_brutos.extend(buscar_vagas_linkedin_guest(keyword, location, FILTRO_TEMPO, APENAS_REMOTO, SENIORIDADE_FILTRO))

    # Deduplicar jobs
    jobs_nac_dict = {job["link"]: job for job in jobs_nacionais_brutos}
    jobs_int_dict = {job["link"]: job for job in jobs_internacionais_brutos}

    for job in jobs_nac_dict.values():
        job["tipo"] = "job"
        job["escopo"] = "nacional"

    for job in jobs_int_dict.values():
        job["tipo"] = "job"
        job["escopo"] = "internacional"

    jobs_nacionais = list(jobs_nac_dict.values())
    jobs_internacionais = list(jobs_int_dict.values())

    todas_vagas_formais = jobs_nacionais + jobs_internacionais
    vagas_filtradas = [v for v in todas_vagas_formais if pre_filtrar_item(v)]

    print(f"\nObtidas {len(todas_vagas_formais)} vagas formais brutas. Filtradas {len(todas_vagas_formais) - len(vagas_filtradas)} por título/localização.")
    print(f"Restam {len(vagas_filtradas)} vagas formais para Aggressive Fetch.")

    def buscar_conteudo(vaga):
        if vaga.get("job_id") and not vaga.get("job_id").startswith("post_"):
            desc = obter_descricao_completa(vaga["job_id"])
            vaga["descricao_completa"] = desc
            vaga["modelo_trabalho"] = identificar_modelo_trabalho(vaga["titulo"], vaga["localizacao"], desc)
            vaga["senioridade"] = identificar_senioridade(vaga["titulo"], desc)
        return vaga

    with ThreadPoolExecutor(max_workers=10) as executor:
        vagas_processadas = list(executor.map(buscar_conteudo, vagas_filtradas))

    # Re-filtrar modalidade/senioridade pós-fetch
    if APENAS_REMOTO:
        vagas_processadas = [v for v in vagas_processadas if v["modelo_trabalho"] == "Remoto"]
    if SENIORIDADE_FILTRO == "JUNIOR":
        vagas_processadas = [v for v in vagas_processadas if v["senioridade"] in ["Júnior", "Estágio", "Não Especificado"]]

    jobs_nac_filtrados = [v for v in vagas_processadas if v["escopo"] == "nacional"]
    jobs_int_filtrados = [v for v in vagas_processadas if v["escopo"] == "internacional"]

    # Montar lista consolidada para o pós-processamento
    todos_itens = jobs_nac_filtrados + jobs_int_filtrados + posts_nacionais_unique + posts_internacionais_unique

    dados_finais = {
        "termo_pesquisado": "Vagas Formais & Posts LinkedIn (BR & Gringa)",
        "filtro_tempo": FILTRO_TEMPO,
        "apenas_remoto": APENAS_REMOTO,
        "senioridade_filtrada": SENIORIDADE_FILTRO,
        "total_extraido": len(todos_itens),
        "vagas": todos_itens
    }

    arquivo_saida = DATA_DIR / "vagas_linkedin.json"
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"\nSucesso! {len(todos_itens)} itens salvos temporariamente em '{arquivo_saida}'. Iniciando pós-processamento...")
    processar_vagas_com_curriculo(str(arquivo_saida))

def main():
    print(f"Iniciando Pipeline de Busca (Recência: {FILTRO_TEMPO} | Remoto: {APENAS_REMOTO} | Senioridade: {SENIORIDADE_FILTRO})...")
    rotator.inicializar_pool(max_concurrency=200)

    buscar_vagas_completas()

if __name__ == "__main__":
    main()
