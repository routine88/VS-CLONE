"""High-level orchestration for the asset import pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from .errors import ImporterError
from .fbx import FBXImporter
from .gltf import GLTFImporter
from .models import ImportReport

LOGGER = logging.getLogger(__name__)

_IMPORTERS = {
    ".fbx": FBXImporter(),
    ".gltf": GLTFImporter(),
}


def discover_assets(source_root: Path) -> Iterable[Path]:
    """Yield source files underneath *source_root* that can be imported."""

    for suffix in _IMPORTERS:
        yield from source_root.rglob(f"*{suffix}")


def import_asset(source_root: Path, output_root: Path, source: Path) -> ImportReport:
    """Import a single asset and return the resulting report."""

    importer = _IMPORTERS.get(source.suffix.lower())
    if importer is None:
        raise ImporterError(f"No importer registered for {source.suffix}")

    relative_dir = source.relative_to(source_root).parent
    bundle_dir = output_root / relative_dir / source.stem

    LOGGER.info("Importing %s", source)
    return importer.import_file(source=source, bundle_dir=bundle_dir, source_root=source_root)


def import_all(source_root: Path, output_root: Path) -> List[ImportReport]:
    """Run the importer for every supported asset inside *source_root*."""

    source_root = source_root.resolve()
    output_root = output_root.resolve()

    if not source_root.exists():
        raise ImporterError(f"Source directory '{source_root}' does not exist")

    reports: List[ImportReport] = []

    for asset in sorted(discover_assets(source_root)):
        reports.append(import_asset(source_root=source_root, output_root=output_root, source=asset))

    return reports
