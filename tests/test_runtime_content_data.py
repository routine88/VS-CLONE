from __future__ import annotations

import json
from pathlib import Path

from game.content_exports import build_content_bundle
from native.client import ContentBundleDTO

RUNTIME_BUNDLE_PATH = Path("native/runtime/data/content_bundle.json")


def test_runtime_content_bundle_matches_export_functions():
    expected = build_content_bundle()
    payload = json.loads(RUNTIME_BUNDLE_PATH.read_text(encoding="utf-8"))
    assert payload == expected

    bundle = ContentBundleDTO.from_dict(payload)
    assert bundle.biomes
    assert bundle.relics
    assert bundle.progression.run_duration_seconds == expected["progression"]["run_duration_seconds"]
