#!/usr/bin/env python3
"""Audit translator keys used in the code base against the localization catalog."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Iterable, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from game.localization import default_catalog


class _TranslateCallVisitor(ast.NodeVisitor):
    """Collect string literals passed to ``Translator.translate``."""

    def __init__(self) -> None:
        self.keys: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - required by ast.NodeVisitor
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "translate":
            key = self._extract_key(node)
            if key is not None:
                self.keys.add(key)
        self.generic_visit(node)

    @staticmethod
    def _extract_key(node: ast.Call) -> str | None:
        if node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                return first.value
        for keyword in node.keywords:
            if keyword.arg == "key" and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    return keyword.value.value
        return None


def _iter_source_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def collect_translator_keys(root: Path) -> Set[str]:
    visitor = _TranslateCallVisitor()
    for path in _iter_source_files(root):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - unlikely during tests
            print(f"warning: unable to read {path}: {exc}", file=sys.stderr)
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            print(f"warning: unable to parse {path}: {exc}", file=sys.stderr)
            continue
        visitor.visit(tree)
    return visitor.keys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="game",
        type=Path,
        help="Root directory to scan for translator calls (default: game)",
    )
    parser.add_argument(
        "--base-language",
        default="en",
        help="Language that must contain every string (default: en)",
    )
    parser.add_argument(
        "--fail-unused",
        action="store_true",
        help="Exit with a non-zero status when unused catalog entries are found",
    )
    args = parser.parse_args(argv)

    source_dir = (Path.cwd() / args.source).resolve()
    if not source_dir.exists():
        parser.error(f"source directory not found: {source_dir}")

    keys_in_code = collect_translator_keys(source_dir)
    catalog = default_catalog()

    try:
        base_entries = set(catalog.language_entries(args.base_language))
    except KeyError as exc:
        parser.error(str(exc))

    missing_in_base = sorted(keys_in_code - base_entries)
    unused_in_base = sorted(base_entries - keys_in_code)

    exit_code = 0
    if missing_in_base:
        print(f"Missing keys in language '{args.base_language}':")
        for key in missing_in_base:
            print(f"  - {key}")
        exit_code = 1

    if unused_in_base:
        message = f"Unused keys in language '{args.base_language}':"
        print(message)
        for key in unused_in_base:
            print(f"  - {key}")
        if args.fail_unused:
            exit_code = 1

    for language in catalog.available_languages():
        if language == args.base_language:
            continue
        entries = set(catalog.language_entries(language))
        missing = sorted(keys_in_code - entries)
        if missing:
            print(f"Keys missing in '{language}' (will fall back to {args.base_language}):")
            for key in missing:
                print(f"  - {key}")

    if exit_code == 0:
        print("All translator keys accounted for in the catalog.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
