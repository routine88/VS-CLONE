"""Utilities for exporting prototype frames to JSON for the in-house runtime."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional

from .audio import AudioFrame, MusicInstruction, SoundInstruction
from .graphics import RenderFrame, RenderInstruction, Sprite


class EngineFrameExporter:
    """Serialize render and audio frames into runtime-friendly JSON payloads."""

    def render_payload(self, frame: RenderFrame) -> Dict[str, Any]:
        """Return a JSON-serialisable dict describing a :class:`RenderFrame`."""

        return {
            "time": frame.time,
            "viewport": list(frame.viewport),
            "messages": list(frame.messages),
            "instructions": [self._render_instruction_payload(instr) for instr in frame.instructions],
        }

    def audio_payload(self, frame: AudioFrame) -> Dict[str, Any]:
        """Return a JSON-serialisable dict describing an :class:`AudioFrame`."""

        return {
            "time": frame.time,
            "effects": [self._effect_payload(effect) for effect in frame.effects],
            "music": [self._music_payload(entry) for entry in frame.music],
            "metadata": dict(frame.metadata),
        }

    def frame_bundle(
        self,
        *,
        render_frame: RenderFrame,
        audio_frame: Optional[AudioFrame] = None,
    ) -> Dict[str, Any]:
        """Combine render and audio data into a single payload."""

        payload: Dict[str, Any] = {"render": self.render_payload(render_frame)}
        if audio_frame is not None:
            payload["audio"] = self.audio_payload(audio_frame)
        return payload

    def render_json(self, frame: RenderFrame, *, sort_keys: bool = True) -> str:
        """Dump a :class:`RenderFrame` to JSON."""

        return json.dumps(self.render_payload(frame), sort_keys=sort_keys, separators=(",", ":"))

    def audio_json(self, frame: AudioFrame, *, sort_keys: bool = True) -> str:
        """Dump an :class:`AudioFrame` to JSON."""

        return json.dumps(self.audio_payload(frame), sort_keys=sort_keys, separators=(",", ":"))

    def bundle_json(
        self,
        *,
        render_frame: RenderFrame,
        audio_frame: Optional[AudioFrame] = None,
        sort_keys: bool = True,
    ) -> str:
        """Dump the combined render/audio payload to JSON."""

        return json.dumps(
            self.frame_bundle(render_frame=render_frame, audio_frame=audio_frame),
            sort_keys=sort_keys,
            separators=(",", ":"),
        )

    def _render_instruction_payload(self, instruction: RenderInstruction) -> Dict[str, Any]:
        return {
            "node_id": instruction.node_id,
            "sprite": self._sprite_payload(instruction.sprite),
            "position": list(instruction.position),
            "scale": instruction.scale,
            "rotation": instruction.rotation,
            "flip_x": instruction.flip_x,
            "flip_y": instruction.flip_y,
            "layer": instruction.layer,
            "z_index": instruction.z_index,
            "metadata": self._metadata_payload(instruction.metadata),
        }

    def _sprite_payload(self, sprite: Sprite) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": sprite.id,
            "texture": sprite.texture,
            "size": list(sprite.size),
            "pivot": list(sprite.pivot),
        }
        if sprite.tint is not None:
            payload["tint"] = list(sprite.tint)
        else:
            payload["tint"] = None
        return payload

    def _metadata_payload(self, metadata: Mapping[str, object]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key, value in metadata.items():
            payload[key] = value
        return payload

    def _effect_payload(self, instruction: SoundInstruction) -> Dict[str, Any]:
        return {
            "clip": {
                "id": instruction.clip.id,
                "path": instruction.clip.path,
                "volume": instruction.clip.volume,
            },
            "volume": instruction.volume,
            "pan": instruction.pan,
        }

    def _music_payload(self, instruction: MusicInstruction) -> Dict[str, Any]:
        track_payload: Optional[Dict[str, Any]]
        if instruction.track is None:
            track_payload = None
        else:
            track_payload = {
                "id": instruction.track.id,
                "path": instruction.track.path,
                "volume": instruction.track.volume,
                "loop": instruction.track.loop,
            }
        payload: Dict[str, Any] = {
            "track": track_payload,
            "action": instruction.action,
        }
        if instruction.volume is not None:
            payload["volume"] = instruction.volume
        return payload


__all__ = ["EngineFrameExporter"]
