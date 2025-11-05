"""Validation checks for the graphics asset manifest."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from game.graphics_assets import load_asset_manifest

ASSET_ROOT = Path("assets/graphics_assets")
SKIP_ENV_VAR = "VS_SKIP_OPTIONAL_ART_PACK_VALIDATION"


@pytest.mark.skipif(os.getenv(SKIP_ENV_VAR), reason="Optional art pack not installed; skipping validation.")
def test_graphics_assets_manifest_has_no_warnings() -> None:
    """Ensure manifest.validate_assets does not emit warnings."""

    manifest = load_asset_manifest(ASSET_ROOT / "manifest.json")
    warnings = manifest.validate_assets(ASSET_ROOT)
    assert not warnings, f"asset validation emitted warnings: {warnings}"
