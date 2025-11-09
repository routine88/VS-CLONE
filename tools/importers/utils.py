"""Utility helpers shared by importer modules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Tuple
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .models import BundleMetadata, ImportReport, ResourceRecord

BUNDLE_VERSION = "1.0"
_ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def sha256_digest(data: bytes) -> str:
    """Return the SHA-256 digest for *data* as a hex string."""

    return hashlib.sha256(data).hexdigest()


def build_resource_records(resources: Mapping[str, bytes]) -> Iterable[ResourceRecord]:
    """Generate :class:`ResourceRecord` entries for the bundle manifest."""

    for path in sorted(resources):
        payload = resources[path]
        yield ResourceRecord(path=path, sha256=sha256_digest(payload), size=len(payload))


def write_bundle(
    bundle_dir: Path,
    metadata: BundleMetadata,
    resources: Mapping[str, bytes],
) -> Tuple[Path, Path, Iterable[ResourceRecord]]:
    """Persist *resources* and *metadata* into a deterministic bundle archive."""

    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_name = f"{metadata.asset_name}.bundle.zip"
    bundle_path = bundle_dir / bundle_name
    manifest_path = bundle_dir / f"{metadata.asset_name}.bundle.json"

    resource_records = list(build_resource_records(resources))

    # Ensure deterministic compression output by writing each entry manually with
    # a fixed timestamp.
    with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as zf:
        for record in resource_records:
            info = ZipInfo(filename=record.path, date_time=_ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            zf.writestr(info, resources[record.path])

    bundle_descriptor = {
        "bundle_version": BUNDLE_VERSION,
        "asset_name": metadata.asset_name,
        "asset_type": metadata.asset_type,
        "source": metadata.source,
        "bundle": bundle_name,
        "metadata": {
            "unit_scale_meters": metadata.unit_scale_meters,
            "mesh_count": metadata.mesh_count,
            "material_count": metadata.material_count,
            "textures": metadata.textures,
            "extra": metadata.extra,
        },
        "resources": [record.__dict__ for record in resource_records],
        "bundle_sha256": sha256_digest(bundle_path.read_bytes()),
    }

    manifest_path.write_text(json.dumps(bundle_descriptor, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return manifest_path, bundle_path, resource_records


def normalise_unit_scale(value: float) -> float:
    """Round the provided unit scale to four decimal places for stability."""

    return round(float(value), 4)


def validate_unit_scale(unit_scale: float, source: Path) -> None:
    """Ensure the provided unit scale is within ±5% of 1.0."""

    if not 0.95 <= unit_scale <= 1.05:
        raise ValueError(
            f"{source.name}: unit scale {unit_scale:.3f} is outside the 1m ±5% budget"
        )
