import json

from game.audio import (
    AudioEngine,
    SoundClip,
    DEFAULT_AUDIO_CUE_TABLE,
    default_audio_cue_table,
)
from tools.audio_manifest import dump_manifest


def test_audio_engine_placeholders_and_bindings():
    audio = AudioEngine()
    frame = audio.build_frame(["ui.level_up", "music.start"], time=0.0)
    effect_ids = [instruction.clip.id for instruction in frame.effects]
    assert "effects/ui.prompt" in effect_ids
    music_actions = [(instruction.track.id, instruction.action) for instruction in frame.music]
    assert ("music.dusk_theme", "play") in music_actions

    follow_up = audio.build_frame(["music.start"], time=1.0)
    assert any(instr.action == "refresh" for instr in follow_up.music)


def test_audio_engine_player_dash_event():
    audio = AudioEngine()
    frame = audio.build_frame(["player.dash"], time=0.5)
    assert any(instruction.clip.id == "effects/player.dash" for instruction in frame.effects)


def test_audio_engine_custom_bindings_override_defaults():
    audio = AudioEngine()
    custom = SoundClip(id="custom.clip", path="audio/custom.ogg", volume=0.5)
    audio.register_effect(custom)
    audio.bind_effect("custom.event", "custom.clip")
    frame = audio.build_frame(["custom.event"], time=2.0)
    assert any(instr.clip.id == "custom.clip" for instr in frame.effects)


def test_audio_engine_environment_audio_cues():
    audio = AudioEngine()
    frame = audio.build_frame(
        [
            "environment.hazard",
            "environment.salvage",
            "environment.weather.change",
            "environment.weather.clear",
        ],
        time=3.0,
    )
    ids = {instruction.clip.id for instruction in frame.effects}
    assert ids == {
        "effects/environment.hazard",
        "effects/environment.salvage",
        "effects/environment.weather_change",
        "effects/environment.weather_clear",
    }


def test_audio_manifest_export_includes_routes():
    audio = AudioEngine()
    manifest = audio.build_manifest().to_dict()

    assert "effects/environment.hazard" in manifest["effects"]
    hazard = manifest["effects"]["effects/environment.hazard"]
    assert hazard["description"]
    assert hazard["path"].endswith(".wav")
    assert "environment" in hazard.get("tags", [])

    assert "music.dusk_theme" in manifest["music"]
    dusk = manifest["music"]["music.dusk_theme"]
    assert dusk["loop"] is True
    assert dusk.get("tempo_bpm") == 96
    assert "environment.hazard" in manifest["event_effects"]
    assert manifest["event_effects"]["environment.hazard"] == [
        "effects/environment.hazard"
    ]


def test_audio_manifest_cli_dump_round_trip():
    payload = dump_manifest()
    data = json.loads(payload)
    assert data["event_music"]["music.start"] == ["music.dusk_theme"]


def test_default_audio_cue_table_matches_manifest():
    audio = AudioEngine()
    manifest = audio.build_manifest().to_dict()

    expected_effects = {
        effect_id: {"path": entry["path"], "volume": entry["volume"]}
        for effect_id, entry in DEFAULT_AUDIO_CUE_TABLE["effects"].items()
    }
    expected_music = {
        track_id: {
            "path": entry["path"],
            "volume": entry["volume"],
            "loop": entry["loop"],
        }
        for track_id, entry in DEFAULT_AUDIO_CUE_TABLE["music"].items()
    }
    expected_event_effects = {
        event: list(routes)
        for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_effects"].items()
    }
    expected_event_music = {
        event: list(routes)
        for event, routes in DEFAULT_AUDIO_CUE_TABLE["event_music"].items()
    }

    assert manifest["effects"] == expected_effects
    assert manifest["music"] == expected_music
    assert manifest["event_effects"] == expected_event_effects
    assert manifest["event_music"] == expected_event_music


def test_default_audio_cue_table_returns_copy():
    table = default_audio_cue_table()
    table["effects"]["effects/ui.confirm"]["volume"] = 0.1

    fresh = default_audio_cue_table()
    assert (
        fresh["effects"]["effects/ui.confirm"]["volume"]
        == DEFAULT_AUDIO_CUE_TABLE["effects"]["effects/ui.confirm"]["volume"]
    )
