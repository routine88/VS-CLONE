"""Export structured content payloads for the native runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from game.content_exports import build_content_bundle

DEFAULT_OUTPUT = Path("native/runtime/data/content_bundle.json")


def export_runtime_content(path: Path) -> Path:
    """Write the combined content bundle to *path*."""

    payload = build_content_bundle()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Destination path for the JSON bundle (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    export_runtime_content(args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
