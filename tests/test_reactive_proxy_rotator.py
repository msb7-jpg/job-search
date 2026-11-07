import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.shared.http.proxy_record import ProxyRecord
from app.shared.http.proxy_rotator import RealtimeProxyRotator
from app.shared.http.proxy_sources import (
    sanitizar_esquema_proxy,
    validar_integridade_semantica_resposta,
)


class TestProxyRecordAndReactiveRotator(unittest.TestCase):
    def test_proxy_record_ewma_and_priority_calculation(self) -> None:
        record = ProxyRecord(url="http://10.0.0.1:8080", latency_ewma=1.0, total_successes=1)
        self.assertAlmostEqual(record.calculate_priority(), 1.0)

        # EWMA_nova = 0.7 * 1.0 + 0.3 * 0.5 = 0.85
        new_priority = record.record_success(0.5)
        self.assertAlmostEqual(record.latency_ewma, 0.85, places=4)
        self.assertAlmostEqual(new_priority, 0.85, places=4)
        self.assertEqual(record.consecutive_fails, 0)

        # Falha leve (ex: 500) -> backoff na prioridade: 0.85 * (1 + 1 * 2) = 2.55
        manter = record.record_failure(status_code=500, is_critical_timeout=False)
        self.assertTrue(manter)
        self.assertAlmostEqual(record.priority, 2.55, places=4)

        # Segunda falha consecutiva -> expurgo imediato
        manter_segunda = record.record_failure(status_code=500, is_critical_timeout=False)
        self.assertFalse(manter_segunda)
        self.assertFalse(record.is_active)

    def test_proxy_record_immediate_purge_on_429_or_timeout(self) -> None:
        record_rate_limit = ProxyRecord(url="http://10.0.0.2:8080", latency_ewma=0.4, total_successes=2)
        keep_after_429 = record_rate_limit.record_failure(status_code=429, is_critical_timeout=False)
        self.assertFalse(keep_after_429)
        self.assertFalse(record_rate_limit.is_active)

        record_timeout = ProxyRecord(url="http://10.0.0.3:8080", latency_ewma=0.4, total_successes=2)
        keep_after_timeout = record_timeout.record_failure(status_code=None, is_critical_timeout=True)
        self.assertFalse(keep_after_timeout)
        self.assertFalse(record_timeout.is_active)

    def test_rotator_dispatches_lowest_ewma_and_respects_in_flight(self) -> None:
        with TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "tier_a.json"
            custom_rotator = RealtimeProxyRotator(tier_a_cache_path=cache_file)

            custom_rotator.adicionar_proxy_valido("http://192.0.2.10:8080", latency=1.8, source="src_slow")
            custom_rotator.adicionar_proxy_valido("http://192.0.2.20:8080", latency=0.25, source="src_fast")

            # Primeiro dispatch deve escolher o nó mais rápido (0.25s) com in_flight == 0
            primeiro = custom_rotator.get_proxy()
            self.assertIsNotNone(primeiro)
            assert primeiro is not None
            self.assertEqual(primeiro.url, "http://192.0.2.20:8080")
            self.assertEqual(primeiro.in_flight, 1)

            # Segundo dispatch concorrente deve escolher o outro nó livre (in_flight == 0)
            segundo = custom_rotator.get_proxy()
            self.assertIsNotNone(segundo)
            assert segundo is not None
            self.assertEqual(segundo.url, "http://192.0.2.10:8080")

            # Reportar sucesso libera in_flight e mantém o mais rápido no topo
            custom_rotator.report_success("http://192.0.2.20:8080", latency=0.20)
            custom_rotator.release_proxy("http://192.0.2.10:8080")

            terceiro = custom_rotator.get_proxy()
            assert terceiro is not None
            self.assertEqual(terceiro.url, "http://192.0.2.20:8080")

    def test_tier_a_cache_persistence_and_warm_load(self) -> None:
        with TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "tier_a.json"
            rotator_writer = RealtimeProxyRotator(tier_a_cache_path=cache_file)
            rotator_writer.adicionar_proxy_valido("http://198.51.100.7:3128", latency=0.45, source="geonode")
            rotator_writer.salvar_cache_tier_a()

            self.assertTrue(cache_file.exists())

            rotator_reader = RealtimeProxyRotator(tier_a_cache_path=cache_file)
            loaded = rotator_reader.carregar_cache_tier_a()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].url, "http://198.51.100.7:3128")
            self.assertAlmostEqual(loaded[0].latency_ewma, 0.45, places=2)

    def test_sanitizar_esquema_and_semantic_integrity(self) -> None:
        self.assertEqual(sanitizar_esquema_proxy("203.0.113.10:8080"), "http://203.0.113.10:8080")
        self.assertEqual(sanitizar_esquema_proxy("https://203.0.113.10:8080"), "http://203.0.113.10:8080")
        self.assertEqual(sanitizar_esquema_proxy("socks5://203.0.113.10:1080"), "socks5://203.0.113.10:1080")
        self.assertIsNone(sanitizar_esquema_proxy("invalid_host"))

        self.assertTrue(validar_integridade_semantica_resposta('{"ip": "203.0.113.10"}', expected_marker="ip"))
        self.assertFalse(validar_integridade_semantica_resposta("<html><title>Mikrotik HttpProxy</title>ip</html>", expected_marker="ip"))
        self.assertFalse(validar_integridade_semantica_resposta("<html><body>Squid Error: Access Denied</body></html>"))


if __name__ == "__main__":
    unittest.main()
