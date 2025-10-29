from game.audio import AudioEngine, SoundClip


def test_audio_engine_placeholders_and_bindings():
    audio = AudioEngine()
    frame = audio.build_frame(["ui.level_up", "music.start"], time=0.0)
    effect_ids = [instruction.clip.id for instruction in frame.effects]
    assert "effects/ui.prompt" in effect_ids
    music_actions = [(instruction.track.id, instruction.action) for instruction in frame.music]
    assert ("music.dusk_theme", "play") in music_actions

    follow_up = audio.build_frame(["music.start"], time=1.0)
    assert any(instr.action == "refresh" for instr in follow_up.music)


def test_audio_engine_custom_bindings_override_defaults():
    audio = AudioEngine()
    custom = SoundClip(id="custom.clip", path="audio/custom.ogg", volume=0.5)
    audio.register_effect(custom)
    audio.bind_effect("custom.event", "custom.clip")
    frame = audio.build_frame(["custom.event"], time=2.0)
    assert any(instr.clip.id == "custom.clip" for instr in frame.effects)
