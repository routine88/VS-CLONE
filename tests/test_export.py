import json

from game.audio import AudioEngine
from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, SceneNode, Sprite


class RuntimeFrameStub:
    """Minimal runtime-side expectations for exported payloads."""

    def validate_render(self, payload):
        assert set(payload.keys()) == {"time", "viewport", "messages", "instructions"}
        assert isinstance(payload["time"], (int, float))
        assert len(payload["viewport"]) == 2
        assert isinstance(payload["messages"], list)
        for instruction in payload["instructions"]:
            self._validate_render_instruction(instruction)

    def validate_audio(self, payload):
        assert set(payload.keys()) == {"time", "effects", "music", "metadata"}
        assert isinstance(payload["time"], (int, float))
        assert isinstance(payload["metadata"], dict)
        for effect in payload["effects"]:
            clip = effect["clip"]
            assert set(clip.keys()) == {"id", "path", "volume"}
            assert isinstance(effect["volume"], (int, float))
            assert isinstance(effect["pan"], (int, float))
        for entry in payload["music"]:
            assert "action" in entry
            track = entry.get("track")
            if track is not None:
                assert set(track.keys()) == {"id", "path", "volume", "loop"}
            if "volume" in entry:
                assert isinstance(entry["volume"], (int, float))

    def validate_bundle(self, payload):
        assert "render" in payload
        self.validate_render(payload["render"])
        if "audio" in payload:
            self.validate_audio(payload["audio"])

    def _validate_render_instruction(self, instruction):
        assert "node_id" in instruction
        sprite = instruction["sprite"]
        assert set(sprite.keys()) == {"id", "texture", "size", "pivot", "tint"}
        assert len(instruction["position"]) == 2
        assert isinstance(instruction["scale"], (int, float))
        assert isinstance(instruction["rotation"], (int, float))
        assert isinstance(instruction["flip_x"], bool)
        assert isinstance(instruction["flip_y"], bool)
        assert isinstance(instruction["layer"], str)
        assert isinstance(instruction["z_index"], int)
        assert isinstance(instruction["metadata"], dict)


def make_render_frame():
    graphics = GraphicsEngine(viewport=(800, 600))
    graphics.register_sprite(
        Sprite(
            id="custom/player",
            texture="sprites/custom_player.png",
            size=(64, 80),
            pivot=(0.5, 0.25),
            tint=(255, 200, 200),
        )
    )
    node = SceneNode(
        id="player",
        position=(4.0, 2.5),
        layer="actors",
        sprite_id="custom/player",
        metadata={"kind": "player", "debug": "export"},
    )
    return graphics.build_frame([node], time=1.25, messages=["tick"])


def make_audio_frame():
    audio = AudioEngine()
    return audio.build_frame(["combat.weapon_fire", "music.start"], time=1.25)


def test_render_export_serialises_payload():
    frame = make_render_frame()
    exporter = EngineFrameExporter()
    payload = exporter.render_payload(frame)
    stub = RuntimeFrameStub()
    stub.validate_render(payload)
    assert json.loads(exporter.render_json(frame)) == payload


def test_audio_export_serialises_payload():
    frame = make_audio_frame()
    exporter = EngineFrameExporter()
    payload = exporter.audio_payload(frame)
    stub = RuntimeFrameStub()
    stub.validate_audio(payload)
    assert json.loads(exporter.audio_json(frame)) == payload


def test_bundle_export_matches_unity_stub():
    render_frame = make_render_frame()
    audio_frame = make_audio_frame()
    exporter = EngineFrameExporter()
    payload = exporter.frame_bundle(render_frame=render_frame, audio_frame=audio_frame)
    stub = RuntimeFrameStub()
    stub.validate_bundle(payload)
    assert json.loads(exporter.bundle_json(render_frame=render_frame, audio_frame=audio_frame)) == payload
