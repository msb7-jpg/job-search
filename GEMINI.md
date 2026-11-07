# Gemini Context: job-search

This repository contains a modular Python automation tool designed to search, filter, extract, and post-process tech job listings from LinkedIn, Gupy, and InHire into structured JSON formats (`vagas_processadas.json`, `vagas_ats_processadas.json`), featuring automated resume matching for custom developer profiles (e.g. Backend & Full-Stack with Vue.js and React.js) and generating separate, dated Markdown reports (`relatorio_matches_YYYY-MM-DD.md`, `relatorio_ats_YYYY-MM-DD.md`).

---

## Project Architecture & Design Principles

The codebase is strictly modularized into self-contained domains with single responsibilities, typed Pydantic models, encapsulated facades, and standardized logging.

### Architecture Overview

```text
app/
├── core/
│   ├── config.py                 # Central settings (Settings) with Pydantic (usar_proxy, buscar_ats, relatórios datados, etc.)
│   └── logging.py                # Centralized structured logger setup
│
├── models/                       # Strict Pydantic models & StrEnums
│   ├── enums.py                  # ScopeEnum, PlatformEnum, ItemTypeEnum, SeniorityEnum, WorkModelEnum, MatchLevelEnum, TimeFilterEnum
│   ├── job.py                    # JobItem schema (LinkedIn, Gupy & InHire Jobs)
│   ├── post.py                   # PostItem schema (LinkedIn Feed Posts)
│   ├── match.py                  # ProfileMatch, ResumeMatch schemas (dynamic multi-profile support)
│   └── report.py                 # ScopeContainer, ProcessedDataOutput, AtsReportOutput schemas
│
├── profiles/                     # 👤 PROFILES DOMAIN (Decoupled keywords, rules & queries)
│   ├── base.py                   # Profile and ScoringRule Pydantic models (queries_jobs, queries_posts, queries_ats, termos_cargo_inhire)
│   ├── predefined.py             # Predefined profiles (Backend Python, Full-Stack Python com Vue.js + React.js)
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
│   ├── fetcher.py                # Google Search (googlesearch-python) post scraper, proxy rotator & deduplication
│   ├── runner.py                 # Standalone direct posts search runner (fast mode / query logging)
│   └── facade.py                 # PostsPipelineFacade (accepts custom profiles & direct execution)
│
├── ats/                          # 🏢 ATS DOMAIN (Gupy & InHire Jobs)
│   ├── data/
│   │   └── inhire_tenants.json   # Base com 480+ empresas/tenants InHire mapeadas e validadas
│   ├── gupy_fetcher.py           # Consumo paginado da API pública do portal Gupy com workplaceType=remote e descrição completa
│   ├── inhire_fetcher.py         # Varredura concorrente de tenants InHire e enriquecimento de descrições completas via API
│   ├── inhire_harvester.py       # Coletor Open-Web (Wayback CDX, urlscan.io, Common Crawl) para descoberta de novos tenants
│   ├── runner.py                 # Standalone direct ATS search runner (fast mode / log de queries e resumo)
│   └── facade.py                 # AtsPipelineFacade (orquestração, deduplicação, pré/pós-filtro, matcher e exportação)
│
├── shared/                       # 🛠️ SHARED INFRASTRUCTURE
│   └── http/
│       ├── proxy_record.py       # ProxyRecord dataclass with EWMA latency score, in_flight concurrency & Circuit Breaker
│       ├── proxy_sources.py      # Concurrent multi-source proxy aggregator, scheme sanitizer & semantic payload validator
│       ├── proxy_rotator.py      # RealtimeProxyRotator (Reactive Producer-Consumer, PriorityQueue EWMA, Tier-A Warm Start Cache)
│       └── client.py             # Resilient HTTP wrapper with inline Circuit Breaker feedback, granular timeouts & direct fallback
│
├── matchers/                     # 🎯 RESUME MATCHING & LLM JUDGE ENGINE
│   ├── skills_definitions.py     # Backward-compatible skill re-exports
│   ├── resume_matcher.py         # Dynamic multi-profile keyword matching & score engine
│   └── llm_matcher.py            # Universal OpenAI-Compatible Semantic LLM Judge (Gemini Bridge / vLLM / Ollama) against resume-pt.md
│
├── notifiers/                    # 📱 NOTIFICATIONS DOMAIN
│   └── telegram_notifier.py      # Telegram Bot HTML summary, Top-N job cards with AI analysis, and Markdown file attachments
│
├── exporters/                    # 📊 EXPORT & PERSISTENCE
│   ├── json_exporter.py          # Serializes raw and processed JSONs (LinkedIn and ATS)
│   ├── markdown_exporter.py      # Generates separate, dated Markdown reports (LinkedIn and ATS)
│   └── pdf_exporter.py           # Generates modern, executive print-quality PDFs via Chromium headless (Qualificadas & Rejeitadas)
│
├── facades/                      # 🏛️ ORCHESTRATION FACADE
│   └── job_search_facade.py      # JobSearchMasterFacade (coordinates LinkedIn & ATS pipelines)
│
├── main.py                       # Minimal entry point (zero business rules)
└── pos_processamento.py          # Standalone post-processing runner (supports custom profiles, LinkedIn and ATS)
```

