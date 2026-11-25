"""Deterministic AST & line-count hygiene gate for Python files."""

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 300
EXCLUDED_LINE_LIMIT_FILES = {
    Path("app/db.py"),
    Path("app/exporters/pdf_exporter.py"),
    Path("proxy_pool/rotator.py"),
}
TARGET_DIRS = ("app", "proxy_pool", "tests", "scripts")


class _SingleLetterVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def _check_name(self, name: str, lineno: int) -> None:
        if len(name) == 1 and name.isalpha():
            self.violations.append((lineno, name))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_arguments(node.args)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_arguments(node.args)
        self.generic_visit(node)

    def _check_arguments(self, args: ast.arguments) -> None:
        all_args = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        if args.vararg:
            all_args.append(args.vararg)
        if args.kwarg:
            all_args.append(args.kwarg)
        for arg in all_args:
            self._check_name(arg.arg, arg.lineno)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self._check_name(node.id, node.lineno)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._check_name(node.name, node.lineno)
        self.generic_visit(node)

    def visit_alias(self, node: ast.alias) -> None:
        if node.asname:
            self._check_name(node.asname, node.lineno)


def main() -> int:
    root = Path.cwd()
    errors: list[str] = []

    for folder in TARGET_DIRS:
        base = root / folder
        if not base.exists():
            continue
        for py_file in sorted(base.rglob("*.py")):
            rel = py_file.relative_to(root)
            source = py_file.read_text(encoding="utf-8")
            line_count = len(source.splitlines())

            if rel not in EXCLUDED_LINE_LIMIT_FILES and line_count > MAX_FILE_LINES:
                errors.append(f"{rel}: {line_count} lines exceeds max {MAX_FILE_LINES} lines (god-file ban)")

            tree = ast.parse(source, filename=str(rel))
            visitor = _SingleLetterVisitor()
            visitor.visit(tree)
            for lineno, ident in visitor.violations:
                errors.append(f"{rel}:{lineno}: single-letter variable '{ident}' is forbidden")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("Python hygiene check passed (0 single-letter vars, 0 oversized files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
