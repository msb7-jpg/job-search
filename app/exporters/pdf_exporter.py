import html
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from app.core.logging import logger
from app.models.enums import PlatformEnum
from app.models.job import JobItem

# ==============================================================================
# SVGs Vetoriais Embutidos (Renderização 100% garantida no Chromium PDF)
# ==============================================================================

SVG_CALENDAR = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>'
    '<line x1="16" y1="2" x2="16" y2="6"/>'
    '<line x1="8" y1="2" x2="8" y2="6"/>'
    '<line x1="3" y1="10" x2="21" y2="10"/>'
    "</svg>"
)

SVG_LOCATION = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
    '<circle cx="12" cy="10" r="3"/>'
    "</svg>"
)

SVG_REMOTE = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
    '<polyline points="9 22 9 12 15 12 15 22"/>'
    "</svg>"
)

SVG_BUILDING = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="4" y="2" width="16" height="20" rx="2" ry="2"/>'
    '<line x1="9" y1="22" x2="9" y2="12"/>'
    '<line x1="15" y1="22" x2="15" y2="12"/>'
    '<line x1="9" y1="6" x2="9.01" y2="6"/>'
    '<line x1="15" y1="6" x2="15.01" y2="6"/>'
    '<line x1="9" y1="10" x2="9.01" y2="10"/>'
    '<line x1="15" y1="10" x2="15.01" y2="10"/>'
    "</svg>"
)

SVG_BRAIN = (
    '<svg class="pdf-icon pdf-icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24A2.5 2.5 0 0 1 9.5 2Z"/>'
    '<path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24A2.5 2.5 0 0 0 14.5 2Z"/>'
    "</svg>"
)

SVG_TARGET = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/>'
    '<circle cx="12" cy="12" r="6"/>'
    '<circle cx="12" cy="12" r="2"/>'
    "</svg>"
)

SVG_CHECK = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/>'
    '<polyline points="8 12 11 15 16 9"/>'
    "</svg>"
)

SVG_CROSS = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="15" y1="9" x2="9" y2="15"/>'
    '<line x1="9" y1="9" x2="15" y2="15"/>'
    "</svg>"
)

SVG_SHIELD = (
    '<svg class="pdf-icon pdf-icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
    "</svg>"
)

SVG_ROCKET = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>'
    '<path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
    '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>'
    '<path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>'
    "</svg>"
)

SVG_EXTERNAL_LINK = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
    '<polyline points="15 3 21 3 21 9"/>'
    '<line x1="10" y1="14" x2="21" y2="3"/>'
    "</svg>"
)

SVG_CODE = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="16 18 22 12 16 6"/>'
    '<polyline points="8 6 2 12 8 18"/>'
    "</svg>"
)

SVG_LIST = (
    '<svg class="pdf-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="8" y1="6" x2="21" y2="6"/>'
    '<line x1="8" y1="12" x2="21" y2="12"/>'
    '<line x1="8" y1="18" x2="21" y2="18"/>'
    '<circle cx="4" cy="6" r="1.5" fill="currentColor"/>'
    '<circle cx="4" cy="12" r="1.5" fill="currentColor"/>'
    '<circle cx="4" cy="18" r="1.5" fill="currentColor"/>'
    "</svg>"
)


def _formatar_data_hoje(data_str: str | None = None) -> str:
    if data_str:
        return data_str
    return datetime.now().strftime("%d/%m/%Y")


def _obter_cor_plataforma(plataforma: PlatformEnum | str) -> tuple[str, str]:
    """Retorna (cor_fundo, cor_texto) para o badge da plataforma."""
    plat_str = str(plataforma).lower()
    if "linkedin" in plat_str:
        return "#0a66c2", "#ffffff"
    if "gupy" in plat_str:
        return "#7c3aed", "#ffffff"
    if "inhire" in plat_str:
        return "#059669", "#ffffff"
    return "#475569", "#ffffff"


