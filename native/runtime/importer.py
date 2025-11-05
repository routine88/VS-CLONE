"""JSON importer that materialises exported frames for the native runtime."""

from __future__ import annotations

import json
import logging
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

from game.audio import AudioFrame, MusicInstruction, MusicTrack, SoundClip, SoundInstruction
from game.graphics import RenderFrame, RenderInstruction, Sprite

LOGGER = logging.getLogger(__name__)

Vector2 = Tuple[float, float]
Color = Tuple[int, int, int]


class EngineFrameImporter:
    """Rehydrate render and audio frames exported by the prototype."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or LOGGER
        self._sprites: Dict[str, Sprite] = {}
        self._effects: Dict[str, SoundClip] = {}
        self._music: Dict[str, MusicTrack] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render_frame(self, payload: Mapping[str, Any]) -> RenderFrame:
        """Convert a render payload produced by :class:`EngineFrameExporter`."""

        time = float(payload.get("time", 0.0))
        viewport_payload = payload.get("viewport", (0, 0))
        viewport = (
            int(viewport_payload[0]),
            int(viewport_payload[1]),
        )
        instructions_payload = payload.get("instructions", [])
        instructions = tuple(
            self._render_instruction(entry)
            for entry in instructions_payload  # type: ignore[arg-type]
        )
        messages_payload = payload.get("messages", [])
        messages = tuple(str(message) for message in messages_payload)
        return RenderFrame(
            time=time,
            viewport=viewport,
            instructions=instructions,
            messages=messages,
        )

    def render_frame_from_json(self, payload: str) -> RenderFrame:
        """Parse JSON text and return a :class:`RenderFrame`."""

        data: Dict[str, Any] = json.loads(payload)
        return self.render_frame(data)

    def audio_frame(self, payload: Mapping[str, Any]) -> AudioFrame:
        """Convert an audio payload produced by :class:`EngineFrameExporter`."""

        time = float(payload.get("time", 0.0))
        effects_payload = payload.get("effects", [])
        music_payload = payload.get("music", [])
        metadata_payload = payload.get("metadata", {})
        return AudioFrame(
            time=time,
            effects=tuple(
                self._sound_instruction(entry)
                for entry in effects_payload  # type: ignore[arg-type]
            ),
            music=tuple(
                self._music_instruction(entry)
                for entry in music_payload  # type: ignore[arg-type]
            ),
            metadata=dict(metadata_payload),
        )

    def audio_frame_from_json(self, payload: str) -> AudioFrame:
        """Parse JSON text and return an :class:`AudioFrame`."""

        data: Dict[str, Any] = json.loads(payload)
        return self.audio_frame(data)

    def frame_bundle(
        self, payload: Mapping[str, Any]
    ) -> Tuple[RenderFrame, Optional[AudioFrame]]:
        """Convert a combined render/audio payload into frame objects."""

        render_payload = payload.get("render")
        if render_payload is None:
            raise KeyError("frame bundle missing render payload")
        render_frame = self.render_frame(render_payload)
        audio_payload = payload.get("audio")
        audio_frame: Optional[AudioFrame]
        if audio_payload is None:
            audio_frame = None
        else:
            audio_frame = self.audio_frame(audio_payload)
        return render_frame, audio_frame

    def frame_bundle_from_json(self, payload: str) -> Tuple[RenderFrame, Optional[AudioFrame]]:
        """Parse JSON text describing a combined frame payload."""

        data: Dict[str, Any] = json.loads(payload)
        return self.frame_bundle(data)

    # ------------------------------------------------------------------
    # Lookup tables
    # ------------------------------------------------------------------
    @property
    def sprite_table(self) -> Mapping[str, Sprite]:
        """Snapshot of all sprites encountered during imports."""

        return MappingProxyType(self._sprites)

    @property
    def effect_table(self) -> Mapping[str, SoundClip]:
        """Snapshot of all effect clips encountered during imports."""

        return MappingProxyType(self._effects)

    @property
    def music_table(self) -> Mapping[str, MusicTrack]:
        """Snapshot of all music tracks encountered during imports."""

        return MappingProxyType(self._music)

    def clear_caches(self) -> None:
        """Forget any cached sprite/audio lookups."""

        self._sprites.clear()
        self._effects.clear()
        self._music.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _render_instruction(self, payload: Mapping[str, Any]) -> RenderInstruction:
        node_id = str(payload.get("node_id", ""))
        sprite_payload = payload.get("sprite", {})
        sprite = self._sprite(sprite_payload)

        position_payload = payload.get("position", (0.0, 0.0))
        position: Vector2 = (
            float(position_payload[0]),
            float(position_payload[1]),
        )
        metadata_payload = payload.get("metadata", {})
        return RenderInstruction(
            node_id=node_id,
            sprite=sprite,
            position=position,
            scale=float(payload.get("scale", 1.0)),
            rotation=float(payload.get("rotation", 0.0)),
            flip_x=bool(payload.get("flip_x", False)),
            flip_y=bool(payload.get("flip_y", False)),
            layer=str(payload.get("layer", "")),
            z_index=int(payload.get("z_index", 0)),
            metadata=dict(metadata_payload),
        )

    def _sprite(self, payload: Mapping[str, Any]) -> Sprite:
        sprite_id = str(payload.get("id", ""))
        texture = str(payload.get("texture", ""))
        size_payload = payload.get("size", (0, 0))
        size = (int(size_payload[0]), int(size_payload[1]))
        pivot_payload = payload.get("pivot", (0.0, 0.0))
        pivot: Vector2 = (
            float(pivot_payload[0]),
            float(pivot_payload[1]),
        )
        tint_payload = payload.get("tint")
        tint: Optional[Color]
        if tint_payload is None:
            tint = None
        else:
            tint = (
                int(tint_payload[0]),
                int(tint_payload[1]),
                int(tint_payload[2]),
            )

        candidate = Sprite(
            id=sprite_id or texture,
            texture=texture,
            size=size,
            pivot=pivot,
            tint=tint,
        )

        if sprite_id:
            cached = self._sprites.get(sprite_id)
            if cached is not None:
                if (
                    cached.texture != candidate.texture
                    or cached.size != candidate.size
                    or cached.pivot != candidate.pivot
                    or cached.tint != candidate.tint
                ):
                    self._logger.warning(
                        "Sprite payload for %s differs from cached value", sprite_id
                    )
                return cached
            self._sprites[sprite_id] = candidate
        return candidate

    def _sound_instruction(self, payload: Mapping[str, Any]) -> SoundInstruction:
        clip_payload = payload.get("clip", {})
        clip = self._sound_clip(clip_payload)
        return SoundInstruction(
            clip=clip,
            volume=float(payload.get("volume", 1.0)),
            pan=float(payload.get("pan", 0.0)),
        )

    def _sound_clip(self, payload: Mapping[str, Any]) -> SoundClip:
        clip_id = str(payload.get("id", ""))
        path = str(payload.get("path", ""))
        volume = float(payload.get("volume", 1.0))

        candidate = SoundClip(id=clip_id or path, path=path, volume=volume)

        if clip_id:
            cached = self._effects.get(clip_id)
            if cached is not None:
                if (
                    cached.path != candidate.path
                    or abs(cached.volume - candidate.volume) > 1e-9
                ):
                    self._logger.warning(
                        "Sound clip payload for %s differs from cached value", clip_id
                    )
                return cached
            self._effects[clip_id] = candidate
        return candidate

    def _music_instruction(self, payload: Mapping[str, Any]) -> MusicInstruction:
        track_payload = payload.get("track")
        track = self._music_track(track_payload) if track_payload is not None else None
        volume: Optional[float]
        if "volume" in payload and payload["volume"] is not None:
            volume = float(payload["volume"])
        else:
            volume = None
        return MusicInstruction(
            track=track,
            action=str(payload.get("action", "")),
            volume=volume,
        )

    def _music_track(self, payload: Mapping[str, Any]) -> MusicTrack:
        track_id = str(payload.get("id", ""))
        path = str(payload.get("path", ""))
        volume = float(payload.get("volume", 1.0))
        loop = bool(payload.get("loop", True))

        candidate = MusicTrack(id=track_id or path, path=path, volume=volume, loop=loop)

        if track_id:
            cached = self._music.get(track_id)
            if cached is not None:
                if (
                    cached.path != candidate.path
                    or abs(cached.volume - candidate.volume) > 1e-9
                    or cached.loop != candidate.loop
                ):
                    self._logger.warning(
                        "Music track payload for %s differs from cached value", track_id
                    )
                return cached
            self._music[track_id] = candidate
        return candidate


__all__ = [
    "EngineFrameImporter",
]
