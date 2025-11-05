"""Validation checks for placeholder audio assets."""

from __future__ import annotations

import json
import wave
from pathlib import Path

from game.audio import materialise_audio_manifest_assets

AUDIO_ROOT = Path("assets")
MANIFEST_PATH = AUDIO_ROOT / "audio" / "manifest.json"


def test_audio_manifest_files_exist_and_match_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    materialise_audio_manifest_assets(manifest, asset_root=AUDIO_ROOT)
    effects = {entry["id"]: entry for entry in manifest.get("effects", [])}
    music = {entry["id"]: entry for entry in manifest.get("music", [])}

    for entry in effects.values():
        clip_path = AUDIO_ROOT / entry["path"]
        assert clip_path.exists(), f"missing audio file for {entry['id']}: {clip_path}"
        with wave.open(str(clip_path), "rb") as handle:
            assert handle.getnframes() > 0, f"zero-length audio clip for {entry['id']}"

    for entry in music.values():
        clip_path = AUDIO_ROOT / entry["path"]
        assert clip_path.exists(), f"missing music file for {entry['id']}: {clip_path}"
        with wave.open(str(clip_path), "rb") as handle:
            assert handle.getnframes() > 0, f"zero-length music track for {entry['id']}"

    for event, ids in manifest.get("event_effects", {}).items():
        for effect_id in ids:
            assert (
                effect_id in effects
            ), f"event {event!r} references unknown effect {effect_id!r}"

    for event, ids in manifest.get("event_music", {}).items():
        for track_id in ids:
            assert (
                track_id in music
            ), f"event {event!r} references unknown music track {track_id!r}"
