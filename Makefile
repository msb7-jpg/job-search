.DEFAULT_GOAL := help
PYTHON := uv run python
RUFF := uv run ruff

.PHONY: help run all rejudge export-pdf harvest api web build-web serve gen-api-types check test test-llm lint format sync clean

help: ## Exibe esta lista de ajuda com todos os comandos disponíveis
	@echo "======================================================================="
	@echo "📌 JOB SEARCH AUTOMATION - COMANDOS MAKEFILE"
	@echo "======================================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

run: ## Executa o Pipeline Unificado (Provedores -> SQLite -> LLM Judge -> PDFs)
	$(PYTHON) -m app.main run

all: run ## Alias para 'make run'

rejudge: ## Reavalia vagas com status PENDING no SQLite sem re-executar scrapers
	$(PYTHON) -m app.main rejudge

export-pdf: ## Regenera os relatórios PDF a partir do SQLite
	$(PYTHON) -m app.main export-pdf

harvest: ## Coleta e valida novos tenants do InHire na Open-Web
	$(PYTHON) -m app.providers.inhire.harvester

api: ## Inicia o servidor FastAPI (porta 8000) com reload
	uv run uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

web: ## Inicia o dashboard React/Vite em modo desenvolvimento (porta 5173)
	bun run --cwd web dev

build-web: ## Gera o bundle de produção do frontend em web/dist
	bun run --cwd web build

serve: build-web ## Compila o frontend e serve tudo via FastAPI na porta 8000
	uv run uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000

gen-api-types: ## Gera tipos TypeScript em web/src/api/openapi.d.ts a partir do FastAPI OpenAPI
	$(PYTHON) -c "import json; from app.api.main import app; print(json.dumps(app.openapi()))" | bunx --cwd web openapi-typescript /dev/stdin -o src/api/openapi.d.ts

check: ## Executa todos os gates mecânicos (ruff, hygiene AST, pyright, import-linter, pytest, tsc, eslint, fallow)
	$(RUFF) format --check app proxy_pool tests scripts
	$(RUFF) check app proxy_pool tests scripts
	$(PYTHON) scripts/check_python_hygiene.py
	uv run pyright
	uv run lint-imports
	uv run pytest -q
	bun run --cwd web typecheck
	bun run --cwd web lint
	bun run --cwd web analyze

test: ## Executa a suíte de testes unitários do projeto
	$(PYTHON) -m unittest discover tests

test-llm: ## Testa o avaliador semântico OpenAI Compatible com vaga de amostra
	$(PYTHON) -m app.matchers.llm_smoke

lint: ## Verifica a qualidade e padrões do código com Ruff
	$(RUFF) check

format: ## Corrige automaticamente problemas de formatação e lint com Ruff
	$(RUFF) check --fix

sync: ## Sincroniza dependências do projeto via uv
	uv sync

clean: ## Remove arquivos temporários e caches (__pycache__, etc.)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
