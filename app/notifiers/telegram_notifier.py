from datetime import datetime
from pathlib import Path

import requests

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.models.report import AtsReportOutput, ProcessedDataOutput


class TelegramNotifier:
    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
        settings: Settings = default_settings,
    ) -> None:
        self.settings = settings
        self.token = token or self.settings.telegram_bot_token
        self.chat_id = chat_id or self.settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    def _esta_habilitado(self) -> bool:
        if not self.settings.enviar_telegram:
            logger.info("📱 [TELEGRAM] Envio desabilitado (enviar_telegram=False).")
            return False
        if not self.token or not self.chat_id:
            logger.warning("⚠️ [TELEGRAM] Token ou Chat ID não configurados no ambiente.")
            return False
        return True

    def enviar_mensagem(self, texto_html: str) -> bool:
        if not self._esta_habilitado():
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            resposta = requests.post(url, json=payload, timeout=self.settings.http_timeout)
            if resposta.status_code == 200:
                logger.info("📱 [TELEGRAM] Mensagem enviada com sucesso!")
                return True
            logger.error(f"❌ [TELEGRAM] Erro ao enviar mensagem (Status {resposta.status_code}): {resposta.text}")
        except Exception as erro:
            logger.error(f"❌ [TELEGRAM] Exceção ao enviar mensagem: {erro}")
        return False

    def enviar_documento(self, caminho_arquivo: Path, legenda: str = "") -> bool:
        if not self._esta_habilitado() or not caminho_arquivo.exists():
            return False

        url = f"{self.base_url}/sendDocument"
        try:
            with open(caminho_arquivo, "rb") as arquivo:
                arquivos = {"document": arquivo}
                dados = {
                    "chat_id": self.chat_id,
                    "caption": legenda,
                    "parse_mode": "HTML",
                }
                resposta = requests.post(
                    url,
                    data=dados,
                    files=arquivos,
                    timeout=max(self.settings.http_timeout, 30),
                )
                if resposta.status_code == 200:
                    logger.info(f"📄 [TELEGRAM] Arquivo '{caminho_arquivo.name}' enviado com sucesso!")
                    return True
                logger.error(f"❌ [TELEGRAM] Erro ao enviar documento (Status {resposta.status_code}): {resposta.text}")
        except Exception as erro:
            logger.error(f"❌ [TELEGRAM] Exceção ao enviar documento: {erro}")
        return False

    def enviar_relatorio_completo(
        self,
        output_ats: AtsReportOutput | None = None,
        output_linkedin: ProcessedDataOutput | None = None,
        top_n: int = 10,
    ) -> None:
        if not self._esta_habilitado():
            return

        data_hoje = datetime.now().strftime("%d/%m/%Y")
        total_ats = output_ats.total_aprovados if output_ats else 0
        total_gupy = output_ats.total_gupy if output_ats else 0
        total_inhire = output_ats.total_inhire if output_ats else 0
        total_linkedin = output_linkedin.total_aprovados if output_linkedin else 0
        total_geral = total_ats + total_linkedin

        # 1. Enviar exclusivamente o Relatório PDF de Vagas Qualificadas
        if self.settings.output_pdf_report.exists():
            legenda_qualificadas = (
                f"🎯 <b>Vagas Qualificadas ({data_hoje})</b>\n"
                f"✨ Total: <b>{total_geral} vagas aprovadas</b> "
                f"(Gupy: {total_gupy}, InHire: {total_inhire}, LinkedIn: {total_linkedin})"
            )
            self.enviar_documento(
                self.settings.output_pdf_report,
                legenda=legenda_qualificadas,
            )

        # 2. Enviar exclusivamente o Relatório PDF de Vagas Rejeitadas (Auditoria)
        if self.settings.output_rejeitadas_pdf_report.exists():
            total_rejeitadas = (output_linkedin.total_rejeitados if output_linkedin else 0) + (
                output_ats.total_rejeitados if output_ats else 0
            )
            legenda_rejeitadas = (
                f"🛡️ <b>Auditoria de Vagas Rejeitadas ({data_hoje})</b>\nTotal de descartes documentados: <b>{total_rejeitadas} vagas</b>"
            )
            self.enviar_documento(
                self.settings.output_rejeitadas_pdf_report,
                legenda=legenda_rejeitadas,
            )
