# 🚀 Job Search - LinkedIn Automated Scraper & Resume Matcher

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/managed__by-uv-261230?logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![LinkedIn API](https://img.shields.io/badge/LinkedIn-Guest__API-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/jobs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, multi-threaded Python automation tool designed to search, filter, extract, and match tech job listings from LinkedIn into structured JSON data (`vagas_linkedin.json`) and formatted Markdown reports (`relatorio_matches.md`). 

The pipeline features an automated resume matching engine tailored for **Backend** and **Full-Stack** developer profiles, analyzing full job descriptions fetched in parallel via public guest endpoints without requiring credentials or session cookies.

---

## 🌟 Key Features

- **🔑 No Authentication Required**: Leverages public LinkedIn Guest endpoints (`/jobs-guest/jobs/api/...`) to query listings without needing API keys, login accounts, or cookies.
- **⚡ Aggressive Parallel Fetching**: Uses `concurrent.futures.ThreadPoolExecutor` to fetch full job descriptions concurrently for maximum processing speed.
- **🎯 Rigorous Post-Fetch Filtering**: Eliminates misclassified positions by validating title, location, and description strings against strict remote/hybrid/on-site and seniority criteria.
- **🧠 Resume Match Score Engine**: Evaluates job descriptions against multiple developer profiles (Backend & Full-Stack), calculating compatibility scores based on key technical skills (Python, Django, FastAPI, PostgreSQL, Vue, React, Docker, Cloud, REST APIs, etc.).
- **📊 Multi-Format Reporting**: Generates a clean structured dataset in `vagas_linkedin.json` and a ranked, human-readable report in `relatorio_matches.md`.

---

## 🏗️ Architecture & Workflow

```
                           +-------------------------------+
                           |      LinkedIn Guest API       |
                           +---------------+---------------+
                                           |
                                           v
+------------------------+  Search Query   +-------------------------------+
|  Search Configuration  |---------------> |   `seeMoreJobPostings/search`  |
|  (Keywords, Recency,   |                 +---------------+---------------+
|  Seniority, Location)  |                                 | Extract Job IDs
+------------------------+                                 v
                                           +-------------------------------+
                                           | Aggressive Parallel Fetcher   |
                                           |  ThreadPoolExecutor (N=10)    |
                                           |     `jobPosting/{job_id}`     |
                                           +---------------+---------------+
                                                           |
                                                           v
                                           +-------------------------------+
                                           |   Strict Filter & Validator   |
                                           | (Workplace Type & Seniority)  |
                                           +---------------+---------------+
                                                           |
                                                           v
+------------------------+                 +-------------------------------+
|  Resume Source Files   |---------------> | Resume Match Score Engine     |
| (Backend & Full-Stack) |                 | (Skill Extraction & Ranking)  |
+------------------------+                 +---------------+---------------+
                                                           |
                                           +---------------+---------------+
                                           |                               |
                                           v                               v
                            +------------------------------+ +------------------------------+
                            |     `vagas_linkedin.json`    | |    `relatorio_matches.md`    |
                            |      (Structured JSON)       | |     (Markdown Summary)       |
                            +------------------------------+ +------------------------------+
```

---

## 📁 Repository Structure

```
job-search/
├── main.py                          # Main entry point: search logic, filtering, parallel fetching, pipeline orchestrator
├── pos_processamento.py             # Resume matching engine: skill extractor, score calculation, report generator
├── relatorio_matches.md             # Generated Markdown report: ranked jobs by compatibility score
├── vagas_linkedin.json              # Output file: structured listings, metadata, and match scores
├── Miguel's Resume - Backend.md     # Source resume profile for Backend Python Engineer
├── Miguel's Resume - Full-stack.md   # Source resume profile for Full-Stack Python Engineer
├── pyproject.toml                   # Project configuration and dependency specifications
├── uv.lock                          # Dependency lockfile managed by uv
└── GEMINI.md                        # Context and architecture guidelines for AI agents
```

---

## ⚡ Tech Stack & Environment

- **Language**: Python (`>= 3.14`)
- **Package & Environment Manager**: [`uv`](https://github.com/astral-sh/uv)
- **Key Dependencies**:
  - [`requests`](https://pypi.org/project/requests/): Direct HTTP requests execution against LinkedIn Guest API endpoints.
  - [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/): HTML parsing for card elements and full job descriptions.
  - `concurrent.futures.ThreadPoolExecutor`: Multi-threaded parallel processing for fast payload fetching.

---

## 🚀 Quick Start

### Prerequisites

Ensure you have Python `>= 3.14` and [`uv`](https://github.com/astral-sh/uv) installed on your system.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/job-search.git
   cd job-search
   ```

2. **Synchronize environment & dependencies**:
   ```bash
   uv sync
   ```

---

## ⚙️ Configuration & Execution

### 1. Configure Search Settings

Open `main.py` and customize your search criteria:

```python
# Recency filter: r86400 (24 hours), r604800 (7 days), r2592000 (30 days)
FILTRO_TEMPO = "r604800"

# Workplace filter: True to filter ONLY 100% remote positions
APENAS_REMOTO = True

# Seniority filter: "JUNIOR", "PLENO", "SENIOR", "TODAS"
# Maps to LinkedIn f_E parameters (1=Internship, 2=Junior/Entry level, 3=Associate, 4=Mid-Senior)
SENIORIDADE_FILTRO = "JUNIOR"
```

Keywords searched by default include:
- `Python Junior`
- `Desenvolvedor Python Junior`
- `Backend Developer Junior`
- `Full Stack Developer Junior`

### 2. Run the Full Scraper & Match Pipeline

Execute the full extraction, post-processing, and reporting workflow:

```bash
uv run python main.py
```

### 3. Run Standalone Post-Processing

If you already have `vagas_linkedin.json` populated and want to re-run or test the resume matching engine:

```bash
uv run python pos_processamento.py
```

---

## 📊 Output Schemas

### Structured Dataset (`vagas_linkedin.json`)

```json
{
    "termo_pesquisado": "Python Junior | Desenvolvedor Python Junior",
    "filtro_tempo": "r604800",
    "apenas_remoto": true,
    "senioridade_filtrada": "JUNIOR",
    "total_extraido": 42,
    "vagas": [
        {
            "job_id": "4192502474",
            "titulo": "Python Junior Developer - Remote Work",
            "empresa": "Tech Company",
            "localizacao": "Brazil",
            "data_postagem": "2026-08-28",
            "senioridade": "Júnior",
            "modelo_trabalho": "Remoto",
            "link": "https://br.linkedin.com/jobs/view/...",
            "descricao_resumida": "Short snippet of the job posting...",
            "descricao_completa": "Full detailed job description text...",
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

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit pull requests.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
