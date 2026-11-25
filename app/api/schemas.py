from datetime import datetime

from pydantic import BaseModel, Field


class SiblingJobSchema(BaseModel):
    id: int
    provider: str
    title: str
    company: str
    url: str


class JobEvaluationSchema(BaseModel):
    layer1_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    llm_status: str
    llm_approved: bool
    llm_score: int
    llm_reasoning: str
    discard_layer: str | None = None
    discard_reason: str | None = None


class ApplicationSchema(BaseModel):
    status: str
    notes: str
    applied_at: datetime | None = None
    updated_at: datetime


class JobSummarySchema(BaseModel):
    id: int
    url_hash: str
    canonical_key: str
    provider: str
    title: str
    company: str
    location: str
    work_model: str
    seniority: str
    url: str
    posted_at: str
    first_seen_at: datetime
    last_seen_at: datetime
    evaluation: JobEvaluationSchema | None = None
    application: ApplicationSchema | None = None


class TailoredResumeSummarySchema(BaseModel):
    id: int
    base_profile_version: str
    diff: dict
    cover_letter_md: str
    qa_answers: dict
    pdf_path: str | None = None
    verification_warnings: list[dict]
    created_at: datetime


class JobDetailSchema(JobSummarySchema):
    description_md: str
    siblings: list[SiblingJobSchema] = Field(default_factory=list)
    tailored_resume: TailoredResumeSummarySchema | None = None


class JobListResponse(BaseModel):
    items: list[JobSummarySchema]
    total: int
    limit: int
    offset: int


class UpdateJobStatusRequest(BaseModel):
    status: str
    notes: str | None = None


class TriggerRunRequest(BaseModel):
    providers: list[str] | None = None
    use_proxy: bool = True
    use_llm: bool = True


class ScrapeRunSchema(BaseModel):
    id: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    providers: list[str]
    total_fetched: int
    total_new: int
    total_approved: int
    total_rejected: int
    error_log: str


class RunsOverviewResponse(BaseModel):
    runs: list[ScrapeRunSchema]
    pending_llm_count: int
    available_providers: list[str]
    is_running: bool
    active_run_id: str | None = None


class BlacklistCompanyRequest(BaseModel):
    company_name: str
    ignore_existing: bool = True


class BlacklistCompanyResponse(BaseModel):
    blacklisted_companies: list[str]
    ignored_jobs_count: int
