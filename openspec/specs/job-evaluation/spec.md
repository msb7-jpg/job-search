# Job Evaluation Specification

## Purpose
Two-layer job filtering and fail-closed LLM evaluation (`app/shared/classifiers.py`, `app/matchers/`, `app/core/user_config.py`).

## Requirements

### Requirement: Dynamic Search Config and Layer 1 Filtering
Layer 1 (`avaliar_pre_filtro_job_bruto()` and `resume_matcher.py`) MUST source queries, `skills_map`, `regras_pontuacao`, filter thresholds, and `blacklisted_companies` from `UserSearchConfig` (`app/data/search_config.json`), never hardcoded personal data.

#### Scenario: Blacklisted company filtering
- **WHEN** a scraped job's company matches `UserSearchConfig.blacklisted_companies`
- **THEN** Layer 1 rejects the job and records the discard layer and reason

### Requirement: Fail-Closed Concurrent Layer 2 LLM Judge
`filtrar_vagas_com_llm_em_lote()` MUST evaluate surviving jobs concurrently (`ThreadPoolExecutor`) and fail closed as `PENDING` if the LLM server is unreachable, times out, or returns invalid JSON.

#### Scenario: LLM unavailable during evaluation
- **WHEN** the OpenAI-compatible LLM endpoint fails or times out
- **THEN** `LlmEvaluation` defaults to `aprovado=False` and persists `llm_status="PENDING"` for later `rejudge` recovery