---

## Tech Stack & Environment

- **Language**: Python (>= 3.14)
- **Data Validation**: `pydantic` (v2)
- **Package Manager**: `uv`
- **Networking & Search**: `requests`, `httpx`, `googlesearch-python`
- **HTML Parsing**: `beautifulsoup4`
- **Concurrency & Progress**: `asyncio` (proxy validation), `ThreadPoolExecutor` (detail fetch & tenant scanning), `tqdm` (interactive query and detail fetching progress bars)

---

## Workflows & Common Commands (via Makefile ou uv)

O repositório possui um `Makefile` que unifica e simplifica todos os comandos operacionais (`make help` para listar):

- **Ajuda e Lista de Comandos**:
  ```bash
  make help
  ```

- **Run Complete Pipeline (LinkedIn + ATS + LLM Judge + PDFs + Telegram)**:
  ```bash
  make run
  # ou make all
  # ou uv run python -m app.main
  ```

- **Run Standalone Jobs Search (LinkedIn)**:
  ```bash
  make jobs
  # ou uv run python -m app.jobs.runner
  ```

- **Run Standalone ATS Search (Gupy + InHire)**:
  ```bash
  make ats
  # ou uv run python -m app.ats.runner
  ```

- **Run Standalone Posts Search (LinkedIn)**:
  ```bash
  make posts
  # ou uv run python -m app.posts.runner
  ```

- **Run Standalone Post-Processing & Matching**:
  ```bash
  make pos-process
  # ou uv run python -m app.pos_processamento
  ```

- **Harvest & Validate New InHire Tenants**:
  ```bash
  make harvest
  # ou uv run python -m app.ats.inhire_harvester
  ```

- **Test Suite**:
  ```bash
  make test
  # ou uv run python -m unittest discover tests
  ```

- **Lint & Code Quality Check**:
  ```bash
  make lint
  # ou make format (para correções automáticas)
  ```

- **Sync Dependencies & Clean**:
  ```bash
  make sync
  make clean
  ```

---

## Code Quality & Best Practices

