"""Dataclasses shared by the importer implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class ResourceRecord:
    """Describes a single file embedded in a generated bundle."""

    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class BundleMetadata:
    """Metadata describing the converted asset."""

    asset_name: str
    asset_type: str
    source: str
    unit_scale_meters: float
    mesh_count: int
    material_count: int
    textures: List[str]
    extra: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportReport:
    """Summary returned by an importer after producing a bundle."""

    source: Path
    bundle_dir: Path
    bundle_manifest: Path
    bundle_archive: Path
    metadata: BundleMetadata
    resources: Iterable[ResourceRecord]
    warnings: List[str] = field(default_factory=list)
