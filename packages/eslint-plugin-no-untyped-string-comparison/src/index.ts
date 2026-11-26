import type { TSESLint } from '@typescript-eslint/utils';
import {
  noUntypedStringComparison,
  type NoUntypedStringComparisonOptions,
} from './rule.ts';

export type { NoUntypedStringComparisonOptions };
export { noUntypedStringComparison };

/**
 * Standalone ESLint plugin exporting the `no-untyped-string-comparison` rule.
 */
const plugin = {
  meta: {
    name: 'eslint-plugin-no-untyped-string-comparison',
    version: '0.1.0',
  },
  rules: {
    'no-untyped-string-comparison': noUntypedStringComparison,
  },
} satisfies TSESLint.FlatConfig.Plugin;

export default plugin;
