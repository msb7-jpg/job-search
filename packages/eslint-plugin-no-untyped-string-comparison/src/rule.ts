import { ESLintUtils, type TSESTree } from '@typescript-eslint/utils';
import * as ts from 'typescript';

/**
 * Configuration options for the `no-untyped-string-comparison` rule.
 */
export interface NoUntypedStringComparisonOptions {
  /** Report comparisons where the non-literal side is typed as `any` (default: `true`). */
  disallowAny?: boolean;
  /** Report comparisons where the non-literal side is typed as `unknown` (default: `false`). */
  disallowUnknown?: boolean;
  /** Allow comparisons against empty string literals `""` or `` `` (default: `true`). */
  allowEmptyString?: boolean;
}

type MessageIds = 'untypedString' | 'untypedAny' | 'untypedUnknown';
type RuleOptions = [NoUntypedStringComparisonOptions];
type StaticStringNode = TSESTree.StringLiteral | TSESTree.TemplateLiteral;

const EQUALITY_OPERATORS = new Set(['==', '===', '!=', '!==']);

const createRule = ESLintUtils.RuleCreator(
  ruleName => `https://github.com/miguelsb/eslint-plugin-no-untyped-string-comparison#${ruleName}`
);

/**
 * Extracts the static string value when `node` is a string `Literal`
 * or a `TemplateLiteral` with zero interpolated expressions.
 */
function extractStaticString(node: TSESTree.Node): string | null {
  if (node.type === 'Literal' && typeof node.value === 'string') {
    return node.value;
  }
  if (node.type === 'TemplateLiteral' && node.expressions.length === 0) {
    return node.quasis[0]?.value.cooked ?? '';
  }
  return null;
}

/**
 * Classifies whether a TypeScript type represents an untyped string (`string`),
 * `any`, or `unknown` (recursively inspecting unions and type parameter constraints).
 */
function classifyDisallowedType(
  type: ts.Type,
  checker: ts.TypeChecker,
  options: Required<NoUntypedStringComparisonOptions>,
  visited = new Set<ts.Type>()
): MessageIds | null {
  if (visited.has(type)) {
    return null;
  }
  visited.add(type);

  if ((type.flags & ts.TypeFlags.Any) !== 0) {
    return options.disallowAny ? 'untypedAny' : null;
  }

  if ((type.flags & ts.TypeFlags.Unknown) !== 0) {
    return options.disallowUnknown ? 'untypedUnknown' : null;
  }

  if ((type.flags & ts.TypeFlags.String) !== 0) {
    return 'untypedString';
  }

  if ((type.flags & ts.TypeFlags.TypeParameter) !== 0) {
    const constraint = checker.getBaseConstraintOfType(type);
    if (constraint) {
      return classifyDisallowedType(constraint, checker, options, visited);
    }
    return null;
  }

  if (type.isUnion()) {
    for (const member of type.types) {
      const match = classifyDisallowedType(member, checker, options, visited);
      if (match) {
        return match;
      }
    }
  }

  return null;
}

/**
 * ESLint rule that forbids comparing generic `string` (and optionally `any`/`unknown`)
 * expressions against static string literals (`'...'`, `"..."`, or `` `...` ``).
 */
export const noUntypedStringComparison = createRule<RuleOptions, MessageIds>({
  name: 'no-untyped-string-comparison',
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow comparing generic string (or any/unknown) values against static string literals.',
    },
    messages: {
      untypedString:
        'Avoid comparing a generic `string` against literal "{{literal}}". Narrow the type with a string literal union, enum, or `as const`.',
      untypedAny:
        'Avoid comparing an `any` value against literal "{{literal}}". Type the value with a string literal union or narrow it first.',
      untypedUnknown:
        'Avoid comparing an `unknown` value against literal "{{literal}}". Narrow the value before comparing against "{{literal}}".',
    },
    schema: [
      {
        type: 'object',
        properties: {
          disallowAny: {
            type: 'boolean',
            description: 'Disallow comparisons where the non-literal side is `any`.',
          },
          disallowUnknown: {
            type: 'boolean',
            description: 'Disallow comparisons where the non-literal side is `unknown`.',
          },
          allowEmptyString: {
            type: 'boolean',
            description: 'Allow comparisons against empty string literals.',
          },
        },
        additionalProperties: false,
      },
    ],
  },
  defaultOptions: [
    {
      disallowAny: true,
      disallowUnknown: false,
      allowEmptyString: true,
    },
  ],
  create(context, [rawOptions]) {
    const options: Required<NoUntypedStringComparisonOptions> = {
      disallowAny: rawOptions.disallowAny ?? true,
      disallowUnknown: rawOptions.disallowUnknown ?? false,
      allowEmptyString: rawOptions.allowEmptyString ?? true,
    };

    const parserServices = ESLintUtils.getParserServices(context);
    const checker = parserServices.program.getTypeChecker();

    function checkComparison(
      reportNode: TSESTree.Node,
      variableNode: TSESTree.Node,
      literalValue: string
    ): void {
      if (options.allowEmptyString && literalValue === '') {
        return;
      }

      const tsNode = parserServices.esTreeNodeToTSNodeMap.get(variableNode);
      const type = checker.getTypeAtLocation(tsNode);
      const messageId = classifyDisallowedType(type, checker, options);

      if (messageId) {
        context.report({
          node: reportNode,
          messageId,
          data: { literal: literalValue },
        });
      }
    }

    return {
      BinaryExpression(node) {
        if (!EQUALITY_OPERATORS.has(node.operator)) {
          return;
        }

        const leftLiteral = extractStaticString(node.left);
        const rightLiteral = extractStaticString(node.right);

        if (leftLiteral !== null && rightLiteral === null) {
          checkComparison(node, node.right, leftLiteral);
        } else if (rightLiteral !== null && leftLiteral === null) {
          checkComparison(node, node.left, rightLiteral);
        }
      },

      SwitchCase(node) {
        if (!node.test || node.parent.type !== 'SwitchStatement') {
          return;
        }

        const caseLiteral = extractStaticString(node.test as StaticStringNode);
        if (caseLiteral === null) {
          return;
        }

        checkComparison(node, node.parent.discriminant, caseLiteral);
      },
    };
  },
});
