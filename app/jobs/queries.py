from typing import ClassVar


class Nacionais:
    TERMOS_JOBS: ClassVar[list[tuple[str, str]]] = [
        ("Python FastAPI Django PostgreSQL", "Brazil"),
        ("Python Vue React PostgreSQL", "Brazil"),
        ("Desenvolvedor Python Junior", "Brazil"),
    ]


class Gringas:
    JOBS_BE = "(Python OR Django OR FastAPI) AND (PostgreSQL OR MySQL) AND (AWS OR GCP OR Docker) AND (Junior OR 'Entry Level' OR Jr)"
    JOBS_FS = "(Python OR Django OR FastAPI) AND (Vue OR React OR TypeScript) AND (PostgreSQL OR MySQL) AND (Junior OR 'Entry Level' OR Jr)"

    TERMOS_JOBS: ClassVar[list[tuple[str, str]]] = [
        (JOBS_BE, "Remote"),
        (JOBS_FS, "Remote"),
    ]

