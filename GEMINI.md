# Gemini Context: job-search

This repository contains a modular Python automation tool designed to search, filter, extract, and post-process tech job listings and LinkedIn posts into structured JSON format (`vagas_processadas.json`), featuring automated resume matching for Backend & Full-Stack developer profiles and generating formatted Markdown reports (`relatorio_matches.md`).

---

## Project Architecture & Design Principles

The codebase is strictly modularized into self-contained domains with single responsibilities, typed Pydantic models, encapsulated facades, and standardized logging.

### Architecture Overview

```text
app/
├── core/
│   ├── config.py                 # Central settings (Settings) with Pydantic
│   └── logging.py                # Centralized structured logger setup
│
├── models/                       # Strict Pydantic models & StrEnums
│   ├── enums.py                  # ScopeEnum, ItemTypeEnum, SeniorityEnum, WorkModelEnum, MatchLevelEnum
│   ├── job.py                    # JobItem schema (LinkedIn Jobs)
│   ├── post.py                   # PostItem schema (LinkedIn Feed Posts)
│   ├── match.py                  # ProfileMatch, ResumeMatch schemas
│   └── report.py                 # ScopeContainer, ProcessedDataOutput schemas
│
├── jobs/                         # 💼 JOBS DOMAIN (Formal LinkedIn Jobs)
│   ├── queries.py                # Queries for national and international jobs
│   ├── classifiers.py            # Pure heuristics (seniority, work model, pre-filter)
│   ├── fetcher.py                # LinkedIn Guest API search & pagination
│   ├── detail_fetcher.py         # Concurrent aggressive fetch for full descriptions
│   └── facade.py                 # JobsPipelineFacade
│
├── posts/                        # 💬 POSTS DOMAIN (LinkedIn Feed Posts)
│   ├── queries.py                # Boolean queries for post discovery
│   ├── searxng_client.py         # SearXNG container health-check & auto-start
│   ├── fetcher.py                # SearXNG post scraper, snippet parser & deduplication
│   └── facade.py                 # PostsPipelineFacade
│
├── shared/                       # 🛠️ SHARED INFRASTRUCTURE
│   └── http/
│       ├── proxy_rotator.py      # Async proxy scraper, validator & rotator
│       └── client.py             # Resilient HTTP request wrapper with bounded retries and fast exits on 401/403/429
│
├── matchers/                     # 🎯 RESUME MATCHING ENGINE
│   ├── skills_definitions.py     # Skill dictionaries for Backend & Fullstack profiles
│   └── resume_matcher.py         # Keyword matching & score calculation engine
│
├── exporters/                    # 📊 EXPORT & PERSISTENCE
│   ├── json_exporter.py          # Serializes raw and processed JSONs
│   └── markdown_exporter.py      # Generates Markdown report (relatorio_matches.md)
│
├── facades/                      # 🏛️ ORCHESTRATION FACADE
│   └── job_search_facade.py      # JobSearchMasterFacade (coordinates all domains)
│
├── main.py                       # Minimal entry point (zero business rules)
└── pos_processamento.py          # Standalone post-processing runner
```

---

## Tech Stack & Environment

- **Language**: Python (>= 3.14)
- **Data Validation**: `pydantic` (v2)
- **Package Manager**: `uv`
- **Networking**: `requests`, `httpx`
- **HTML Parsing**: `beautifulsoup4`
- **Concurrency**: `asyncio` (proxy validation) + `ThreadPoolExecutor` (detail fetch)

---

## Workflows & Common Commands

- **Sync Environment**:
  ```bash
  uv sync
  ```

- **Run Complete Pipeline**:
  ```bash
  uv run python -m app.main
  ```

- **Run Standalone Post-Processing**:
  ```bash
  uv run python -m app.pos_processamento
  ```

- **Lint & Code Quality Check**:
  ```bash
  uv run ruff check
  ```
  *(Ou `uv run ruff check --fix` para correções automáticas)*

---

## Code Quality & Best Practices

- **Explicit Variable Naming**:
  - Proibido o uso de variáveis abreviadas, crípticas ou de letra única (ex: `for i, v in enumerate(...)` ou `m_be = ...`).
  - Use sempre nomes descritivos e legíveis no contexto do domínio (ex: `for index, job in enumerate(...)`, `backend_match = job.match_curriculo.backend if job.match_curriculo else None`).
- **HTTP Resilience Policy**:
  - O cliente HTTP compartilhado deve usar retries limitados e backoff controlado para evitar delays artificiais em respostas bloqueadas.
  - Casos de status 401/403/429 devem encerrar rapidamente a série de tentativas em vez de repetir esperas inúteis.
  - A validação de proxy não deve transformar respostas legítimas em falhas de rede nem aumentar o tempo total do job principal.
- **SearXNG Local**:
  - O serviço deve escutar explicitamente em `0.0.0.0` para que a porta publicada pelo Docker seja acessível pelo cliente Python em IPv4.
- **Post-Change Validation Directive**:
  - **Sempre** após realizar modificações no código, deve-se executar `uv run ruff check` (e/ou `uv run ruff check --fix`) para validar e corrigir quaisquer pendências de lint/formatação.

---

## Self-Update Directive
The AI agent MUST automatically update `GEMINI.md` whenever relevant architectural, feature, endpoint, or guideline changes are implemented in the codebase.

