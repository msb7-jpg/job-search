.DEFAULT_GOAL := help
PYTHON := uv run python
RUFF := uv run ruff

.PHONY: help run all jobs ats posts pos-process harvest test test-llm lint format sync clean

help: ## Exibe esta lista de ajuda com todos os comandos disponíveis
	@echo "======================================================================="
	@echo "📌 JOB SEARCH AUTOMATION - COMANDOS MAKEFILE"
	@echo "======================================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

run: ## Executa o Pipeline Completo (LinkedIn + ATS + LLM Judge + PDFs + Telegram)
	$(PYTHON) -m app.main

all: run ## Alias para 'make run'

jobs: ## Executa busca direta e rápida apenas de vagas no LinkedIn
	$(PYTHON) -m app.jobs.runner

ats: ## Executa busca direta e rápida apenas de vagas ATS (Gupy + InHire)
	$(PYTHON) -m app.ats.runner

posts: ## Executa busca de posts no feed do LinkedIn (Google Search)
	$(PYTHON) -m app.posts.runner

pos-process: ## Executa apenas o pós-processamento e LLM Judge sobre dados já baixados
	$(PYTHON) -m app.pos_processamento

harvest: ## Coleta e valida novos tenants do InHire na Open-Web
	$(PYTHON) -m app.ats.inhire_harvester

test: ## Executa a suíte de testes unitários do projeto
	$(PYTHON) -m unittest discover tests

test-llm: ## Testa o avaliador semântico OpenAI Compatible (Gemini Bridge) com vaga de amostra
	$(PYTHON) -m app.matchers.llm_matcher

lint: ## Verifica a qualidade e padrões do código com Ruff
	$(RUFF) check

format: ## Corrige automaticamente problemas de formatação e lint com Ruff
	$(RUFF) check --fix

sync: ## Sincroniza dependências do projeto via uv
	uv sync

clean: ## Remove arquivos temporários e caches (__pycache__, logs antigos, etc.)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
