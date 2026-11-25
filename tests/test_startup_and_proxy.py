import unittest
from unittest.mock import MagicMock, patch

from proxy_pool.client import requisicao_com_rotacao
from proxy_pool.rotator import ProxyRotator


class ProxyValidationTests(unittest.TestCase):
    @patch("proxy_pool.rotator.requests.get")
    def test_proxy_response_valid_when_ip_trace_present(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        response.text = '{"origin": "203.0.113.5"}'
        mock_get.return_value = response

        self.assertTrue(ProxyRotator.testar_proxy_sincrono("http://203.0.113.5:8080"))

    @patch("proxy_pool.rotator.requests.get")
    def test_proxy_response_rejected_for_html_placeholder(self, mock_get):
        response = MagicMock()
        response.status_code = 200
        response.text = "<html><title>Access Denied</title></html>"
        mock_get.return_value = response

        self.assertFalse(ProxyRotator.testar_proxy_sincrono("http://203.0.113.5:8080"))

    @patch("proxy_pool.client.requests.get")
    def test_requisicao_com_rotacao_does_not_retry_heavily_on_blocked_response(self, mock_get):
        mock_get.return_value = MagicMock(status_code=403)

        result = requisicao_com_rotacao(
            "https://example.com",
            usar_proxy=False,
            timeout=8,
            max_retries=4,
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
