from __future__ import annotations

"""CLI helper for exporting the graphics manifest."""

import argparse
import json
from pathlib import Path
from typing import Any

from game.graphics import GraphicsEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export the GraphicsEngine manifest as JSON.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional file path to write the manifest JSON to instead of stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation to use when pretty-printing JSON (default: 2).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without whitespace (overrides --indent).",
    )
    return parser


def dump_manifest(*, indent: int = 2, compact: bool = False) -> str:
    """Return the current GraphicsEngine manifest as a JSON string."""

    engine = GraphicsEngine()
    manifest = engine.build_manifest().to_dict()
    if compact:
        return json.dumps(manifest, separators=(",", ":"), sort_keys=True)
    return json.dumps(manifest, indent=indent, sort_keys=True)


def main(argv: Any | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    json_payload = dump_manifest(indent=args.indent, compact=args.compact)

    if args.output:
        args.output.write_text(json_payload + ("" if args.compact else "\n"))
    else:
        print(json_payload)


if __name__ == "__main__":
    main()
