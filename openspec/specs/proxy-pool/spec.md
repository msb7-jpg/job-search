# Proxy Pool Specification

## Purpose
Standalone reactive proxy rotator package (`proxy_pool/`) isolated from `app.*` internals.

## Requirements

### Requirement: Package Isolation Boundary
The `proxy_pool/` package MUST maintain zero imports from `app.*` and use standard `logging.getLogger("proxy_pool")` with injectable cache paths (`tier_a_cache_path`).

#### Scenario: Standalone usage without app config
- **WHEN** `RealtimeProxyRotator` or `requisicao_com_rotacao` is imported and invoked outside `app/`
- **THEN** it operates without importing any `app.*` module and writes Tier-A cache only to the injected `tier_a_cache_path`
