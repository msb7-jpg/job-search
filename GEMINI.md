# Gemini Context: job-search

This repository contains a Python automation tool designed to search, filter, extract, and post-process tech job listings from LinkedIn into structured JSON format (`vagas_linkedin.json`), featuring automated resume matching for Backend & Full-Stack developer profiles and generating formatted Markdown reports (`relatorio_matches.md`).

---

## Project Overview

- **Name**: `job-search`
- **Main Goal**: Search and extract tech job postings (Python, Django, FastAPI, Vue, React) with filtering by **Seniority** (e.g. Junior/Entry Level), **Recency** (e.g. last 7 days), and **Workplace Type** (Remote vs On-site), complete with full job descriptions fetched via aggressive parallel processing and automated **Resume Match Scoring** for 2 resume versions (`Miguel's Resume - Backend.md` and `Miguel's Resume - Full-stack.md`).

---

## Tech Stack & Environment

- **Language**: Python (>= 3.14)
- **Package & Environment Manager**: `uv`
- **Key Dependencies**:
  - `requests`: Direct HTTP execution for LinkedIn Guest API endpoints.
  - `beautifulsoup4` (`bs4`): HTML parsing for card elements and full job descriptions.
  - `concurrent.futures.ThreadPoolExecutor`: Multi-threaded parallel fetching ("Aggressive Fetch").

---

## Repository Structure

```
job-search/
├── main.py                          # Main entry point: search logic, API filtering, parallel description fetch, pipeline orchestrator
├── pos_processamento.py             # Post-processing module: resume matching engine for Backend & Full-stack profiles
├── relatorio_matches.md             # Generated Markdown report: ranked job listings by match score
├── Miguel's Resume - Backend.md    # Source resume for Backend Python Engineer profile
├── Miguel's Resume - Full-stack.md  # Source resume for Full-Stack Python Engineer profile
├── pyproject.toml                   # Project configuration and dependency specifications (managed by uv)
├── uv.lock                          # Lockfile for reproducible dependencies
├── vagas_linkedin.json              # Output file generated containing structured job listings and match scores
├── GEMINI.md                        # Gemini agent context, API specs, and project guidelines
└── README.md                        # Documentation
```

---

## LinkedIn Guest API Specifications & Architecture

This repository utilizes **LinkedIn's public guest endpoints** for reliable data extraction without requiring authentication or cookies.

### 1. Search Endpoint
```http
GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_TPR={f_TPR}&f_WT={f_WT}&f_E={f_E}&start={start}
```

#### Query Parameters:
- `keywords`: Tech search query (e.g., `Python Junior`, `Desenvolvedor Python Junior`).
- `location`: Location string (e.g., `Brazil`, `Remote`).
- `f_TPR` (Time Posted Range / Recency):
  - `r86400`: Past 24 hours (1 day)
  - `r604800`: Past week (7 days)
  - `r2592000`: Past month (30 days)
- `f_WT` (Workplace Type):
  - `1`: On-site (Presencial)
  - `2`: Remote (Remoto)
  - `3`: Hybrid (Híbrido)
- `f_E` (Experience Level / Seniority):
  - `1`: Internship (Estágio)
  - `2`: Entry level / Junior (Júnior)
  - `3`: Associate
  - `4`: Mid-Senior level (Pleno / Sênior)
- `start`: Pagination offset (`0`, `25`, `50`, ...).

### 2. Aggressive Fetch Endpoint (Full Job Description)
```http
GET https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}
```
- **Target Element**: `<div class="show-more-less-html__markup">` or `<section class="description">`.
- **Method**: Extracted via `ThreadPoolExecutor(max_workers=10)` to populate `descricao_completa` for all listings concurrently.

---

## Resume Matching System (Post-Processing)

The post-processing pipeline (`pos_processamento.py`) evaluates each extracted job against two resume files:
- `Miguel's Resume - Backend.md` (Focus: Python, Django, FastAPI, PostgreSQL, Redis, RabbitMQ, Celery, Docker, REST APIs, Pytest, AWS/GCP, Semantic Search).
- `Miguel's Resume - Full-stack.md` (Focus: Python, Django, FastAPI, Vue.js, React.js, TypeScript, JavaScript, PostgreSQL, Docker, REST APIs, Pytest, Jest).

### Outputs:
1. **`vagas_linkedin.json`**: Enriched with `"match_curriculo": { "backend": ..., "fullstack": ... }`.
2. **`relatorio_matches.md`**: Dedicated human-readable Markdown report ranking the best matching job listings per resume profile.

---

## Output Data Schema (`vagas_linkedin.json`)

The output file format contains metadata, array of job listings, and calculated match metrics for both resumes:

```json
{
    "termo_pesquisado": "Query summary string",
    "filtro_tempo": "r604800",
    "apenas_remoto": true,
    "senioridade_filtrada": "JUNIOR",
    "total_extraido": 82,
    "vagas": [
        {
            "job_id": "4192502474",
            "titulo": "Python Junior Developer - Remote Work",
            "empresa": "Company Name",
            "localizacao": "Location",
            "data_postagem": "Post Date String",
            "senioridade": "Júnior",
            "modelo_trabalho": "Remoto",
            "link": "https://br.linkedin.com/jobs/view/...",
            "descricao_resumida": "Short summary",
            "descricao_completa": "Full job description text...",
            "match_curriculo": {
                "backend": {
                    "score_porcentagem": 80,
                    "nivel": "Excelente",
                    "habilidades_compativeis": ["Docker", "Git", "Python", "REST APIs", "Redis", "SQL"],
                    "total_habilidades_encontradas": 6
                },
                "fullstack": {
                    "score_porcentagem": 80,
                    "nivel": "Excelente",
                    "habilidades_compativeis": ["Docker", "JavaScript", "Python", "REST APIs", "Redis", "SQL"],
                    "total_habilidades_encontradas": 6
                }
            }
        }
    ]
}
```

---

## Workflows & Common Commands

- **Sync Environment**:
  ```bash
  uv sync
  ```

- **Run Complete Scraper & Match Pipeline**:
  ```bash
  uv run python main.py
  ```

- **Run Standalone Post-Processing Matcher**:
  ```bash
  uv run python pos_processamento.py
  ```

- **Add Dependencies**:
  ```bash
  uv add <package_name>
  ```

---

## Development Guidelines

1. **Package Management**: Always use `uv` (`uv run`, `uv add`, `uv sync`) for environment execution.
2. **Filtering Rules**:
   - `f_E=2` for Entry Level / Junior positions.
   - `f_WT=2` for remote filtering.
   - `f_TPR` for time filtering.
   - Post-fetch validation (`identificar_senioridade` & `identificar_modelo_trabalho`) to strictly discard any listings containing `Híbrido`/`Hybrid`/`On-site`/`Presencial` badges or mid/senior/lead titles when `APENAS_REMOTO` or `SENIORIDADE_FILTRO` is enabled.
3. **Concurrency**: Keep aggressive fetching parallelized via `ThreadPoolExecutor` to maintain high execution speed.
4. **Post-Processing Persistence**: Automatically calculate and store `match_curriculo` metrics in `vagas_linkedin.json` and generate the formatted Markdown report `relatorio_matches.md`.
5. **Encoding**: Save output using `utf-8` encoding with `ensure_ascii=False`.
6. **Self-Update Directive**: The AI agent MUST automatically update `GEMINI.md` whenever relevant architectural, feature, endpoint, or guideline changes are implemented in the codebase to persist context for future sessions.
