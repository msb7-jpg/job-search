import hashlib
import json
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    desc,
    event,
    func,
    or_,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, joinedload, mapped_column, relationship

from app.models.enums import MatchLevelEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.models.match import LlmEvaluation, ProfileMatch, ResumeMatch


def _utcnow() -> datetime:
    return datetime.now(UTC)


def compute_url_hash(url: str) -> str:
    """Normaliza a URL removendo tracking params e gera hash determinístico de 16 hex chars."""
    raw = (url or "").strip()
    if not raw:
        return hashlib.sha256(b"").hexdigest()[:16]

    parsed = urllib.parse.urlsplit(raw)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    filtered_pairs = [(key, value) for key, value in query_pairs if not key.lower().startswith(("utm_", "trk", "refid", "trackingid"))]
    normalized = urllib.parse.urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            urllib.parse.urlencode(sorted(filtered_pairs)),
            "",
        )
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def compute_canonical_key(company: str, title: str, work_model: str) -> str:
    """Chave canônica não-única para agrupar a mesma vaga encontrada em múltiplos provedores."""
    raw = f"{(company or '').strip().lower()}|{(title or '').strip().lower()}|{(work_model or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class Base(DeclarativeBase):
    pass


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url_hash: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    canonical_key: Mapped[str] = mapped_column(String(16), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    work_model: Mapped[str] = mapped_column(String(64))
    seniority: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(Text)
    description_md: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[str] = mapped_column(String(64), default="Recente")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    evaluation: Mapped["JobEvaluationRow | None"] = relationship(
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    application: Mapped["ApplicationRow | None"] = relationship(
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )


class JobEvaluationRow(Base):
    __tablename__ = "job_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True)
    layer1_score: Mapped[int] = mapped_column(Integer, default=0)
    matched_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    missing_skills_json: Mapped[str] = mapped_column(Text, default="[]")
    llm_status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    llm_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_score: Mapped[int] = mapped_column(Integer, default=0)
    llm_reasoning: Mapped[str] = mapped_column(Text, default="")
    discard_layer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    discard_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    job: Mapped[JobRow] = relationship(back_populates="evaluation")


class ApplicationRow(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    job: Mapped[JobRow] = relationship(back_populates="application")


class TailoredResumeRow(Base):
    __tablename__ = "tailored_resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    base_profile_version: Mapped[str] = mapped_column(String(64), default="v1")
    diff_json: Mapped[str] = mapped_column(Text, default="{}")
    cover_letter_md: Mapped[str] = mapped_column(Text, default="")
    qa_answers_json: Mapped[str] = mapped_column(Text, default="{}")
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ScrapeRunRow(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING")
    providers_json: Mapped[str] = mapped_column(Text, default="[]")
    total_fetched: Mapped[int] = mapped_column(Integer, default=0)
    total_new: Mapped[int] = mapped_column(Integer, default=0)
    total_approved: Mapped[int] = mapped_column(Integer, default=0)
    total_rejected: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str] = mapped_column(Text, default="")


def create_db_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", future=True)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    return engine


def init_db(db_path: Path) -> Engine:
    engine = create_db_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def upsert_scraped_jobs(
    session: Session,
    items: list[JobItem],
) -> tuple[list[tuple[JobRow, JobItem]], list[JobRow]]:
    """Persiste vagas coletadas evitando duplicatas entre execuções.

    Retorna (pendentes_ou_novas, ja_avaliadas).
    """
    now = _utcnow()
    to_evaluate: list[tuple[JobRow, JobItem]] = []
    already_evaluated: list[JobRow] = []

    for item in items:
        url_hash = compute_url_hash(item.link or item.job_id)
        existing = session.scalar(select(JobRow).where(JobRow.url_hash == url_hash))

        if existing is not None:
            existing.last_seen_at = now
            if item.descricao_completa and len(item.descricao_completa) > len(existing.description_md or ""):
                existing.description_md = item.descricao_completa

            evaluation = existing.evaluation
            if evaluation is not None and evaluation.llm_status in ("APPROVED", "REJECTED", "SKIPPED"):
                already_evaluated.append(existing)
            else:
                to_evaluate.append((existing, item))
            continue

        row = JobRow(
            url_hash=url_hash,
            canonical_key=compute_canonical_key(item.empresa, item.titulo, item.modelo_trabalho.value),
            external_id=item.job_id,
            provider=item.provider,
            title=item.titulo,
            company=item.empresa,
            location=item.localizacao,
            work_model=item.modelo_trabalho.value,
            seniority=item.senioridade.value,
            url=item.link,
            description_md=item.descricao_completa or item.descricao_resumida or "",
            posted_at=item.data_postagem,
            first_seen_at=now,
            last_seen_at=now,
        )
        row.application = ApplicationRow(status="NEW", updated_at=now)
        session.add(row)
        session.flush()
        to_evaluate.append((row, item))

    session.commit()
    return to_evaluate, already_evaluated


def save_evaluation(
    session: Session,
    job_row: JobRow,
    item: JobItem,
    llm_status: str,
) -> None:
    """Salva ou atualiza o resultado de avaliação (Camada 1 + Camada 2 LLM) de uma vaga."""
    job_row.seniority = item.senioridade.value
    job_row.work_model = item.modelo_trabalho.value

    perfil = item.match_curriculo.perfil if item.match_curriculo else None
    avaliacao_llm = item.match_curriculo.avaliacao_llm if item.match_curriculo else None

    layer1_score = perfil.score_porcentagem if perfil else 0
    matched_skills = perfil.habilidades_compativeis if perfil else []
    llm_approved = bool(avaliacao_llm.aprovado) if avaliacao_llm else (llm_status == "APPROVED")
    llm_score = avaliacao_llm.score_llm if avaliacao_llm else 0
    llm_reasoning = avaliacao_llm.justificativa if avaliacao_llm else (item.motivo_descarte or "")

    existing_eval = job_row.evaluation
    if existing_eval is None:
        existing_eval = JobEvaluationRow(job_id=job_row.id)
        session.add(existing_eval)

    existing_eval.layer1_score = layer1_score
    existing_eval.matched_skills_json = json.dumps(matched_skills, ensure_ascii=False)
    existing_eval.missing_skills_json = "[]"
    existing_eval.llm_status = llm_status
    existing_eval.llm_approved = llm_approved
    existing_eval.llm_score = llm_score
    existing_eval.llm_reasoning = llm_reasoning
    existing_eval.discard_layer = item.camada_descarte
    existing_eval.discard_reason = item.motivo_descarte
    existing_eval.evaluated_at = _utcnow()


def row_to_job_item(row: JobRow) -> JobItem:
    """Converte um JobRow + JobEvaluationRow do SQLite de volta para JobItem (compatível com pdf_exporter)."""
    try:
        seniority = SeniorityEnum(row.seniority)
    except ValueError:
        seniority = SeniorityEnum.NAO_ESPECIFICADO

    try:
        work_model = WorkModelEnum(row.work_model)
    except ValueError:
        work_model = WorkModelEnum.NAO_ESPECIFICADO

    evaluation = row.evaluation
    resume_match: ResumeMatch | None = None
    discard_layer: str | None = None
    discard_reason: str | None = None

    if evaluation is not None:
        skills = json.loads(evaluation.matched_skills_json or "[]")
        score = evaluation.layer1_score
        if score >= 85:
            nivel = MatchLevelEnum.EXCELENTE
        elif score >= 70:
            nivel = MatchLevelEnum.ALTO
        elif score >= 50:
            nivel = MatchLevelEnum.MEDIO
        else:
            nivel = MatchLevelEnum.BAIXO

        profile_match = ProfileMatch(
            score_porcentagem=score,
            nivel=nivel,
            habilidades_compativeis=skills,
            total_habilidades_encontradas=len(skills),
        )
        llm_eval = None
        if evaluation.llm_status in ("APPROVED", "REJECTED"):
            llm_eval = LlmEvaluation(
                aprovado=evaluation.llm_approved,
                score_llm=evaluation.llm_score,
                justificativa=evaluation.llm_reasoning,
                status=evaluation.llm_status,
            )
        resume_match = ResumeMatch(perfil=profile_match, avaliacao_llm=llm_eval)
        discard_layer = evaluation.discard_layer
        discard_reason = evaluation.discard_reason

    return JobItem(
        job_id=row.external_id,
        provider=row.provider,
        titulo=row.title,
        empresa=row.company,
        localizacao=row.location,
        data_postagem=row.posted_at,
        senioridade=seniority,
        modelo_trabalho=work_model,
        link=row.url,
        descricao_resumida=row.description_md[:300] if row.description_md else "",
        descricao_completa=row.description_md or "",
        match_curriculo=resume_match,
        camada_descarte=discard_layer,
        motivo_descarte=discard_reason,
    )


def get_pending_llm_jobs(session: Session) -> list[tuple[JobRow, JobItem]]:
    """Retorna todas as vagas com avaliação LLM pendente para reprocessamento (`rejudge`)."""
    stmt = select(JobRow).join(JobEvaluationRow, JobEvaluationRow.job_id == JobRow.id).where(JobEvaluationRow.llm_status == "PENDING")
    rows = list(session.scalars(stmt))
    return [(row, row_to_job_item(row)) for row in rows]


def get_jobs_for_pdf(session: Session) -> tuple[list[JobItem], list[JobItem]]:
    """Retorna (qualificadas, rejeitadas) ordenadas por score para geração dos PDFs."""
    rows = list(session.scalars(select(JobRow).join(JobEvaluationRow)))
    qualified: list[JobItem] = []
    rejected: list[JobItem] = []

    for row in rows:
        item = row_to_job_item(row)
        evaluation = row.evaluation
        if evaluation and evaluation.llm_status == "APPROVED" and not item.camada_descarte:
            qualified.append(item)
        elif evaluation and (evaluation.llm_status in ("REJECTED", "SKIPPED") or item.camada_descarte):
            rejected.append(item)

    qualified.sort(
        key=lambda j: (
            j.match_curriculo.score_maximo if j.match_curriculo else 0,
            j.match_curriculo.avaliacao_llm.score_llm if (j.match_curriculo and j.match_curriculo.avaliacao_llm) else 0,
        ),
        reverse=True,
    )
    return qualified, rejected


VALID_APPLICATION_STATUSES = frozenset(
    {
        "NEW",
        "SAVED",
        "TAILORING",
        "READY_TO_APPLY",
        "APPLIED",
        "INTERVIEWING",
        "OFFER",
        "REJECTED",
        "IGNORED",
    }
)


def list_jobs(
    session: Session,
    *,
    status: str | None = None,
    llm_status: str | None = None,
    provider: str | None = None,
    min_score: int | None = None,
    discard_layer: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[JobRow], int]:
    """Consulta paginada e filtrada de vagas para a API do Dashboard."""
    base_stmt = (
        select(JobRow)
        .outerjoin(JobEvaluationRow, JobEvaluationRow.job_id == JobRow.id)
        .outerjoin(ApplicationRow, ApplicationRow.job_id == JobRow.id)
    )

    if status:
        statuses = [item.strip().upper() for item in status.split(",") if item.strip()]
        if statuses:
            base_stmt = base_stmt.where(ApplicationRow.status.in_(statuses))

    if llm_status:
        llm_statuses = [item.strip().upper() for item in llm_status.split(",") if item.strip()]
        if llm_statuses:
            base_stmt = base_stmt.where(JobEvaluationRow.llm_status.in_(llm_statuses))

    if provider:
        base_stmt = base_stmt.where(JobRow.provider == provider.strip())

    if min_score is not None:
        base_stmt = base_stmt.where(
            func.max(func.coalesce(JobEvaluationRow.llm_score, 0), func.coalesce(JobEvaluationRow.layer1_score, 0)) >= min_score
        )

    if discard_layer:
        base_stmt = base_stmt.where(JobEvaluationRow.discard_layer.ilike(f"%{discard_layer.strip()}%"))

    if search:
        termo = f"%{search.strip()}%"
        base_stmt = base_stmt.where(
            or_(
                JobRow.title.ilike(termo),
                JobRow.company.ilike(termo),
                JobRow.location.ilike(termo),
                JobRow.description_md.ilike(termo),
            )
        )

    total = session.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    ordered_stmt = (
        base_stmt.options(joinedload(JobRow.evaluation), joinedload(JobRow.application))
        .order_by(
            desc(func.coalesce(JobEvaluationRow.llm_score, 0)),
            desc(func.coalesce(JobEvaluationRow.layer1_score, 0)),
            desc(JobRow.last_seen_at),
        )
        .offset(offset)
        .limit(limit)
    )
    rows = list(session.scalars(ordered_stmt).unique())
    return rows, int(total)


def get_job_detail(session: Session, job_id: int) -> tuple[JobRow | None, list[JobRow]]:
    """Retorna uma vaga com evaluation/application e suas duplicatas cross-provider (mesma canonical_key)."""
    stmt = select(JobRow).options(joinedload(JobRow.evaluation), joinedload(JobRow.application)).where(JobRow.id == job_id)
    row = session.scalar(stmt)
    if row is None:
        return None, []

    siblings_stmt = select(JobRow).where(JobRow.canonical_key == row.canonical_key, JobRow.id != row.id).order_by(desc(JobRow.last_seen_at))
    siblings = list(session.scalars(siblings_stmt))
    return row, siblings


class InvalidApplicationStatusError(ValueError):
    def __init__(self, status: str) -> None:
        super().__init__(f"Status inválido: {status}")


def update_application_status(
    session: Session,
    job_id: int,
    status: str,
    notes: str | None = None,
) -> ApplicationRow | None:
    """Atualiza o status de candidatura (Kanban / Triage / Rescue) e notas."""
    clean_status = status.strip().upper()
    if clean_status not in VALID_APPLICATION_STATUSES:
        raise InvalidApplicationStatusError(status)

    job_row = session.get(JobRow, job_id)
    if job_row is None:
        return None

    now = _utcnow()
    app_row = job_row.application
    if app_row is None:
        app_row = ApplicationRow(job_id=job_row.id, status=clean_status, updated_at=now)
        session.add(app_row)
    else:
        app_row.status = clean_status
        app_row.updated_at = now

    if clean_status == "APPLIED" and app_row.applied_at is None:
        app_row.applied_at = now

    if notes is not None:
        app_row.notes = notes

    session.commit()
    session.refresh(app_row)
    return app_row


def ignore_jobs_by_company(session: Session, company_name: str) -> int:
    """Marca como IGNORED vagas NEW/SAVED da empresa recém-adicionada à blacklist."""
    clean = company_name.strip().lower()
    if not clean:
        return 0

    stmt = (
        select(JobRow)
        .join(ApplicationRow, ApplicationRow.job_id == JobRow.id)
        .where(
            func.lower(JobRow.company).contains(clean),
            ApplicationRow.status.in_(("NEW", "SAVED")),
        )
    )
    rows = list(session.scalars(stmt))
    now = _utcnow()
    for row in rows:
        if row.application is not None:
            row.application.status = "IGNORED"
            row.application.updated_at = now
    session.commit()
    return len(rows)


def list_scrape_runs(session: Session, limit: int = 20) -> list[ScrapeRunRow]:
    """Lista execuções recentes do pipeline ordenadas da mais nova para a mais antiga."""
    stmt = select(ScrapeRunRow).order_by(desc(ScrapeRunRow.id)).limit(limit)
    return list(session.scalars(stmt))


def count_pending_llm_jobs(session: Session) -> int:
    """Conta quantas vagas estão aguardando avaliação LLM (PENDING)."""
    stmt = select(func.count(JobEvaluationRow.id)).where(JobEvaluationRow.llm_status == "PENDING")
    return int(session.scalar(stmt) or 0)


def get_latest_tailored_resume(session: Session, job_id: int) -> TailoredResumeRow | None:
    """Retorna o currículo adaptado mais recente para uma vaga, se existir."""
    stmt = select(TailoredResumeRow).where(TailoredResumeRow.job_id == job_id).order_by(desc(TailoredResumeRow.id)).limit(1)
    return session.scalar(stmt)
