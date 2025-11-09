"""Command line entry-point for the asset import pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable

from .errors import ImporterError
from .models import ImportReport
from .pipeline import import_all

LOGGER = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def _summarise(reports: Iterable[ImportReport]) -> None:
    for report in reports:
        LOGGER.info("%s -> %s", report.source.name, report.bundle_manifest)
        for warning in report.warnings:
            LOGGER.warning("%s", warning)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import FBX/GLTF assets into engine bundles")
    parser.add_argument("--source", type=Path, default=Path("assets/source"), help="Source asset directory")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/generated"),
        help="Destination directory for generated bundles",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Treat importer warnings as fatal errors",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    _configure_logging(verbose=args.verbose)

    try:
        reports = import_all(source_root=args.source, output_root=args.output)
    except ImporterError as exc:
        LOGGER.error("%s", exc)
        return 1

    _summarise(reports)

    warnings = [warning for report in reports for warning in report.warnings]
    if warnings and args.fail_on_warn:
        LOGGER.error("Importer warnings were treated as errors")
        return 2

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
