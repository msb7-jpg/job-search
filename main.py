import json
import urllib.parse
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pos_processamento import processar_vagas_com_curriculo

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Configurações de Filtro
# Recência: r86400 (24h), r604800 (7 dias), r2592000 (30 dias)
FILTRO_TEMPO = "r604800"

# Modelo de Trabalho: True para filtrar APENAS vagas 100% remotas
APENAS_REMOTO = True

# Senioridade: "JUNIOR", "PLENO", "SENIOR", "TODAS"
# f_E no LinkedIn: 1=Estágio, 2=Júnior/Entry level, 3=Associate, 4=Pleno/Sênior
SENIORIDADE_FILTRO = "JUNIOR"

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
        response = requests.get(url, headers=HEADERS, timeout=7)
        if response.status_code == 200:
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
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
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
    return vagas

def main():
    tipo_remoto = "APENAS REMOTAS (100% REMOTE)" if APENAS_REMOTO else "TODAS"
    print(f"Iniciando busca no LinkedIn (Recência: {FILTRO_TEMPO} | Modelo: {tipo_remoto} | Senioridade: {SENIORIDADE_FILTRO})...")

    # Termos de busca expandidos para maximizar captura de vagas Entry-level/Júnior
    termos_busca = [
        ("Python", "Brazil"),
        ("Python Junior", "Brazil"),
        ("Desenvolvedor Python", "Brazil"),
        ("Python Django", "Brazil"),
        ("Python FastAPI", "Brazil"),
        ("Desenvolvedor Backend", "Brazil"),
        ("Python Fullstack", "Brazil"),
        ("Python React", "Remote"),
        ("Python Vue", "Remote"),
    ]

    vagas_encontradas = []
    links_vistos = set()

    for keywords, location in termos_busca:
        print(f"Buscando '{keywords}' em '{location}'...")
        novas_vagas = buscar_vagas_linkedin_guest(
            keywords, location, filtro_tempo=FILTRO_TEMPO, apenas_remoto=APENAS_REMOTO, senioridade_filtro=SENIORIDADE_FILTRO
        )

        for vaga in novas_vagas:
            if vaga["link"] not in links_vistos:
                links_vistos.add(vaga["link"])
                vagas_encontradas.append(vaga)

    print(f"\nObtidas {len(vagas_encontradas)} vagas brutas. Iniciando Aggressive Fetch (conteúdo completo)...")

    def buscar_conteudo(vaga):
        if vaga["job_id"]:
            desc = obter_descricao_completa(vaga["job_id"])
            vaga["descricao_completa"] = desc
            vaga["modelo_trabalho"] = identificar_modelo_trabalho(vaga["titulo"], vaga["localizacao"], desc)
            vaga["senioridade"] = identificar_senioridade(vaga["titulo"], desc)
        return vaga

    with ThreadPoolExecutor(max_workers=10) as executor:
        vagas_encontradas = list(executor.map(buscar_conteudo, vagas_encontradas))

    if APENAS_REMOTO:
        vagas_encontradas = [v for v in vagas_encontradas if v["modelo_trabalho"] == "Remoto"]
    
    if SENIORIDADE_FILTRO == "JUNIOR":
        vagas_encontradas = [v for v in vagas_encontradas if v["senioridade"] in ["Júnior", "Estágio", "Não Especificado"]]

    query_resumo = f'LinkedIn Search (Python / Django / FastAPI / Vue / React) [Recência: {FILTRO_TEMPO}, Remoto Estrito: {APENAS_REMOTO}, Senioridade: {SENIORIDADE_FILTRO}]'

    dados_finais = {
        "termo_pesquisado": query_resumo,
        "filtro_tempo": FILTRO_TEMPO,
        "apenas_remoto": APENAS_REMOTO,
        "senioridade_filtrada": SENIORIDADE_FILTRO,
        "total_extraido": len(vagas_encontradas),
        "vagas": vagas_encontradas
    }

    nome_arquivo = "vagas_linkedin.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"\nSucesso! {len(vagas_encontradas)} vagas 100% REMOTAS e nível JÚNIOR salvas em '{nome_arquivo}'.")

    # Executa o pós-processamento para atualizar JSON e gerar relatorio_matches.md
    processar_vagas_com_curriculo(nome_arquivo)

if __name__ == "__main__":
    main()
