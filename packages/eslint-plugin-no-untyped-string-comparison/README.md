# eslint-plugin-no-untyped-string-comparison

Type-aware ESLint plugin that disallows comparing generic `string` (and optionally `any` / `unknown`) values against static string literals (`'...'`, `"..."`, or `` `...` ``), while allowing comparisons against string literal unions, enums, `as const` types, and `typeof` expressions.

## Installation

```bash
npm install -D eslint-plugin-no-untyped-string-comparison
```

## Flat Config (`eslint.config.js`)

Requires TypeScript type-aware linting (`projectService: true` or `project: true`).

```js
import tseslint from 'typescript-eslint';
import noUntypedStringComparison from 'eslint-plugin-no-untyped-string-comparison';

export default tseslint.config(
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      'no-untyped-string-comparison': noUntypedStringComparison,
    },
    rules: {
      'no-untyped-string-comparison/no-untyped-string-comparison': [
        'error',
        {
          disallowAny: true,
          disallowUnknown: false,
          allowEmptyString: true,
        },
      ],
    },
  }
);
```

## Options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `disallowAny` | `boolean` | `true` | Report comparisons where the non-literal side is typed as `any`. |
| `disallowUnknown` | `boolean` | `false` | Report comparisons where the non-literal side is typed as `unknown`. |
| `allowEmptyString` | `boolean` | `true` | Allow comparisons against empty strings (`''`, `""`, `` `` ``). |
