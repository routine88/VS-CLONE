"""Importer for GLTF scene files."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .errors import ImporterError
from .models import BundleMetadata, ImportReport
from .utils import normalise_unit_scale, validate_unit_scale, write_bundle

LOGGER = logging.getLogger(__name__)


class GLTFImporter:
    """Convert GLTF files into deterministic bundle archives."""

    asset_type = "gltf"

    def import_file(self, source: Path, bundle_dir: Path, source_root: Path) -> ImportReport:
        try:
            gltf = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ImporterError(f"Invalid GLTF JSON: {source}") from exc

        unit_scale = normalise_unit_scale(gltf.get("asset", {}).get("unitScaleFactor", 1.0))
        try:
            validate_unit_scale(unit_scale, source)
        except ValueError as exc:
            raise ImporterError(str(exc)) from exc

        mesh_count = len(gltf.get("meshes", [])) or 1
        material_count = len(gltf.get("materials", [])) or 1

        textures, texture_payloads = self._collect_images(source, gltf)
        buffers, buffer_payloads = self._collect_buffers(source, gltf)

        resources: Dict[str, bytes] = {f"meshes/{source.name}": source.read_bytes()}
        warnings: List[str] = []

        for rel_path, payload in {**texture_payloads, **buffer_payloads}.items():
            if payload is None:
                warnings.append(f"Missing resource '{rel_path}' referenced by {source.name}")
                continue
            resources[rel_path] = payload

        metadata = BundleMetadata(
            asset_name=source.stem,
            asset_type=self.asset_type,
            source=str(source.relative_to(source_root)),
            unit_scale_meters=unit_scale,
            mesh_count=mesh_count,
            material_count=material_count,
            textures=sorted(Path(tex).name for tex in textures),
            extra={
                "default_scene": gltf.get("scene"),
                "animations": len(gltf.get("animations", [])),
                "skins": len(gltf.get("skins", [])),
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

    def _collect_images(
        self, source: Path, gltf: Dict[str, object]
    ) -> Tuple[List[str], Dict[str, bytes | None]]:
        textures: List[str] = []
        payloads: Dict[str, bytes | None] = {}
        for image in gltf.get("images", []) or []:
            uri = image.get("uri")
            if not uri:
                continue
            textures.append(uri)
            rel_path = f"textures/{Path(uri).name}"
            payloads[rel_path] = self._resolve_uri(source.parent, uri)
        return textures, payloads

    def _collect_buffers(
        self, source: Path, gltf: Dict[str, object]
    ) -> Tuple[List[str], Dict[str, bytes | None]]:
        buffers: List[str] = []
        payloads: Dict[str, bytes | None] = {}
        for buffer in gltf.get("buffers", []) or []:
            uri = buffer.get("uri")
            if not uri:
                continue
            buffers.append(uri)
            rel_path = f"buffers/{Path(uri).name}"
            payloads[rel_path] = self._resolve_uri(source.parent, uri)
        return buffers, payloads

    def _resolve_uri(self, root: Path, uri: str) -> bytes | None:
        if uri.startswith("data:"):
            try:
                payload = uri.split(",", 1)[1]
            except IndexError:  # pragma: no cover - defensive
                LOGGER.warning("Malformed data URI: %s", uri)
                return None
            return base64.b64decode(payload)

        resolved = (root / uri).resolve()
        if not resolved.exists():
            LOGGER.warning("Missing external resource %s", resolved)
            return None
        return resolved.read_bytes()
