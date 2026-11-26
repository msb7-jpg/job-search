# Design

## Approach
1. Wire `packages/eslint-plugin-no-untyped-string-comparison/src/index.ts` into `web/eslint.config.js` with `parserOptions.projectService: true` and options `{ disallowAny: true, disallowUnknown: false, allowEmptyString: true }`.
2. Remove the legacy `no-restricted-syntax` string-comparison selectors from `web/eslint.config.js`.
3. Run `bun test packages/eslint-plugin-no-untyped-string-comparison/tests/rule.test.ts` and `make check`, fixing any violations in `web/src/`.

## Verification
- `bun test packages/eslint-plugin-no-untyped-string-comparison/tests/rule.test.ts` passes.
- `make check` exits `0`.
