import { describe, expect, test } from 'bun:test';
import path from 'node:path';
import { Linter } from 'eslint';
import tseslint from 'typescript-eslint';
import plugin, {
  type NoUntypedStringComparisonOptions,
} from '../src/index.ts';

const TESTS_DIR = import.meta.dirname;
const FIXTURE_FILE = path.join(TESTS_DIR, 'fixtures', 'sample.ts');

function lintCode(
  code: string,
  options?: NoUntypedStringComparisonOptions
): Linter.LintMessage[] {
  const linter = new Linter({ configType: 'flat' });
  const ruleConfig: Linter.RuleEntry = options
    ? ['error', options]
    : ['error'];

  return linter.verify(
    code,
    [
      {
        files: ['**/*.ts'],
        languageOptions: {
          parser: tseslint.parser,
          parserOptions: {
            project: path.join(TESTS_DIR, 'tsconfig.json'),
            tsconfigRootDir: TESTS_DIR,
          },
        },
        plugins: {
          'no-untyped-string-comparison': plugin,
        },
        rules: {
          'no-untyped-string-comparison/no-untyped-string-comparison': ruleConfig,
        },
      },
    ],
    FIXTURE_FILE
  );
}

describe('no-untyped-string-comparison', () => {
  describe('generic string comparisons (should report)', () => {
    test('flags ===, !==, ==, != with generic string on left or right', () => {
      const messages = lintCode(`
        function check(name: string) {
          const a = name === 'michael';
          const b = 'michael' !== name;
          const c = name == "dwight";
          const d = "jim" != name;
          return a || b || c || d;
        }
      `);
      expect(messages.map(msg => msg.messageId)).toEqual([
        'untypedString',
        'untypedString',
        'untypedString',
        'untypedString',
      ]);
    });

    test('flags template literals without expressions', () => {
      const messages = lintCode(`
        function check(name: string) {
          if (name === \`michael\`) return 1;
          if (\`dwight\` !== name) return 2;
          return 0;
        }
      `);
      expect(messages.map(msg => msg.messageId)).toEqual([
        'untypedString',
        'untypedString',
      ]);
    });

    test('flags optional/nullable string unions (string | undefined, string | null)', () => {
      const messages = lintCode(`
        function check(name?: string, role: string | null = null) {
          if (name === 'michael') return 1;
          if (role === 'admin') return 2;
          return 0;
        }
      `);
      expect(messages.map(msg => msg.messageId)).toEqual([
        'untypedString',
        'untypedString',
      ]);
    });

    test('flags generic type parameter constrained to string', () => {
      const messages = lintCode(`
        function check<T extends string>(value: T) {
          return value === 'michael';
        }
      `);
      expect(messages.map(msg => msg.messageId)).toEqual(['untypedString']);
    });

    test('flags switch/case on generic string (literal and template literal)', () => {
      const messages = lintCode(`
        function check(name: string) {
          switch (name) {
            case 'michael':
              return 1;
            case \`dwight\`:
              return 2;
            default:
              return 0;
          }
        }
      `);
      expect(messages.map(msg => msg.messageId)).toEqual([
        'untypedString',
        'untypedString',
      ]);
    });
  });

  describe('typed literal unions, enums, as const, typeof (should pass)', () => {
    test('allows string literal union types', () => {
      const messages = lintCode(`
        type UserName = 'michael' | 'dwight' | 'jim';
        function check(name: UserName) {
          if (name === 'michael') return 1;
          if (\`dwight\` === name) return 2;
          switch (name) {
            case 'jim':
              return 3;
            default:
              return 0;
          }
        }
      `);
      expect(messages).toHaveLength(0);
    });

    test('allows as const inferred types and enum types', () => {
      const messages = lintCode(`
        const ROLES = ['admin', 'guest'] as const;
        type Role = (typeof ROLES)[number];
        enum Status { Active = 'active', Inactive = 'inactive' }

        function check(role: Role, status: Status) {
          if (role === 'admin') return 1;
          if (status === 'active') return 2;
          return 0;
        }
      `);
      expect(messages).toHaveLength(0);
    });

    test('allows generic type parameter constrained to literal union', () => {
      const messages = lintCode(`
        function check<T extends 'a' | 'b'>(value: T) {
          return value === 'a';
        }
      `);
      expect(messages).toHaveLength(0);
    });

    test('allows typeof expressions naturally', () => {
      const messages = lintCode(`
        function check(val: unknown, fn: unknown) {
          if (typeof val === 'string') return 1;
          if (typeof fn === 'function') return 2;
          if (typeof window === 'undefined') return 3;
          return 0;
        }
      `);
      expect(messages).toHaveLength(0);
    });

    test('ignores literal-to-literal comparisons and interpolated templates', () => {
      const messages = lintCode(`
        function check(name: string, prefix: string) {
          if ('a' === 'b') return 1;
          if (\`a\` === 'b') return 2;
          if (name === \`\${prefix}_admin\`) return 3;
          return 0;
        }
      `);
      expect(messages).toHaveLength(0);
    });
  });

  describe('configurable flags: disallowAny, disallowUnknown, allowEmptyString', () => {
    test('disallowAny defaults to true and can be disabled', () => {
      const code = `
        function check(val: any) {
          return val === 'michael';
        }
      `;
      expect(lintCode(code).map(msg => msg.messageId)).toEqual(['untypedAny']);
      expect(lintCode(code, { disallowAny: true }).map(msg => msg.messageId)).toEqual([
        'untypedAny',
      ]);
      expect(lintCode(code, { disallowAny: false })).toHaveLength(0);
    });

    test('disallowUnknown defaults to false and can be enabled', () => {
      const code = `
        function check(val: unknown) {
          return val === 'michael';
        }
      `;
      expect(lintCode(code)).toHaveLength(0);
      expect(lintCode(code, { disallowUnknown: true }).map(msg => msg.messageId)).toEqual([
        'untypedUnknown',
      ]);
    });

    test('allowEmptyString defaults to true and can be disabled', () => {
      const code = `
        function check(val: string) {
          return val === '' || val !== \`\`;
        }
      `;
      expect(lintCode(code)).toHaveLength(0);
      expect(lintCode(code, { allowEmptyString: false }).map(msg => msg.messageId)).toEqual([
        'untypedString',
        'untypedString',
      ]);
    });
  });
});