def _renderizar_html_para_pdf(conteudo_html: str, caminho_pdf: Path) -> Path:
    """Renderiza uma string HTML para PDF utilizando o Chromium Headless."""
    caminho_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as temp_html:
        temp_html.write(conteudo_html)
        caminho_temp_html = Path(temp_html.name)

    try:
        comando = [
            "chromium",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={caminho_pdf}",
            str(caminho_temp_html),
        ]
        resultado = subprocess.run(  # noqa: S603
            comando,
            check=True,
            capture_output=True,
            text=True,
            timeout=40,
        )
        if caminho_pdf.exists() and caminho_pdf.stat().st_size > 0:
            logger.info(f"📑 [PDF-EXPORTER] PDF gerado com sucesso em '{caminho_pdf}' ({caminho_pdf.stat().st_size} bytes).")
            return caminho_pdf
        logger.error(f"❌ [PDF-EXPORTER] Falha ao gerar PDF. Saída do Chromium: {resultado.stderr}")
    except Exception as erro:
        logger.error(f"❌ [PDF-EXPORTER] Exceção ao executar Chromium para gerar PDF: {erro}")
    finally:
        if caminho_temp_html.exists():
            caminho_temp_html.unlink()

    return caminho_pdf


def gerar_relatorio_qualificadas_pdf(
    vagas: list[JobItem],
    caminho_pdf: Path,
    data_str: str | None = None,
) -> Path:
    """Gera um PDF estético e moderno para as vagas 100% qualificadas e validadas pela IA."""
    data_formatada = _formatar_data_hoje(data_str)
    total_vagas = len(vagas)

    cards_html: list[str] = []
    for indice, vaga in enumerate(vagas, 1):
        bg_plat, text_plat = _obter_cor_plataforma(vaga.plataforma)
        titulo_esc = html.escape(vaga.titulo)
        empresa_esc = html.escape(vaga.empresa)
        local_esc = html.escape(vaga.localizacao)
        postagem_esc = html.escape(vaga.data_postagem)
        link_esc = html.escape(vaga.link)
        plataforma_esc = html.escape(str(vaga.plataforma))

        score_heuristico = vaga.match_curriculo.score_maximo if vaga.match_curriculo else 0
        avaliacao_llm = vaga.match_curriculo.avaliacao_llm if vaga.match_curriculo else None
        score_llm = avaliacao_llm.score_llm if avaliacao_llm else score_heuristico
        justificativa_llm = (
            html.escape(avaliacao_llm.justificativa)
            if avaliacao_llm and avaliacao_llm.justificativa
            else "Aprovada pelos critérios de match e elegibilidade do currículo."
        )
        nivel_llm = (
            html.escape(avaliacao_llm.nivel_detectado) if avaliacao_llm and avaliacao_llm.nivel_detectado else "Júnior / Entry-Level"
        )

        # Extrair habilidades
        skills: list[str] = []
        if vaga.match_curriculo and vaga.match_curriculo.perfis:
            for perfil in vaga.match_curriculo.perfis.values():
                skills.extend(perfil.habilidades_compativeis)
        skills_unicas = sorted(set(skills))
        pills_html = (
            "".join(f'<span class="skill-pill">{html.escape(skill)}</span>' for skill in skills_unicas)
            or '<span class="skill-pill">Python & Full-Stack</span>'
        )

        # Reconstrução de destaques e descrição completa
        trecho_descricao = (vaga.descricao_completa or vaga.descricao_resumida or "").strip()
        descricao_exibicao = trecho_descricao[:800].rsplit(" ", 1)[0] + "..." if len(trecho_descricao) > 800 else trecho_descricao
        descricao_html = html.escape(descricao_exibicao) if descricao_exibicao else "Descrição detalhada não informada pelo anunciante."

        linhas_resumo = [
            f"<li>{html.escape(linha.strip())}</li>"
            for linha in trecho_descricao.split("\n")
            if len(linha.strip()) > 35
            and any(
                palavra in linha.lower()
                for palavra in ["desenvolver", "atuar", "requisito", "experiência", "conhecimento", "responsab", "tecnolog"]
            )
        ][:3]
        resumo_html = "".join(linhas_resumo)

        secao_destaques = (
            f"""
          <div class="section-subtitle">{SVG_LIST} Destaques e Requisitos Identificados:</div>
          <ul class="job-highlights">
            {resumo_html}
          </ul>
        """
            if resumo_html
            else ""
        )

        card = f"""
        <div class="job-card">
          <div class="job-header">
            <div class="job-header-left">
              <span class="badge-plataforma" style="background-color: {bg_plat}; color: {text_plat};">
                {plataforma_esc}
              </span>
              <span class="badge-tag">{SVG_CALENDAR} {postagem_esc}</span>
              <span class="badge-tag">{SVG_LOCATION} {local_esc}</span>
              <span class="badge-tag">{SVG_REMOTE} 100% Remoto</span>
            </div>
            <div class="job-header-right">
              <span class="badge-score">{SVG_TARGET} Match: {score_heuristico}%</span>
              <span class="badge-ai">{SVG_BRAIN} Score IA: {score_llm}%</span>
            </div>
          </div>

          <h2 class="job-title">{indice}. {titulo_esc}</h2>
          <div class="job-company">{SVG_BUILDING} <strong>{empresa_esc}</strong> • Nível Confirmado: <span class="badge-level">{nivel_llm}</span></div>

          <div class="ai-box">
            <div class="ai-box-title">{SVG_BRAIN} Parecer Técnico da Inteligência Artificial:</div>
            <div class="ai-box-content">{justificativa_llm}</div>
          </div>

          <div class="section-subtitle">{SVG_CODE} Tecnologias & Habilidades Identificadas:</div>
          <div class="skills-container">
            {pills_html}
          </div>

          <div class="section-subtitle">{SVG_LIST} Descrição & Escopo da Oportunidade:</div>
          <div class="job-description-box">
            {descricao_html}
          </div>

          {secao_destaques}

          <div class="job-footer">
            <a href="{link_esc}" class="btn-apply">{SVG_ROCKET} Candidatar-se &rarr;</a>
            <span class="job-link-text">{link_esc}</span>
          </div>
        </div>
        """
        cards_html.append(card)

    corpo_vagas = (
        "\n".join(cards_html)
        if cards_html
        else """
    <div class="job-card empty-card">
      <p>Nenhuma oportunidade qualificada com 100% de aderência na rodada de hoje.</p>
    </div>
    """
    )

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório Executivo de Vagas Qualificadas - {data_formatada}</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 12mm 14mm 14mm 14mm;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 11.5px;
    line-height: 1.45;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .pdf-icon {{
    width: 12px;
    height: 12px;
    display: inline-block;
    vertical-align: -1.5px;
    margin-right: 3px;
    flex-shrink: 0;
  }}
  .pdf-icon-md {{
    width: 14px;
    height: 14px;
    vertical-align: -2px;
    margin-right: 5px;
  }}
  .report-header-clean {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0f172a;
    color: #ffffff;
    padding: 12px 18px;
    border-radius: 8px;
    margin-bottom: 16px;
  }}
  .report-header-clean .header-title {{
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -0.3px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .report-header-clean .header-badge {{
    background: #2563eb;
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 9999px;
  }}
  .report-header-clean .header-date {{
    font-size: 11px;
    color: #94a3b8;
    font-weight: 500;
    display: flex;
    align-items: center;
  }}
  .job-description-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #3b82f6;
    padding: 9px 12px;
    border-radius: 4px;
    color: #334155;
    font-size: 10.5px;
    line-height: 1.5;
    margin-bottom: 12px;
    white-space: pre-line;
  }}

  .job-card {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 16px;
    page-break-inside: avoid;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }}
  .job-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }}
  .job-header-left, .job-header-right {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .badge-plataforma {{
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-tag {{
    font-size: 10px;
    background: #f1f5f9;
    color: #475569;
    padding: 3px 7px;
    border-radius: 4px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
  }}
  .badge-score {{
    font-size: 11px;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
  }}
  .badge-ai {{
    font-size: 11px;
    background: #fef3c7;
    color: #b45309;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
  }}
  .badge-level {{
    background: #dcfce7;
    color: #15803d;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
  }}
  .job-title {{
    font-size: 15px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 4px;
  }}
  .job-company {{
    font-size: 12px;
    color: #334155;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
  }}
  .ai-box {{
    background: #eef2ff;
    border-left: 3px solid #6366f1;
    padding: 10px 12px;
    border-radius: 4px;
    margin-bottom: 12px;
  }}
  .ai-box-title {{
    font-weight: 700;
    color: #4338ca;
    font-size: 11px;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
  }}
  .ai-box-content {{
    color: #1e1b4b;
    font-size: 11px;
    line-height: 1.4;
  }}
  .section-subtitle {{
    font-size: 10.5px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
  }}
  .skills-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-bottom: 12px;
  }}
  .skill-pill {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    color: #0f172a;
    font-size: 10px;
    font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 4px;
  }}
  .job-highlights {{
    list-style: none;
    margin-bottom: 14px;
  }}
  .job-highlights li {{
    position: relative;
    padding-left: 14px;
    color: #334155;
    margin-bottom: 3px;
    font-size: 10.5px;
  }}
  .job-highlights li::before {{
    content: "•";
    position: absolute;
    left: 4px;
    color: #2563eb;
    font-weight: bold;
  }}
  .job-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px dashed #e2e8f0;
    padding-top: 10px;
  }}
  .btn-apply {{
    display: inline-flex;
    align-items: center;
    background: #2563eb;
    color: #ffffff !important;
    text-decoration: none;
    font-weight: 700;
    font-size: 11px;
    padding: 6px 14px;
    border-radius: 6px;
  }}
  .job-link-text {{
    font-size: 9.5px;
    color: #94a3b8;
    max-width: 320px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .empty-card {{
    text-align: center;
    padding: 40px;
    color: #64748b;
  }}
</style>
</head>
<body>

  <div class="report-header-clean">
    <div class="header-title">
      {SVG_TARGET} Vagas Qualificadas <span class="header-badge">{total_vagas}</span>
    </div>
    <div class="header-date">
      {SVG_CALENDAR} Emissão: {data_formatada}
    </div>
  </div>

  {corpo_vagas}

</body>
</html>
"""
    return _renderizar_html_para_pdf(html_completo, caminho_pdf)


def gerar_relatorio_rejeitadas_pdf(
    vagas_rejeitadas: list[JobItem],
    caminho_pdf: Path,
    data_str: str | None = None,
) -> Path:
    """Gera um PDF estético de auditoria com todas as vagas rejeitadas e suas respectivas justificativas detalhadas."""
    data_formatada = _formatar_data_hoje(data_str)
    total_rejeitadas = len(vagas_rejeitadas)

    # Classificar e contar por motivo de rejeição
    total_senioridade = sum(
        1
        for vaga in vagas_rejeitadas
        if "senior" in (vaga.motivo_descarte or "").lower()
        or "pleno" in (vaga.motivo_descarte or "").lower()
        or "ano" in (vaga.motivo_descarte or "").lower()
        or "mentor" in (vaga.motivo_descarte or "").lower()
    )
    total_localizacao = sum(
        1
        for vaga in vagas_rejeitadas
        if "local" in (vaga.motivo_descarte or "").lower()
        or "presencial" in (vaga.motivo_descarte or "").lower()
        or "país" in (vaga.motivo_descarte or "").lower()
        or "portugal" in (vaga.motivo_descarte or "").lower()
        or "vietna" in (vaga.motivo_descarte or "").lower()
        or "eua" in (vaga.motivo_descarte or "").lower()
    )
    total_stack = total_rejeitadas - (total_senioridade + total_localizacao)
    total_stack = max(total_stack, 0)

    itens_html: list[str] = []
    for indice, vaga in enumerate(vagas_rejeitadas, 1):
        bg_plat, text_plat = _obter_cor_plataforma(vaga.plataforma)
        titulo_esc = html.escape(vaga.titulo)
        empresa_esc = html.escape(vaga.empresa)
        local_esc = html.escape(vaga.localizacao)
        link_esc = html.escape(vaga.link)
        plataforma_esc = html.escape(str(vaga.plataforma))
        camada_esc = html.escape(vaga.camada_descarte or "Filtro Heurístico / LLM")
        motivo_esc = html.escape(vaga.motivo_descarte or "Incompatível com os requisitos de experiência ou modalidade.")

        item = f"""
        <div class="reject-card">
          <div class="reject-header">
            <div class="reject-header-left">
              <span class="badge-plataforma" style="background-color: {bg_plat}; color: {text_plat};">
                {plataforma_esc}
              </span>
              <span class="badge-camada">{SVG_SHIELD} {camada_esc}</span>
              <span class="badge-tag">{SVG_LOCATION} {local_esc}</span>
            </div>
            <div class="reject-header-right">
              <span class="badge-status-reject">{SVG_CROSS} Rejeitada</span>
            </div>
          </div>

          <div class="reject-title-row">
            <span class="reject-index">#{indice}</span>
            <h3 class="reject-title">{titulo_esc}</h3>
            <span class="reject-company">({empresa_esc})</span>
          </div>

          <div class="reject-reason-box">
            <strong>Motivo e Diagnóstico do Descarte:</strong>
            <div class="reject-reason-text">{motivo_esc}</div>
          </div>

          <div class="reject-footer">
            <a href="{link_esc}" class="reject-link">{SVG_EXTERNAL_LINK} Auditar vaga original no {plataforma_esc}</a>
          </div>
        </div>
        """
        itens_html.append(item)

    corpo_rejeitadas = (
        "\n".join(itens_html)
        if itens_html
        else """
    <div class="reject-card empty-card">
      <p>Nenhuma vaga descartada registrada nesta rodada.</p>
    </div>
    """
    )

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório de Auditoria de Vagas Rejeitadas - {data_formatada}</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 12mm 14mm 14mm 14mm;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f8fafc;
    color: #0f172a;
    font-size: 11px;
    line-height: 1.45;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .pdf-icon {{
    width: 11px;
    height: 11px;
    display: inline-block;
    vertical-align: -1.5px;
    margin-right: 3px;
    flex-shrink: 0;
  }}
  .pdf-icon-md {{
    width: 13px;
    height: 13px;
    vertical-align: -2px;
    margin-right: 4px;
  }}
  .report-header {{
    background: linear-gradient(135deg, #881337 0%, #4c0519 100%);
    color: #ffffff;
    padding: 18px 22px;
    border-radius: 10px;
    margin-bottom: 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }}
  .report-header-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #9f1239;
    padding-bottom: 10px;
    margin-bottom: 10px;
  }}
  .report-title {{
    font-size: 19px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
  }}
  .report-date {{
    font-size: 12px;
    color: #fecdd3;
    font-weight: 500;
  }}
  .report-meta {{
    display: flex;
    gap: 20px;
    font-size: 11px;
    color: #ffe4e6;
  }}
  .report-meta strong {{
    color: #ffffff;
  }}

  .metrics-strip {{
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
  }}
  .metric-card {{
    flex: 1;
    background: #ffffff;
    border: 1px solid #fecdd3;
    padding: 10px 14px;
    border-radius: 8px;
    text-align: center;
  }}
  .metric-value {{
    font-size: 18px;
    font-weight: 800;
    color: #be123c;
  }}
  .metric-label {{
    font-size: 9.5px;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
  }}

  .reject-card {{
    background: #ffffff;
    border: 1px solid #f1f5f9;
    border-left: 3px solid #e11d48;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    page-break-inside: avoid;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }}
  .reject-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }}
  .reject-header-left, .reject-header-right {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .badge-plataforma {{
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 3px;
    text-transform: uppercase;
  }}
  .badge-camada {{
    font-size: 9.5px;
    background: #f1f5f9;
    color: #334155;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
  }}
  .badge-tag {{
    font-size: 9.5px;
    background: #f8fafc;
    color: #64748b;
    padding: 2px 6px;
    border-radius: 3px;
    display: inline-flex;
    align-items: center;
  }}
  .badge-status-reject {{
    font-size: 9.5px;
    background: #ffe4e6;
    color: #9f1239;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
  }}
  .reject-title-row {{
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin-bottom: 6px;
  }}
  .reject-index {{
    font-size: 11px;
    font-weight: 700;
    color: #94a3b8;
  }}
  .reject-title {{
    font-size: 13px;
    font-weight: 700;
    color: #0f172a;
  }}
  .reject-company {{
    font-size: 11.5px;
    color: #475569;
  }}
  .reject-reason-box {{
    background: #fff1f2;
    border: 1px solid #ffe4e6;
    color: #881337;
    padding: 8px 10px;
    border-radius: 5px;
    font-size: 10.5px;
    line-height: 1.45;
    margin-bottom: 6px;
  }}
  .reject-reason-box strong {{
    color: #be123c;
    display: block;
    margin-bottom: 2px;
  }}
  .reject-reason-text {{
    color: #4c0519;
  }}
  .reject-footer {{
    text-align: right;
  }}
  .reject-link {{
    font-size: 9.5px;
    color: #2563eb;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
  }}
  .empty-card {{
    text-align: center;
    padding: 40px;
    color: #64748b;
  }}
</style>
</head>
<body>

  <div class="report-header">
    <div class="report-header-top">
      <div class="report-title">{SVG_SHIELD} Auditoria de Vagas Rejeitadas & Justificativas</div>
      <div class="report-date">Emissão: {data_formatada}</div>
    </div>
    <div class="report-meta">
      <div>Transparência Total de Filtragem: <strong>Camada 1 (Heurística) + Camada 2 (LLM Judge)</strong></div>
      <div>Alvo: <strong>Júnior (até 2 anos) • 100% Remoto Brasil</strong></div>
    </div>
  </div>

  <div class="metrics-strip">
    <div class="metric-card">
      <div class="metric-value">{total_rejeitadas}</div>
      <div class="metric-label">Total Descartadas</div>
    </div>
    <div class="metric-card">
      <div class="metric-value">{total_senioridade}</div>
      <div class="metric-label">Senioridade &gt; 2 Anos / Pleno / Sênior</div>
    </div>
    <div class="metric-card">
      <div class="metric-value">{total_localizacao}</div>
      <div class="metric-label">Local Incompatível / Presencial</div>
    </div>
    <div class="metric-card">
      <div class="metric-value">{total_stack}</div>
      <div class="metric-label">Stack / Match Insuficiente</div>
    </div>
  </div>

  {corpo_rejeitadas}

</body>
</html>
"""
    return _renderizar_html_para_pdf(html_completo, caminho_pdf)


def gerar_relatorio_rejeitadas_markdown(
    vagas_rejeitadas: list[JobItem],
    caminho_md: Path,
    data_str: str | None = None,
) -> Path:
    """Gera um relatório Markdown com o histórico e justificativas de vagas descartadas."""
    data_formatada = _formatar_data_hoje(data_str)
    linhas = [
        f"# 🛡️ Relatório de Auditoria de Vagas Rejeitadas - {data_formatada}\n",
        "Este documento registra todas as oportunidades filtradas e descartadas pelo pipeline, detalhando a camada "
        "de bloqueio e a justificativa semântica/heurística aplicada para proteger o foco do candidato.\n",
        f"> **Total de Vagas Descartadas:** {len(vagas_rejeitadas)}\n",
        "---\n",
    ]

    for indice, vaga in enumerate(vagas_rejeitadas, 1):
        camada = vaga.camada_descarte or "Filtro Heurístico / LLM"
        motivo = vaga.motivo_descarte or "Incompatível com o perfil desejado."
        linhas.extend(
            [
                f"### {indice}. [{vaga.plataforma}] {vaga.titulo} ({vaga.empresa})",
                f"- **Localização**: {vaga.localizacao} | **Postagem**: {vaga.data_postagem}",
                f"- **Camada de Bloqueio**: `{camada}`",
                f"- **Diagnóstico / Justificativa**: {motivo}",
                f"- 🔗 [Ver vaga no {vaga.plataforma}]({vaga.link})\n",
            ]
        )

    caminho_md.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_md, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

    logger.info(f"📄 [PDF-EXPORTER] Relatório Markdown de rejeitadas gerado em '{caminho_md}'.")
    return caminho_md
