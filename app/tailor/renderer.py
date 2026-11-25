from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pypdf import PdfReader

from app.core.config import DATA_DIR
from app.exporters.pdf_exporter import render_html_to_pdf
from app.tailor.models import MasterProfile, TailoredDiff, VerificationWarning

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
RESUMES_DIR = DATA_DIR / "resumes"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_tailored_resume_pdf(
    job_id: int,
    profile: MasterProfile,
    diff: TailoredDiff,
    output_dir: Path = RESUMES_DIR,
) -> tuple[Path, int, VerificationWarning | None]:
    """Renderiza o currículo em HTML ATS-safe -> Chromium PDF e valida a regra de 1 página."""
    template = _jinja_env.get_template("resume.html.j2")

    labels = (
        {
            "summary": "Resumo Profissional",
            "experience": "Experiência Profissional",
            "skills": "Competências Técnicas",
            "education": "Formação Acadêmica",
            "languages": "Idiomas",
        }
        if diff.language == "pt"
        else {
            "summary": "Summary",
            "experience": "Experience",
            "skills": "Technical Skills",
            "education": "Education",
            "languages": "Languages",
        }
    )

    rendered_experiences = []
    for exp in profile.experiences:
        selected_bullets: list[str] = []
        for bullet in exp.bullets:
            if bullet.id in diff.bullet_overrides:
                selected_bullets.append(diff.bullet_overrides[bullet.id])
            elif not diff.bullet_overrides:
                selected_bullets.append(bullet.text)
        if selected_bullets:
            rendered_experiences.append(
                {
                    "company": exp.company,
                    "role": exp.role,
                    "location": exp.location,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "bullets": selected_bullets,
                }
            )

    contact_parts = [
        part
        for part in [
            profile.identity.email,
            profile.identity.phone,
            profile.identity.location,
            profile.identity.linkedin_url,
            profile.identity.github_url,
            profile.identity.portfolio_url,
        ]
        if part
    ]

    html_content = template.render(
        language=diff.language,
        profile=profile,
        headline=diff.headline or profile.identity.headline,
        contact_line=" • ".join(contact_parts),
        summary=diff.tailored_summary or profile.default_summary,
        experiences=rendered_experiences,
        skill_groups=diff.selected_skill_groups or profile.skill_groups,
        labels=labels,
    )

    pdf_path = output_dir / f"resume_job_{job_id}.pdf"
    render_html_to_pdf(html_content, pdf_path)

    page_count = 0
    overflow_warning: VerificationWarning | None = None
    if pdf_path.exists() and pdf_path.stat().st_size > 0:
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        if page_count > 1:
            overflow_warning = VerificationWarning(
                bullet_id="page_count",
                warning_type="overflow_pages",
                details=f"Overflow: {page_count} páginas geradas. Remova ou encurte 1-2 bullets para caber em 1 página.",
            )

    return pdf_path, page_count, overflow_warning
