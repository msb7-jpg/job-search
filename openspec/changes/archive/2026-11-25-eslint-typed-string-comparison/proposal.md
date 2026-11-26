# Proposal

## Why
`web/eslint.config.js` currently relies on `no-restricted-syntax` to catch untyped string literal comparisons. A decoupled, TypeScript `ts.TypeChecker`-based ESLint plugin (`packages/eslint-plugin-no-untyped-string-comparison`) has been authored (see `notes/new-eslint.md`) and needs to be integrated into the frontend lint pipeline.

## What Changes
- Configure `packages/eslint-plugin-no-untyped-string-comparison` in `web/eslint.config.js` with `projectService: true` and replace the brittle `no-restricted-syntax` string-comparison rule.
- Fix any newly flagged untyped string comparisons in `web/src/` and ensure `bun test` for the plugin passes.

## Capabilities

### Modified Capabilities
- `quality-gates`: Enforce type-aware `no-untyped-string-comparison` rule in `web/eslint.config.js` as part of `make check`.

## Impact
- Tooling: `web/eslint.config.js`, `packages/eslint-plugin-no-untyped-string-comparison/`, `Makefile` (if plugin tests are wired in).
- Frontend: Any `web/src/` files flagged by the new type-aware rule.
