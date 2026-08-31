# Gemini Context: job-search

This repository contains a modular Python automation tool designed to search, filter, extract, and post-process tech job listings and LinkedIn posts into structured JSON format (`vagas_processadas.json`), featuring automated resume matching for custom developer profiles (e.g. Backend & Full-Stack) and generating formatted Markdown reports (`relatorio_matches.md`).

---

## Project Architecture & Design Principles

The codebase is strictly modularized into self-contained domains with single responsibilities, typed Pydantic models, encapsulated facades, and standardized logging.

### Architecture Overview

```text
app/
├── core/
│   ├── config.py                 # Central settings (Settings) with Pydantic (usar_proxy, enriquecer_detalhes, etc.)
│   └── logging.py                # Centralized structured logger setup
│
├── models/                       # Strict Pydantic models & StrEnums
│   ├── enums.py                  # ScopeEnum, ItemTypeEnum, SeniorityEnum, WorkModelEnum, MatchLevelEnum, TimeFilterEnum
│   ├── job.py                    # JobItem schema (LinkedIn Jobs)
│   ├── post.py                   # PostItem schema (LinkedIn Feed Posts)
│   ├── match.py                  # ProfileMatch, ResumeMatch schemas (dynamic multi-profile support)
│   └── report.py                 # ScopeContainer, ProcessedDataOutput schemas
│
├── profiles/                     # 👤 PROFILES DOMAIN (Decoupled keywords, rules & queries)
│   ├── base.py                   # Profile and ScoringRule Pydantic models
│   ├── predefined.py             # Predefined profiles (Backend Python, Full-Stack Python)
│   └── __init__.py               # Exports Profile, ScoringRule, DEFAULT_PROFILES, etc.
│
├── jobs/                         # 💼 JOBS DOMAIN (Formal LinkedIn Jobs)
│   ├── queries.py                # Default queries for national and international jobs
│   ├── classifiers.py            # Pure heuristics (seniority, work model, pre-filter)
│   ├── fetcher.py                # LinkedIn Guest API search & pagination
│   ├── detail_fetcher.py         # Concurrent aggressive fetch & fast classification fallback
│   ├── runner.py                 # Standalone direct jobs search runner (fast mode / query logging)
│   └── facade.py                 # JobsPipelineFacade (accepts custom profiles & direct execution)
│
├── posts/                        # 💬 POSTS DOMAIN (LinkedIn Feed Posts)
│   ├── queries.py                # Boolean queries for post discovery
│   ├── fetcher.py                # DDGS post scraper, snippet parser & deduplication
│   ├── runner.py                 # Standalone direct posts search runner (fast mode / query logging)
│   └── facade.py                 # PostsPipelineFacade (accepts custom profiles & direct execution)
│
├── shared/                       # 🛠️ SHARED INFRASTRUCTURE
│   └── http/
│       ├── proxy_sources.py      # Multi-source proxy aggregator (Geonode API, GitHub TheSpeedX/monosans, Spys.one, FreeProxyList, ProxyScrape)
│       ├── proxy_rotator.py      # Dynamic Proxy Pool & Rotator supporting ACTIVE_POOL, PRE_FLIGHT, and ADAPTIVE_FAILOVER strategies
│       └── client.py             # Resilient HTTP request wrapper with dynamic failover, proxy eviction, and direct mode fallback
│
├── matchers/                     # 🎯 RESUME MATCHING ENGINE
│   ├── skills_definitions.py     # Backward-compatible skill re-exports
│   └── resume_matcher.py         # Dynamic multi-profile keyword matching & score engine
│
├── exporters/                    # 📊 EXPORT & PERSISTENCE
│   ├── json_exporter.py          # Serializes raw and processed JSONs
│   └── markdown_exporter.py      # Generates Markdown report with dynamic profiles
│
├── facades/                      # 🏛️ ORCHESTRATION FACADE
│   └── job_search_facade.py      # JobSearchMasterFacade (coordinates all domains & profiles)
│
├── main.py                       # Minimal entry point (zero business rules)
└── pos_processamento.py          # Standalone post-processing runner (supports custom profiles)
```

---

## Tech Stack & Environment

- **Language**: Python (>= 3.14)
- **Data Validation**: `pydantic` (v2)
- **Package Manager**: `uv`
- **Networking & Search**: `requests`, `httpx`, `ddgs`
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

- **Run Standalone Jobs Search (Direct & Fast, with Query Logs)**:
  ```bash
  uv run python -m app.jobs.runner
  # ou
  uv run python -m app.jobs.facade
  ```

- **Run Standalone Posts Search (Direct, with Query Logs)**:
  ```bash
  uv run python -m app.posts.runner
  # ou
  uv run python -m app.posts.facade
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

- **Profile-Driven Configuration**:
  - Configurações de palavras-chave, habilidades, regras de pontuação de currículo e queries de busca ficam encapsuladas em instâncias de [`Profile`](app/profiles/base.py).
  - É possível instanciar novos perfis sob demanda e passá-los para as pipelines sem alterar a lógica interna das etapas.
- **Fast Execution & Direct Mode**:
  - O sistema opera por padrão com `usar_proxy = False` e `enriquecer_detalhes = False` em execuções diretas/rápidas, evitando latência de raspagem de proxies ou chamadas profundas para cada ID de vaga quando não requisitado.
- **Explicit Variable Naming**:
  - Proibido o uso de variáveis abreviadas, crípticas ou de letra única (ex: `for i, v in enumerate(...)` ou `m_be = ...`).
  - Use sempre nomes descritivos e legíveis no contexto do domínio (ex: `for index, job in enumerate(...)`, `backend_match = job.match_curriculo.backend if job.match_curriculo else None`).
- **HTTP Resilience Policy**:
  - O cliente HTTP compartilhado deve usar retries limitados e backoff controlado para evitar delays artificiais em respostas bloqueadas.
  - Casos de status 401/403/429 devem encerrar rapidamente a série de tentativas em vez de repetir esperas inúteis.
- **DuckDuckGo Search (DDGS)**:
  - A busca de publicações de feed do LinkedIn é efetuada nativamente via `ddgs`, eliminando containers Docker locais e provendo suporte direto à passagem de proxies ou fallback transparente.
- **Post-Change Validation Directive**:
  - **Sempre** após realizar modificações no código, deve-se executar `uv run ruff check` (e/ou `uv run ruff check --fix`) para validar e corrigir quaisquer pendências de lint/formatação.

---

## Self-Update Directive
The AI agent MUST automatically update `GEMINI.md` whenever relevant architectural, feature, endpoint, or guideline changes are implemented in the codebase.

