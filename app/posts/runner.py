from app.core.config import Settings
from app.core.logging import logger
from app.models.enums import TimeFilterEnum
from app.models.post import PostItem
from app.posts.facade import PostsPipelineFacade
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES
from app.shared.http.proxy_rotator import rotator


def executar_busca_posts_direta(
    settings: Settings | None = None,
    profiles: list[Profile] = DEFAULT_PROFILES,
) -> tuple[list[PostItem], list[PostItem]]:
    config = settings or Settings(filtro_tempo=TimeFilterEnum.ULTIMA_SEMANA)

    logger.info("=" * 80)
    logger.info("💬 INICIANDO BUSCA DIRETA DE POSTS DO LINKEDIN (Google Search)")
    logger.info(f"⚙️ Config: Recência={config.filtro_tempo.descricao} [{config.filtro_tempo.value}]")
    logger.info(f"👤 Perfis Ativos: {[perfil.display_name for perfil in profiles]}")
    logger.info("=" * 80)

    facade = PostsPipelineFacade(settings=config, profiles=profiles)
    posts_nacionais, posts_internacionais = facade.run()

    total_encontrado = len(posts_nacionais) + len(posts_internacionais)
    logger.info("=" * 80)
    logger.info("📊 RESUMO DE POSTS ENCONTRADOS")
    logger.info(f"Total Geral: {total_encontrado} posts")
    logger.info(f"  🇧🇷 Nacionais (Brasil): {len(posts_nacionais)}")
    logger.info(f"  🌐 Internacionais (Gringa): {len(posts_internacionais)}")
    logger.info("=" * 80)

    if posts_nacionais:
        logger.info("\n--- Amostra de Posts Nacionais ---")
        for indice, post in enumerate(posts_nacionais[:5], 1):
            logger.info(f"{indice}. {post.titulo} | {post.data_postagem} -> {post.link}")

    if posts_internacionais:
        logger.info("\n--- Amostra de Posts Internacionais ---")
        for indice, post in enumerate(posts_internacionais[:5], 1):
            logger.info(f"{indice}. {post.titulo} | {post.data_postagem} -> {post.link}")

    return posts_nacionais, posts_internacionais


if __name__ == "__main__":
    rotator.inicializar_pool()
    executar_busca_posts_direta()
