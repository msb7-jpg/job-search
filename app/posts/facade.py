from app.core.config import Settings
from app.core.logging import logger
from app.models.enums import ScopeEnum
from app.models.post import PostItem
from app.posts.fetcher import buscar_posts_linkedin
from app.profiles.base import Profile


class PostsPipelineFacade:
    def __init__(
        self,
        settings: Settings,
        profiles: list[Profile],
    ) -> None:
        self.settings = settings
        self.profiles = profiles

    def _obter_queries_nacionais(self) -> list[str]:
        queries_vistas: set[str] = set()
        queries_ordenadas: list[str] = []
        for perfil in self.profiles:
            for query in perfil.queries_posts_nacionais:
                if query not in queries_vistas:
                    queries_vistas.add(query)
                    queries_ordenadas.append(query)
        return queries_ordenadas

    def _obter_queries_internacionais(self) -> list[str]:
        queries_vistas: set[str] = set()
        queries_ordenadas: list[str] = []
        for perfil in self.profiles:
            for query in perfil.queries_posts_internacionais:
                if query not in queries_vistas:
                    queries_vistas.add(query)
                    queries_ordenadas.append(query)
        return queries_ordenadas

    def run(self) -> tuple[list[PostItem], list[PostItem]]:
        logger.info(
            f"💬 [POSTS-PIPELINE] Iniciando extração de posts do LinkedIn via Google Search para "
            f"{len(self.profiles)} perfis ({', '.join(p.name for p in self.profiles)}) "
            f"[Filtro: {self.settings.filtro_tempo.descricao} ({self.settings.filtro_tempo.value})]..."
        )

        queries_nacionais = self._obter_queries_nacionais()
        queries_internacionais = self._obter_queries_internacionais()

        # 1. Posts Nacionais
        posts_nac: list[PostItem] = []
        for query in queries_nacionais:
            encontrados = buscar_posts_linkedin(
                query,
                scope=ScopeEnum.NACIONAL,
                settings=self.settings,
            )
            logger.info(f"💬 [POSTS-SEARCH] Query: '{query[:45]}...' (Brasil) -> {len(encontrados)} posts encontrados")
            posts_nac.extend(encontrados)

        # 2. Posts Internacionais
        posts_int: list[PostItem] = []
        for query in queries_internacionais:
            encontrados = buscar_posts_linkedin(
                query,
                scope=ScopeEnum.INTERNACIONAL,
                settings=self.settings,
            )
            logger.info(f"💬 [POSTS-SEARCH] Query: '{query[:45]}...' (Gringa) -> {len(encontrados)} posts encontrados")
            posts_int.extend(encontrados)

        # 3. Deduplicação por Link
        posts_nac_unique = list({post.link: post for post in posts_nac}.values())
        posts_int_unique = list({post.link: post for post in posts_int}.values())

        total_coletado = len(posts_nac_unique) + len(posts_int_unique)
        logger.info(
            f"💬 [POSTS-PIPELINE] Posts únicos coletados: Nacional={len(posts_nac_unique)}, "
            f"Internacional={len(posts_int_unique)} (Total: {total_coletado})"
        )
        return posts_nac_unique, posts_int_unique


if __name__ == "__main__":
    from app.posts.runner import executar_busca_posts_direta

    executar_busca_posts_direta()
