import unittest
from unittest.mock import MagicMock, patch

from app.models.enums import ScopeEnum
from app.posts.fetcher import buscar_posts_linkedin, gerar_variantes_query_posts
from app.shared.http.client import requisicao_com_rotacao
from app.shared.http.proxy_rotator import ProxyRotator


class ProxyValidationTests(unittest.TestCase):
    def test_proxy_response_valid_when_ip_trace_present(self):
        rotator = ProxyRotator()
        response = MagicMock()
        response.status_code = 200
        response.text = "ip=203.0.113.5\n"
        response.headers = {"Content-Type": "text/plain"}

        self.assertTrue(rotator._proxy_response_looks_valid(response))

    def test_proxy_response_rejected_for_html_placeholder(self):
        rotator = ProxyRotator()
        response = MagicMock()
        response.status_code = 200
        response.text = "<html><title>Access Denied</title></html>"
        response.headers = {"Content-Type": "text/html"}

        self.assertFalse(rotator._proxy_response_looks_valid(response))

    def test_query_variants_keep_a_broad_fallback(self):
        variants = gerar_variantes_query_posts('site:linkedin.com/posts/ "hiring" AND "Python" AND "remote"')

        self.assertIn("site:linkedin.com/posts/", variants[0])
        self.assertTrue(any("linkedin.com/posts" in variant for variant in variants))
        self.assertTrue(any("hiring" in variant.lower() for variant in variants))
        self.assertTrue(any("python" in variant.lower() for variant in variants))

    @patch("app.shared.http.client.time.sleep", return_value=None)
    @patch("app.shared.http.client.requests.get")
    def test_requisicao_com_rotacao_does_not_retry_heavily_on_blocked_response(self, mock_get, mock_sleep):
        mock_get.return_value = MagicMock(status_code=403)

        result = requisicao_com_rotacao("https://example.com", max_retries=4, timeout=8)

        self.assertIsNone(result)
        self.assertEqual(mock_sleep.call_count, 0)


class DDGSPostSearchTests(unittest.TestCase):
    @patch("app.posts.fetcher.DDGS")
    def test_buscar_posts_linkedin_converts_ddgs_results(self, mock_ddgs_cls):
        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {
                "title": "Vaga Python Junior",
                "href": "https://www.linkedin.com/posts/empresa_vaga-python-activity-12345",
                "body": "Estamos contratando desenvolvedor Python Junior remoto.",
            },
            {
                "title": "Ignored Link",
                "href": "https://www.google.com/search?q=test",
                "body": "Not a linkedin post",
            },
        ]
        mock_ddgs_cls.return_value = mock_instance

        posts = buscar_posts_linkedin(
            query="site:linkedin.com/posts/ python junior",
            scope=ScopeEnum.NACIONAL,
            max_resultados=5,
        )

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].titulo, "Vaga Python Junior")
        self.assertIn("linkedin.com/posts", posts[0].link)


if __name__ == "__main__":
    unittest.main()
