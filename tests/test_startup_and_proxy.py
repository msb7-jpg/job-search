import unittest
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.models.enums import ScopeEnum
from app.posts.fetcher import buscar_posts_linkedin, formatar_query
from app.shared.http.client import requisicao_com_rotacao
from app.shared.http.proxy_rotator import ProxyRotator


class ProxyValidationTests(unittest.TestCase):
    @patch("app.shared.http.proxy_rotator.requests.get")
    def test_proxy_response_valid_when_ip_trace_present(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        response.text = '{"origin": "203.0.113.5"}'
        mock_get.return_value = response

        self.assertTrue(ProxyRotator.testar_proxy_sincrono("http://203.0.113.5:8080"))

    @patch("app.shared.http.proxy_rotator.requests.get")
    def test_proxy_response_rejected_for_html_placeholder(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        response.text = "<html><title>Access Denied</title></html>"
        mock_get.return_value = response

        self.assertFalse(ProxyRotator.testar_proxy_sincrono("http://203.0.113.5:8080"))

    def test_query_variants_keep_a_broad_fallback(self):
        variants = formatar_query('"hiring" AND "Python" AND "remote"')
        self.assertIn("site:linkedin.com/posts/", variants)

    @patch("app.shared.http.client.requests.get")
    def test_requisicao_com_rotacao_does_not_retry_heavily_on_blocked_response(self, mock_get):
        mock_get.return_value = MagicMock(status_code=403)

        result = requisicao_com_rotacao(
            "https://example.com",
            usar_proxy=False,
            timeout=8,
            max_retries=4,
        )

        self.assertIsNone(result)


class GooglePostSearchTests(unittest.TestCase):
    @patch("app.posts.fetcher.requests.get")
    def test_buscar_posts_linkedin_converts_google_direct_html(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="g">
          <div class="tF2Cxc">
            <a href="https://www.linkedin.com/posts/empresa_vaga-python-activity-12345?trk=public">
              <h3>Vaga Python Junior Remoto</h3>
            </a>
            <div class="VwiC3b">Estamos contratando desenvolvedor Python Junior 100% remoto para time backend.</div>
          </div>
        </div>
        """
        mock_get.return_value = mock_response

        test_settings = Settings(usar_proxy=False)
        posts = buscar_posts_linkedin(
            query="site:linkedin.com/posts/ python junior",
            scope=ScopeEnum.NACIONAL,
            settings=test_settings,
            max_resultados=5,
        )

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].titulo, "Vaga Python Junior Remoto")
        self.assertIn("linkedin.com/posts", posts[0].link)

    @patch("app.posts.fetcher.requests.get")
    def test_buscar_posts_linkedin_filters_senior_when_junior_target(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <div class="g">
          <div class="tF2Cxc">
            <a href="https://www.linkedin.com/posts/empresa_vaga-senior-activity-99999">
              <h3>Senior Python Staff Architect</h3>
            </a>
            <div class="VwiC3b">Vaga para liderança e arquitetura sênior.</div>
          </div>
        </div>
        """
        mock_get.return_value = mock_response

        test_settings = Settings(usar_proxy=False)
        posts = buscar_posts_linkedin(
            query="site:linkedin.com/posts/ python senior",
            scope=ScopeEnum.NACIONAL,
            settings=test_settings,
            max_resultados=5,
        )

        self.assertEqual(len(posts), 0)


if __name__ == "__main__":
    unittest.main()

