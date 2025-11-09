"""Helpers that surface the baseline asset bundles shipped with the repo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class BaselineLevelAssets:
    """Container describing the default character and environment bundles."""

    name: str
    environment_bundle: Path
    character_bundle: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_baseline_assets(root: Path | None = None) -> BaselineLevelAssets:
    """Return the baseline level bundle references."""

    root = root or _repo_root()
    generated = root / "assets" / "generated"
    environment_bundle = generated / "environments" / "baseline_arena" / "baseline_arena.bundle.json"
    character_bundle = generated / "characters" / "baseline_character" / "baseline_character.bundle.json"

    return BaselineLevelAssets(
        name="Baseline Hangar",
        environment_bundle=environment_bundle,
        character_bundle=character_bundle,
    )


def load_bundle_manifest(bundle_path: Path) -> Dict[str, Any]:
    """Load a generated bundle manifest from disk."""

    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    data["bundle_path"] = str(bundle_path)
    return data


BASELINE_LEVEL = get_baseline_assets()
