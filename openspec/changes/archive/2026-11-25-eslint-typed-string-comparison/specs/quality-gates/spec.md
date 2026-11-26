# Delta Specification: Quality Gates

## MODIFIED Requirements

### Requirement: Full Mechanical Gate (`make check`)
Every change MUST pass `make check` (`ruff format --check`, `ruff check`, `check_python_hygiene.py`, `pyright`, `lint-imports`, `pytest`, `tsc`, `eslint`, `fallow`), with `eslint` enforcing `no-untyped-string-comparison/no-untyped-string-comparison` via `ts.TypeChecker` instead of `no-restricted-syntax`.

#### Scenario: Running quality gates
- **WHEN** `make check` is executed at the repository root
- **THEN** all Python and TypeScript/Bun checks exit `0`

#### Scenario: Untyped string comparison caught by ESLint
- **WHEN** TypeScript code compares a generic `string` (or `any` when `disallowAny: true`) against a non-empty string literal in `BinaryExpression` or `SwitchCase`
- **THEN** `eslint` reports an error, while literal unions, `enum`, `as const`, and `typeof` comparisons are permitted
