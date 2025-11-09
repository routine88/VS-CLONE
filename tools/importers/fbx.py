"""Importer for Autodesk FBX files."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List

from .errors import ImporterError
from .models import BundleMetadata, ImportReport
from .utils import normalise_unit_scale, validate_unit_scale, write_bundle

LOGGER = logging.getLogger(__name__)

_UNIT_SCALE_RE = re.compile(r"UnitScaleFactor" r"[^0-9]*" r"([0-9]+(?:\.[0-9]+)?)")
_GEOMETRY_RE = re.compile(r"Geometry::")
_MATERIAL_RE = re.compile(r"Material::")


class FBXImporter:
    """Convert FBX meshes into deterministic bundle archives."""

    asset_type = "fbx"

    def import_file(self, source: Path, bundle_dir: Path, source_root: Path) -> ImportReport:
        sidecar_path = Path(f"{source}.import.json")
        sidecar_data = self._load_sidecar(sidecar_path)

        text = source.read_text(encoding="utf-8", errors="ignore")
        unit_scale = self._resolve_unit_scale(text=text, sidecar=sidecar_data, source=source)
        mesh_count = sidecar_data.get("mesh_count") or len(_GEOMETRY_RE.findall(text)) or 1
        material_count = sidecar_data.get("material_count") or len(_MATERIAL_RE.findall(text)) or 1

        textures = self._collect_textures(source=source, sidecar=sidecar_data)
        resources: Dict[str, bytes] = {
            f"meshes/{source.name}": source.read_bytes(),
        }
        warnings: List[str] = []

        for texture in textures:
            texture_path = (source.parent / texture).resolve()
            if not texture_path.exists():
                warnings.append(f"Missing texture '{texture}' referenced by {source.name}")
                continue
            resources[f"textures/{texture_path.name}"] = texture_path.read_bytes()

        metadata = BundleMetadata(
            asset_name=source.stem,
            asset_type=self.asset_type,
            source=str(source.relative_to(source_root)),
            unit_scale_meters=unit_scale,
            mesh_count=mesh_count,
            material_count=material_count,
            textures=sorted([Path(texture).name for texture in textures]),
            extra={
                "category": sidecar_data.get("category", source.parent.name),
                "sidecar": bool(sidecar_data),
                "notes": sidecar_data.get("notes", []),
            },
        )

        manifest_path, bundle_path, resource_records = write_bundle(
            bundle_dir=bundle_dir,
            metadata=metadata,
            resources=resources,
        )

        return ImportReport(
            source=source,
            bundle_dir=bundle_dir,
            bundle_manifest=manifest_path,
            bundle_archive=bundle_path,
            metadata=metadata,
            resources=resource_records,
            warnings=warnings,
        )

    def _load_sidecar(self, sidecar: Path) -> Dict[str, object]:
        if not sidecar.exists():
            return {}
        LOGGER.debug("Loading FBX sidecar %s", sidecar)
        try:
            return json.loads(sidecar.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ImporterError(f"Invalid sidecar JSON: {sidecar}") from exc

    def _resolve_unit_scale(self, text: str, sidecar: Dict[str, object], source: Path) -> float:
        if "unit_scale_meters" in sidecar:
            unit_scale = normalise_unit_scale(sidecar["unit_scale_meters"])
        else:
            match = _UNIT_SCALE_RE.search(text)
            if not match:
                LOGGER.warning("%s: falling back to default unit scale", source.name)
                unit_scale = 1.0
            else:
                unit_scale = normalise_unit_scale(match.group(1))

        try:
            validate_unit_scale(unit_scale, source)
        except ValueError as exc:
            raise ImporterError(str(exc)) from exc
        return unit_scale

    def _collect_textures(self, source: Path, sidecar: Dict[str, object]) -> List[str]:
        raw_textures = sidecar.get("textures") or []
        if isinstance(raw_textures, dict):
            values: Iterable[str] = raw_textures.values()
        else:
            values = raw_textures
        unique: List[str] = []
        for value in values:
            tex = str(value)
            if tex not in unique:
                unique.append(tex)
        return unique
