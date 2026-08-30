import unittest
from unittest.mock import MagicMock, patch

import requests

from app.posts.fetcher import gerar_variantes_query_posts
from app.posts.searxng_client import garantir_searxng_ativo
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


@patch("app.posts.searxng_client.time.sleep", return_value=None)
@patch("app.posts.searxng_client.subprocess.run")
@patch("app.posts.searxng_client.requests.get")
class SearxngStartupTests(unittest.TestCase):
    def test_garantir_searxng_ativo_starts_container_if_unavailable(self, mock_get, mock_subprocess, _mock_sleep):
        mock_get.side_effect = [
            requests.exceptions.RequestException("down"),
            MagicMock(status_code=200, json=lambda: {"results": []}),
        ]
        mock_subprocess.return_value = MagicMock(returncode=0)

        self.assertTrue(garantir_searxng_ativo())
        mock_subprocess.assert_called_once()


if __name__ == "__main__":
    unittest.main()
