import argparse

from app.core.config import Settings
from app.core.logging import logger
from app.pipeline import export_pdfs_from_db, rejudge_pending_jobs, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-search", description="Pipeline local-first de busca e triagem de vagas.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Executa coleta concorrente, deduplicação SQLite, LLM Judge e PDF.")
    run_parser.add_argument(
        "--providers",
        nargs="+",
        help="Lista opcional de provedores (ex: linkedin gupy inhire ciandt fullstack).",
    )
    run_parser.add_argument("--no-proxy", action="store_true", help="Desativa o pool de proxies nesta execução.")
    run_parser.add_argument("--no-llm", action="store_true", help="Desativa o LLM Judge nesta execução.")
    run_parser.add_argument("--no-pdf", action="store_true", help="Pula a geração de relatórios PDF.")

    subparsers.add_parser("rejudge", help="Reavalia vagas com status PENDING no SQLite sem re-executar scrapers.")
    subparsers.add_parser("export-pdf", help="Regenera os relatórios PDF a partir do SQLite.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = Settings()

    command = args.command or "run"
    if command == "run":
        if getattr(args, "no_proxy", False):
            settings.usar_proxy = False
        if getattr(args, "no_llm", False):
            settings.usar_filtro_llm = False

        logger.info(
            f"Iniciando Job Search (Recência: {settings.filtro_tempo.descricao} [{settings.filtro_tempo.value}] | "
            f"Remoto: {settings.apenas_remoto} | Senioridade: {settings.senioridade_filtro})"
        )
        run_pipeline(
            settings=settings,
            providers_filter=getattr(args, "providers", None),
            skip_pdf=getattr(args, "no_pdf", False),
        )
    elif command == "rejudge":
        rejudge_pending_jobs(settings=settings)
    elif command == "export-pdf":
        export_pdfs_from_db(settings=settings)


if __name__ == "__main__":
    main()
