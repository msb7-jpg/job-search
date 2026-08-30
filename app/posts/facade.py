from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.models.enums import ScopeEnum
from app.models.post import PostItem
from app.posts.fetcher import buscar_posts_linkedin
from app.posts.queries import Gringas, Nacionais
from app.posts.searxng_client import garantir_searxng_ativo


class PostsPipelineFacade:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings

    def run(self) -> tuple[list[PostItem], list[PostItem]]:
        logger.info("💬 [POSTS-PIPELINE] Iniciando extração de posts do LinkedIn...")

        if not garantir_searxng_ativo(self.settings):
            logger.error("💬 [POSTS-PIPELINE] SearXNG indisponível. Pulando busca de posts.")
            return [], []

        # 1. Posts Nacionais
        posts_nac: list[PostItem] = []
        for query in (Nacionais.POSTS_BE, Nacionais.POSTS_FS):
            posts_nac.extend(buscar_posts_linkedin(query, scope=ScopeEnum.NACIONAL, settings=self.settings))

        # 2. Posts Internacionais
        posts_int: list[PostItem] = []
        for query in (Gringas.POSTS_BE, Gringas.POSTS_FS):
            posts_int.extend(buscar_posts_linkedin(query, scope=ScopeEnum.INTERNACIONAL, settings=self.settings))

        # 3. Deduplicação por Link
        posts_nac_unique = list({p.link: p for p in posts_nac}.values())
        posts_int_unique = list({p.link: p for p in posts_int}.values())

        logger.info(f"💬 [POSTS-PIPELINE] Posts únicos coletados: Nacional={len(posts_nac_unique)}, Internacional={len(posts_int_unique)}")
        return posts_nac_unique, posts_int_unique
