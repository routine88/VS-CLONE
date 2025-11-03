"""Export the audio routing manifest to aid external clients of the runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from game.audio import AudioEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the AudioEngine manifest as JSON for integration tooling."
    )
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
    """Return the current AudioEngine manifest as a JSON string."""

    engine = AudioEngine()
    manifest = engine.build_manifest().to_dict()
    if compact:
        return json.dumps(manifest, separators=(",", ":"), sort_keys=True)
    return json.dumps(manifest, indent=indent, sort_keys=True)


def main(argv: Any | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload = dump_manifest(indent=args.indent, compact=args.compact)

    if args.output:
        args.output.write_text(payload + ("" if args.compact else "\n"))
    else:
        print(payload)


if __name__ == "__main__":
    main()
