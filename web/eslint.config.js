import js from '@eslint/js';
import boundaries from 'eslint-plugin-boundaries';
import jsdoc from 'eslint-plugin-jsdoc';
import reactHooks from 'eslint-plugin-react-hooks';
import tsdoc from 'eslint-plugin-tsdoc';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist', 'src/api/openapi.d.ts'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      'react-hooks': reactHooks,
      boundaries,
      jsdoc,
      tsdoc,
    },
    settings: {
      'boundaries/elements': [
        { type: 'api', pattern: 'src/api/*' },
        { type: 'state', pattern: 'src/state/*' },
        { type: 'lib', pattern: 'src/lib/*' },
        { type: 'components', pattern: 'src/components/*' },
        { type: 'features', pattern: 'src/features/*' },
      ],
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'quotes': ['error', 'single', { avoidEscape: true }],
      'arrow-parens': ['error', 'as-needed'],
      'react-hooks/immutability': 'off',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': 'off',
      'id-length': ['error', { min: 2 }],
      'max-lines': ['error', { max: 200, skipBlankLines: true, skipComments: true }],
      'tsdoc/syntax': 'error',
      'jsdoc/require-description': 'error',
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: false,
          require: {
            FunctionDeclaration: true,
            MethodDefinition: true,
          },
          contexts: [
            'TSInterfaceDeclaration',
            'TSTypeAliasDeclaration',
            'TSInterfaceDeclaration > TSInterfaceBody > TSPropertySignature',
          ],
        },
      ],
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'react',
              importNames: ['useState', 'useMemo', 'useEffect', 'useRef', 'useCallback'],
              message:
                "Use useSignal / useComputed from '@preact/signals-react'. Classic lifecycle hooks (useEffect/useRef) are only allowed inside src/**/hooks/*.ts.",
            },
            {
              name: '@preact/signals-react/runtime',
              message: 'useSignals() is unnecessary with @preact/signals-react-transform.',
            },
          ],
        },
      ],
      'no-restricted-syntax': [
        'error',
        {
          selector:
            "BinaryExpression[operator=/^(===|!==|==|!=)$/][left.type!='UnaryExpression'][right.type='Literal'][right.raw=/^['\"]/][right.value!='']",
          message: 'Avoid comparing against raw string literals. Use a named constant instead.',
        },
        {
          selector:
            "BinaryExpression[operator=/^(===|!==|==|!=)$/][right.type!='UnaryExpression'][left.type='Literal'][left.raw=/^['\"]/][left.value!='']",
          message: 'Avoid comparing against raw string literals. Use a named constant instead.',
        },
        {
          selector:
            "BinaryExpression[operator=/^(===|!==|==|!=)$/][left.type!='UnaryExpression'][right.type='TemplateLiteral'][right.expressions.length=0]",
          message: 'Avoid comparing against raw template literals. Use a named constant instead.',
        },
        {
          selector:
            "SwitchCase[test.type='Literal'][test.raw=/^['\"]/][test.value!='']",
          message: 'Avoid switching on raw string literals. Use a named constant instead.',
        },
      ],
      'boundaries/element-types': [
        'error',
        {
          default: 'allow',
          rules: [
            {
              from: ['components'],
              disallow: ['features'],
              message: 'Shared components must not import feature modules.',
            },
            {
              from: ['api', 'state', 'lib'],
              disallow: ['components', 'features'],
              message: 'API/state/lib layers must not import UI components or features.',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['src/features/**/*Page.tsx', 'src/features/**/ReviewStudioModal.tsx', 'src/App.tsx'],
    rules: {
      'max-lines': ['error', { max: 120, skipBlankLines: true, skipComments: true }],
    },
  },
  {
    files: ['src/**/hooks/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: 'react',
              importNames: ['useState', 'useMemo'],
              message:
                "Use useSignal / useComputed from '@preact/signals-react' instead of useState / useMemo.",
            },
            {
              name: '@preact/signals-react/runtime',
              message: 'useSignals() is unnecessary with @preact/signals-react-transform.',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['src/components/ui/**'],
    rules: {
      'jsdoc/require-jsdoc': 'off',
      'jsdoc/require-description': 'off',
      'tsdoc/syntax': 'off',
      'id-length': 'off',
      'no-restricted-syntax': 'off',
      'no-restricted-imports': 'off',
    },
  }
);
