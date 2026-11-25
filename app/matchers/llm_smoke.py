import time

from app.core.config import Settings
from app.matchers.llm_matcher import (
    avaliar_vaga_com_llm,
    carregar_texto_curriculo,
    verificar_servidor_llm_ativo,
)
from app.models.job import JobItem


def executar_teste_llm() -> None:
    """Função standalone para testar conexão e avaliação com o endpoint configurado."""
    cfg = Settings()
    print("=" * 80)
    print("🧠 TESTE DE CONEXÃO E AVALIAÇÃO COM LLM JUDGE (OPENAI-COMPATIBLE)")
    print(f"🔗 Endpoint Base URL: {cfg.llm_base_url}")
    print(f"🤖 Modelo Configurado: {cfg.llm_model_name}")
    print("=" * 80)

    ativo, modelo_detectado = verificar_servidor_llm_ativo(cfg.llm_base_url, cfg.llm_api_key, timeout=4)
    if not ativo:
        print(f"❌ Erro: O servidor em {cfg.llm_base_url} não respondeu ao endpoint /models.")
        return

    print(f"✅ Conexão bem-sucedida! Servidor ativo (Modelo detectado: {modelo_detectado}).")

    vaga_teste = JobItem(
        job_id="test_001",
        titulo="Desenvolvedor Python Júnior (Remoto)",
        empresa="Tech Innovations Brasil",
        localizacao="Remoto - Brasil",
        link="https://linkedin.com/jobs/view/test-001",
        descricao_completa=(
            "Buscamos desenvolvedor Python Júnior com até 2 anos de experiência para atuar com Django, "
            "FastAPI e PostgreSQL em regime 100% remoto para todo o Brasil. Desejável conhecimento em Vue.js ou React."
        ),
    )

    curriculo = carregar_texto_curriculo(cfg.caminho_curriculo_md)
    print("\n🔍 Avaliando vaga de teste:")
    print(f"   Título: {vaga_teste.titulo} ({vaga_teste.empresa})")
    print("\n⏳ Enviando requisição para o LLM Judge...")

    inicio = time.perf_counter()
    resultado = avaliar_vaga_com_llm(
        vaga=vaga_teste,
        texto_curriculo=curriculo,
        base_url=cfg.llm_base_url,
        model_name=cfg.llm_model_name,
        api_key=cfg.llm_api_key,
        max_anos_experiencia=cfg.max_anos_experiencia,
        timeout=cfg.llm_timeout,
    )
    tempo_total = time.perf_counter() - inicio

    print("=" * 80)
    print(f"📊 Aprovado: {'✅ SIM' if resultado.aprovado else '❌ NÃO'} | Score: {resultado.score_llm}/100")
    print(f"   Nível: {resultado.nivel_detectado} | Justificativa: {resultado.justificativa}")
    print(f"   Tempo de Resposta: {tempo_total:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    executar_teste_llm()
