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
│   ├── fetcher.py                # Google Search (googlesearch-python) post scraper, proxy rotator & deduplication
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
- **Networking & Search**: `requests`, `httpx`, `googlesearch-python`
- **HTML Parsing**: `beautifulsoup4`
- **Concurrency & Progress**: `asyncio` (proxy validation), `ThreadPoolExecutor` (detail fetch), `tqdm` (interactive query and detail fetching progress bars)

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

- **Single Source of Truth (SSOT) & Zero Redundant Defaults Principle**:
  - `Settings` é a única fonte da verdade para parâmetros globais e operacionais de execução (concorrência, timeouts, flags de proxy, enriquecimento, recência e filtros).
  - Instâncias de `Profile` são a única fonte da verdade para regras de pontuação de currículo, keywords e listas de queries de busca.
  - **Proibição de Defaults Redundantes em Cascata**: Métodos e funções internas (fetchers, classificadores, evaluators) não devem declarar valores padrão opcionais redundantes ou divergentes (ex.: `apenas_remoto: bool = True`, `usar_proxy: bool = False`, `max_workers = 10`) que mascarem o `Settings` ou o chamador. Parâmetros operacionais devem ser obrigatórios e passados explicitamente a partir do contexto de execução.
- **Profile-Driven Configuration**:
  - Configurações de palavras-chave, habilidades, regras de pontuação de currículo e queries de busca ficam encapsuladas em instâncias de [`Profile`](app/profiles/base.py).
  - É possível instanciar novos perfis sob demanda e passá-los para as pipelines sem alterar a lógica interna das etapas.
- **Interactive Progress Bars & Structured Feedback**:
  - Uso de `tqdm` em tempo real para monitorar o progresso de queries restantes durante a busca inicial e de descrições pendentes durante o `Aggressive Fetching` concorrente com `ThreadPoolExecutor` (`as_completed`), preservando os logs estruturados e a ordem original das vagas.
- **Detailed Filter & Discard Reporting**:
  - Contabilização explícita e logs detalhados de vagas descartadas no pré-filtro inicial (por senioridade incompatível e por modelo de trabalho presencial/híbrido) e no pós-filtro rigoroso após classificação detalhada.
- **Fast Execution & Direct Mode**:
  - O sistema opera por padrão com `usar_proxy = False` e `enriquecer_detalhes = False` em execuções diretas/rápidas, evitando latência de raspagem de proxies ou chamadas profundas para cada ID de vaga quando não requisitado.
- **Explicit Variable Naming**:
  - Proibido o uso de variáveis abreviadas, crípticas ou de letra única (ex: `for i, v in enumerate(...)` ou `m_be = ...`).
  - Use sempre nomes descritivos e legíveis no contexto do domínio (ex: `for index, job in enumerate(...)`, `backend_match = job.match_curriculo.backend if job.match_curriculo else None`).
- **HTTP Resilience & Proxy Policy**:
  - Pool de proxies gerenciado por validação assíncrona inicial em lote (`asyncio` + `httpbin.org/ip`) com rotação circular Round-Robin (FIFO).
  - **Zero retry no mesmo IP**: falhas de conexão ou status `401`/`403`/`429`/`5xx` causam a evicção imediata do proxy da lista ativa (`remover_proxy_invalido(proxy, motivo)`) logando o total de IPs saudáveis restantes no pool e passando imediatamente para o próximo IP.
  - **Recarga Automática Sob Demanda**: caso todos os proxies saudáveis se esgotem durante a execução, o pool recarrega novas fontes e valida um novo lote automaticamente.
- **Standby & Modularidade de Posts**:
  - A busca de posts via Google Search pode ser ligada ou colocada em standby a qualquer momento através da flag `buscar_posts: bool = False` em `Settings`.
- **Match-Based Descending Ordering & Motivational Icons**:
  - Tanto o pós-processamento estruturado em JSON (`vagas_processadas.json`) quanto o relatório gerado em Markdown (`relatorio_matches.md`) ordenam automaticamente todas as oportunidades em cada grupo (Nacional e Internacional, para Jobs e Posts) da maior compatibilidade para a menor (com desempate por total de skills encontradas).
  - O relatório Markdown inclui ícones/emojis motivacionais por nível de match (🔥 para 90-100%, 🚀 para 80-89%, ⚡ para 70-79%, 🎯 para 60-69%, 💡 para 40-59% e ⚪ para <40%) no título das vagas e em cada perfil compatível para destacar e incentivar a priorização de candidaturas.
- **Post-Change Validation Directive**:
  - **Sempre** após realizar modificações no código, deve-se executar `uv run ruff check` (e/ou `uv run ruff check --fix`) para validar e corrigir quaisquer pendências de lint/formatação.


---

## Self-Update Directive
The AI agent MUST automatically update `GEMINI.md` whenever relevant architectural, feature, endpoint, or guideline changes are implemented in the codebase.