- **Single Source of Truth (SSOT) & Zero Redundant Defaults Principle**:
  - `Settings` é a única fonte da verdade para parâmetros globais e operacionais de execução (concorrência, timeouts, flags de proxy, enriquecimento, recência e filtros).
  - **Filtros de Recência Separados**:
    - `filtro_tempo` para vagas formais no LinkedIn (padrão: 24 horas).
    - `filtro_tempo_posts` para publicações/posts no LinkedIn (padrão: última semana).
    - `filtro_tempo_ats` para vagas Gupy e InHire (padrão: qualquer data aberta/publicada).
  - **Relatórios Separados, Datados e PDFs Executivos**:
    - LinkedIn: `relatorio_matches_YYYY-MM-DD.md` com título contendo a data (`DD/MM/YYYY`).
    - ATS: `relatorio_ats_YYYY-MM-DD.md` com título contendo a data (`DD/MM/YYYY`) e estatísticas dedicadas de Gupy e InHire.
    - **PDF de Qualificadas**: `relatorio_vagas_qualificadas_YYYY-MM-DD.pdf` com design minimalista, cabeçalho limpo (apenas total de vagas e data de emissão), descrição completa/escopo da vaga formatada em destaque, botões de ação diretos ("Candidatar-se"), badges de plataforma/senioridade/scores, tech stack pills e parecer técnico da IA.
    - **PDF & Markdown de Auditoria de Rejeitadas**: `relatorio_vagas_rejeitadas_YYYY-MM-DD.pdf` e `relatorio_vagas_rejeitadas_YYYY-MM-DD.md`, categorizando os descartes por camada (Heurística de Local/Modelo, Senioridade no Título, Empresas Bloqueadas tipo Micro1, Vagas de AI Training/RLHF, Score de Keywords, ou LLM Judge Semântico) com a justificativa exata.
    - **Envio Focado para o Telegram**: Envio exclusivo dos dois relatórios executivos em PDF (Qualificadas e Rejeitadas), sem mensagens avulsas de cards nem arquivos markdown auxiliares.
  - Instâncias de `Profile` são a única fonte da verdade para regras de pontuação de currículo, keywords e listas de queries de busca (incluindo `queries_ats` e `termos_cargo_inhire`).
  - **Proibição de Defaults Redundantes em Cascata**: Métodos e funções internas (fetchers, classificadores, evaluators) não devem declarar valores padrão opcionais redundantes ou divergentes. Parâmetros operacionais devem ser obrigatórios e passados explicitamente a partir do contexto de execução.
- **Profile-Driven Configuration & Full-Stack Symmetrical Support**:
  - O perfil Full-Stack Python dá suporte simétrico a **Vue.js** (Vue 2, Vue 3, Nuxt.js, Pinia) e **React.js** (Next.js, Redux), além de TypeScript, JavaScript, Tailwind CSS e frameworks backend Python (Django, FastAPI, Flask).
- **Interactive Progress Bars & Structured Feedback**:
  - Uso de `tqdm` em tempo real para monitorar o progresso de queries restantes e varredura de empresas (tenants).
- **Detailed Filter & Discard Reporting & 2-Stage Hybrid LLM Judge**:
  - **Camada 1 (Heurística Rápida)**: Descarte imediato de países/cidades incompatíveis (Vietnã, Índia, Filipinas, Leste Europeu local, vagas com Security Clearance americano ou `(m/w/d)` local europeu), senioridade Pleno/Sênior/Lead, empresas indesejadas (Micro1, Invisible, DataAnnotation, Outlier) e vagas voltadas a treinamento/avaliação/anotação de modelos de IA (AI Trainer, RLHF, prompt evaluation).
  - **Camada 2 (LLM Judge Semântico Universal)**: Avaliação semântica via endpoint padrão OpenAI-Compatible (`LLM_BASE_URL`, padrão `http://127.0.0.1:8765/v1` com `gemini-3.8-flash` ou compatível) confrontando cada vaga candidata com o currículo real (`/home/miguelsb/workspace/auto-apply/resume-pt.md`), aprovando exclusivamente vagas de **Desenvolvimento de Software Real (Backend/Full-Stack)**, **Júnior / Entry-Level (máx. 2 anos de XP)** e **100% Remotas viáveis do Brasil** (ou presenciais/híbridas em Recife-PE). Zero dependência de binários locais ou subprocessos de SO.
- **Search Tooling Preference (`rg` over `grep`)**:
  - Sempre utilizar `rg` (`ripgrep`, `/home/linuxbrew/.linuxbrew/bin/rg`) em vez de `grep` para buscas rápidas em arquivos e diretórios no workspace.
- **Explicit Variable Naming**:
  - Proibido o uso de variáveis abreviadas, crípticas ou de letra única (ex: `for index, job in enumerate(...)`, `backend_match = job.match_curriculo.backend if job.match_curriculo else None`).
- **Post-Change Validation Directive**:
  - **Sempre** após realizar modificações no código, deve-se executar `uv run ruff check` (e/ou `uv run ruff check --fix`) para validar e corrigir quaisquer pendências de lint/formatação.

---

## Self-Update Directive
The AI agent MUST automatically update `GEMINI.md` whenever relevant architectural, feature, endpoint, or guideline changes are implemented in the codebase.
