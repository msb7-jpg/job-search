from tqdm import tqdm

from app.ats.gupy_fetcher import buscar_vagas_gupy_por_query
from app.ats.inhire_fetcher import buscar_vagas_inhire
from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.exporters.json_exporter import salvar_dados_brutos_json, salvar_dados_processados_json
from app.exporters.markdown_exporter import gerar_relatorio_ats_markdown
from app.jobs.classifiers import (
    avaliar_pre_filtro_job_bruto,
    classificar_modelo_trabalho,
    classificar_senioridade,
)
from app.matchers.llm_matcher import filtrar_vagas_com_llm_em_lote
from app.matchers.resume_matcher import (
    avaliar_compatibilidade,
    gerar_diagnostico_descarte_keywords,
)
from app.models.enums import PlatformEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.models.report import AtsReportOutput
from app.notifiers.telegram_notifier import TelegramNotifier
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


class AtsPipelineFacade:
    def __init__(
        self,
        settings: Settings = default_settings,
        profiles: list[Profile] = DEFAULT_PROFILES,
    ) -> None:
        self.settings = settings
        self.profiles = profiles

    def _obter_queries_gupy(self) -> list[str]:
        queries_vistas: set[str] = set()
        queries_ordenadas: list[str] = []
        for perfil in self.profiles:
            for query in perfil.queries_ats:
                query_limpa = query.strip()
                if query_limpa and query_limpa.lower() not in queries_vistas:
                    queries_vistas.add(query_limpa.lower())
                    queries_ordenadas.append(query_limpa)
        return queries_ordenadas

    def _obter_termos_inhire(self) -> list[str]:
        termos_vistos: set[str] = set()
        termos_ordenados: list[str] = []
        for perfil in self.profiles:
            for termo in perfil.termos_cargo_inhire:
                termo_limpo = termo.strip().lower()
                if termo_limpo and termo_limpo not in termos_vistos:
                    termos_vistos.add(termo_limpo)
                    termos_ordenados.append(termo_limpo)
        return termos_ordenados

    def executar_extracao(self) -> list[JobItem]:
        logger.info("🏢 [ATS-PIPELINE] [FASE 1/3] Extraindo vagas das plataformas Gupy e InHire...")
        queries_gupy = self._obter_queries_gupy()
        termos_inhire = self._obter_termos_inhire()

        # 1. Coleta na Gupy
        vagas_gupy: list[JobItem] = []
        logger.info(f"🟣 [GUPY] Executando busca em {len(queries_gupy)} queries no portal Gupy...")
        with tqdm(total=len(queries_gupy), desc="🟣 [GUPY] Buscando Queries", unit="query") as barra_gupy:
            for query in queries_gupy:
                encontradas = buscar_vagas_gupy_por_query(
                    termo_busca=query,
                    filtro_tempo=self.settings.filtro_tempo_ats,
                    apenas_remoto=self.settings.apenas_remoto,
                    max_paginas=self.settings.max_paginas_gupy,
                    timeout=self.settings.http_timeout,
                )
                logger.info(f"🟣 [GUPY] Query '{query}' -> {len(encontradas)} vagas encontradas")
                vagas_gupy.extend(encontradas)
                barra_gupy.update(1)

        # 2. Coleta na InHire
        vagas_inhire = buscar_vagas_inhire(
            caminho_tenants=self.settings.inhire_tenants_file,
            termos_cargo_inhire=termos_inhire,
            filtro_tempo=self.settings.filtro_tempo_ats,
            apenas_remoto=self.settings.apenas_remoto,
            senioridade_filtro=self.settings.senioridade_filtro,
            enriquecer_detalhes=self.settings.enriquecer_detalhes_inhire,
            max_workers=self.settings.max_workers_ats,
            timeout=self.settings.http_timeout,
        )

        # 3. Deduplicação por Link
        todas_brutas = vagas_gupy + vagas_inhire
        vagas_unicas_dict: dict[str, JobItem] = {}
        for vaga in todas_brutas:
            if vaga.link:
                vagas_unicas_dict[vaga.link] = vaga
            else:
                vagas_unicas_dict[vaga.job_id] = vaga

        vagas_unicas = list(vagas_unicas_dict.values())
        logger.info(
            f"🏢 [ATS-PIPELINE] Vagas brutas coletadas: {len(todas_brutas)} "
            f"(Gupy: {len(vagas_gupy)}, InHire: {len(vagas_inhire)}, Únicas após dedup: {len(vagas_unicas)})"
        )

        # 4. Salvar JSON Bruto de ATS
        dados_brutos = {
            "plataformas": ["Gupy", "InHire"],
            "filtro_tempo": self.settings.filtro_tempo_ats,
            "apenas_remoto": self.settings.apenas_remoto,
            "senioridade_filtrada": self.settings.senioridade_filtro,
            "total_extraido": len(vagas_unicas),
            "vagas": [vaga.model_dump() for vaga in vagas_unicas],
        }
        salvar_dados_brutos_json(dados_brutos, self.settings.output_ats_raw_json)

        return vagas_unicas

    def executar_pos_processamento(self, vagas_brutas: list[JobItem]) -> AtsReportOutput:
        logger.info("🎯 [ATS-PIPELINE] [FASE 2/3] Avaliando compatibilidade de currículo (Matcher)...")
        threshold = self.settings.threshold_minimo_match
        vagas_aprovadas: list[JobItem] = []
        vagas_rejeitadas: list[JobItem] = []

        descartadas_pre = 0
        descartadas_pos = 0

        for vaga in vagas_brutas:
            # Pré-filtro
            aprovado_pre, motivo_pre = avaliar_pre_filtro_job_bruto(
                titulo=vaga.titulo,
                localizacao=vaga.localizacao,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                empresa=vaga.empresa,
                descricao=vaga.descricao_completa or vaga.descricao_resumida,
            )
            if not aprovado_pre:
                vaga.camada_descarte = "Camada 1 - Pré-Filtro Heurístico"
                vaga.motivo_descarte = f"Descarte no pré-filtro inicial: {motivo_pre}."
                vagas_rejeitadas.append(vaga)
                descartadas_pre += 1
                continue

            # Reclassificação enriquecida com base na descrição completa
            texto_descricao = vaga.descricao_completa or vaga.descricao_resumida
            if texto_descricao:
                vaga.senioridade = classificar_senioridade(
                    titulo=vaga.titulo,
                    descricao=texto_descricao,
                    padrao_junior=False,
                )
                vaga.modelo_trabalho = classificar_modelo_trabalho(
                    titulo=vaga.titulo,
                    localizacao=vaga.localizacao,
                    descricao=texto_descricao,
                    padrao_remoto=(vaga.modelo_trabalho == WorkModelEnum.REMOTO),
                )

            # Pós-filtro (validação rigorosa de senioridade incompatível)
            if self.settings.senioridade_filtro == "JUNIOR" and vaga.senioridade in (
                SeniorityEnum.SENIOR,
                SeniorityEnum.PLENO,
            ):
                vaga.camada_descarte = "Camada 1 - Heurística de Senioridade"
                vaga.motivo_descarte = f"Senioridade classificada como {vaga.senioridade.value} (excede o limite de Júnior/Entry-Level)."
                vagas_rejeitadas.append(vaga)
                descartadas_pos += 1
                continue

            if self.settings.apenas_remoto and vaga.modelo_trabalho != WorkModelEnum.REMOTO:
                vaga.camada_descarte = "Camada 1 - Heurística de Local/Modelo"
                vaga.motivo_descarte = f"Modelo de trabalho classificado como {vaga.modelo_trabalho.value} (não é 100% remoto viável)."
                vagas_rejeitadas.append(vaga)
                descartadas_pos += 1
                continue

            # Avaliação de Match
            vaga.match_curriculo = avaliar_compatibilidade(vaga, perfis=self.profiles)
            scores = (
                [perfil_match.score_porcentagem for perfil_match in vaga.match_curriculo.perfis.values()]
                if vaga.match_curriculo and vaga.match_curriculo.perfis
                else []
            )
            if any(score >= threshold for score in scores):
                vagas_aprovadas.append(vaga)
            else:
                vaga.camada_descarte = "Camada 1 - Score de Keywords"
                vaga.motivo_descarte = gerar_diagnostico_descarte_keywords(
                    item=vaga,
                    match_curriculo=vaga.match_curriculo,
                    threshold=threshold,
                )
                vagas_rejeitadas.append(vaga)

        # Ordenar pelo maior match primeiro antes da avaliação LLM
        def extrair_chave_match(item: JobItem) -> tuple[int, int]:
            if not item.match_curriculo:
                return (0, 0)
            return (
                item.match_curriculo.score_maximo,
                item.match_curriculo.total_skills_maximo,
            )

        vagas_aprovadas.sort(key=extrair_chave_match, reverse=True)

        # 2ª Camada: Filtro Semântico via LLM Local (lcpp / gemini-bridge)
        if vagas_aprovadas and self.settings.usar_filtro_llm:
            vagas_aprovadas, rejeitadas_llm = filtrar_vagas_com_llm_em_lote(
                vagas=vagas_aprovadas,
                settings=self.settings,
                rotulo_lote="ATS (Gupy + InHire)",
            )
            vagas_rejeitadas.extend(rejeitadas_llm)
            vagas_aprovadas.sort(key=extrair_chave_match, reverse=True)

        vagas_gupy = [vaga for vaga in vagas_aprovadas if vaga.plataforma == PlatformEnum.GUPY]
        vagas_inhire = [vaga for vaga in vagas_aprovadas if vaga.plataforma == PlatformEnum.INHIRE]

        logger.info(
            f"🏢 [ATS-PIPELINE] Avaliação concluída: {len(vagas_aprovadas)} vagas qualificadas "
            f"(Gupy: {len(vagas_gupy)}, InHire: {len(vagas_inhire)} | Descartes: pré={descartadas_pre}, pós={descartadas_pos})"
        )

        return AtsReportOutput(
            filtro_threshold_minimo=threshold,
            total_aprovados=len(vagas_aprovadas),
            total_gupy=len(vagas_gupy),
            total_inhire=len(vagas_inhire),
            total_rejeitados=len(vagas_rejeitadas),
            vagas=vagas_aprovadas,
            vagas_gupy=vagas_gupy,
            vagas_inhire=vagas_inhire,
            rejeitadas=vagas_rejeitadas,
        )

    def exportar_resultados(self, output: AtsReportOutput) -> None:
        logger.info("📊 [ATS-PIPELINE] [FASE 3/3] Exportando relatórios ATS JSON e Markdown...")
        salvar_dados_processados_json(output, self.settings.output_ats_processed_json)
        gerar_relatorio_ats_markdown(output, self.settings.output_ats_markdown_report)

    def run(self, notificar_telegram: bool = True) -> AtsReportOutput:
        vagas_brutas = self.executar_extracao()
        output = self.executar_pos_processamento(vagas_brutas)
        self.exportar_resultados(output)
        if notificar_telegram and self.settings.enviar_telegram:
            notifier = TelegramNotifier(settings=self.settings)
            notifier.enviar_relatorio_completo(output_ats=output, output_linkedin=None)
        logger.info(
            f"✨ [ATS-PIPELINE] Concluído com {output.total_aprovados} oportunidades qualificadas "
            f"(Relatório: {self.settings.output_ats_markdown_report})!"
        )
        return output


if __name__ == "__main__":
    from app.ats.runner import executar_busca_ats_direta

    executar_busca_ats_direta()
