import subprocess
import time
from pathlib import Path

import requests

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.shared.http.proxy_rotator import DEFAULT_HEADERS

DOCKER_EXECUTABLE = "/usr/bin/docker"

def garantir_searxng_ativo(settings: Settings | None = None) -> bool:
    cfg = settings or default_settings
    max_espera = cfg.searxng_max_espera
    timeout = 5

    logger.debug("[POSTS-SEARXNG] Verificando integridade da instância local SearXNG...")
    for tentativa in range(max_espera + 1):
        try:
            response = requests.get(
                cfg.searxng_url,
                params={"q": "test", "format": "json"},
                headers=DEFAULT_HEADERS,
                timeout=timeout,
            )
            if response.status_code == 200:
                logger.debug("[POSTS-SEARXNG] Instância local SearXNG está pronta.")
                return True
        except requests.RequestException:
            pass

        if tentativa == 0:
            try:
                if not Path(DOCKER_EXECUTABLE).is_file():
                    logger.warning("[POSTS-SEARXNG] Binário Docker não encontrado; verifique a inicialização manual.")
                    continue
                logger.info("[POSTS-SEARXNG] Subindo container Docker SearXNG...")
                subprocess.run(  # noqa: S603
                    [DOCKER_EXECUTABLE, "compose", "up", "-d"],
                    cwd=cfg.searxng_compose_dir,
                    check=False,
                )
            except OSError as exc:
                logger.warning(f"[POSTS-SEARXNG] Não foi possível iniciar o SearXNG: {exc}")

        if tentativa < max_espera:
            time.sleep(1)

    logger.error("[POSTS-SEARXNG] Timeout ao tentar conectar ao SearXNG.")
    return False
