"""Asset registries used by the native runtime renderer."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, MutableMapping

from native.client.audio import (
    AudioManifestDTO,
    MusicInstructionDTO,
    MusicTrackDescriptor,
    SoundClipDescriptor,
    SoundInstructionDTO,
)
from native.client.dto import SpriteDescriptor
from native.client.manifest import GraphicsManifest, ManifestSprite

LOGGER = logging.getLogger(__name__)


DEFAULT_GRAPHICS_MANIFEST = Path("assets/graphics_assets/manifest.json")
DEFAULT_AUDIO_MANIFEST = Path("assets/audio/manifest.json")


@dataclass(frozen=True)
class SpriteHandle:
    """Resolved sprite reference reused across frames."""

    id: str
    texture_path: Path
    size: tuple[int, int]
    pivot: tuple[float, float]
    tint: tuple[int, int, int] | None
    manifest: ManifestSprite | None


@dataclass(frozen=True)
class EffectHandle:
    """Resolved sound effect clip."""

    id: str
    path: Path
    volume: float
    descriptor: SoundClipDescriptor


@dataclass(frozen=True)
class MusicHandle:
    """Resolved music track entry."""

    id: str
    path: Path
    volume: float
    loop: bool
    descriptor: MusicTrackDescriptor


class SpriteRegistry:
    """Registry that materialises sprites from the graphics manifest."""

    def __init__(
        self,
        *,
        manifest_path: Path | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._path = manifest_path or DEFAULT_GRAPHICS_MANIFEST
        self._logger = logger or LOGGER
        self._manifest = GraphicsManifest.from_path(self._path)
        self._handles: Dict[str, SpriteHandle] = {}
        self._missing: MutableMapping[str, int] = {}

    @property
    def manifest(self) -> GraphicsManifest:
        return self._manifest

    @property
    def missing_counts(self) -> Mapping[str, int]:
        return dict(self._missing)

    def _build_handle(self, descriptor: SpriteDescriptor) -> SpriteHandle:
        sprite_id = descriptor.id or descriptor.texture
        manifest_sprite = self._manifest.sprites.get(descriptor.id)

        if manifest_sprite is not None:
            texture_path = manifest_sprite.texture_path
            size = manifest_sprite.size or descriptor.size
            pivot = manifest_sprite.pivot or descriptor.pivot
            tint = manifest_sprite.tint if manifest_sprite.tint is not None else descriptor.tint
        else:
            texture_path = Path(descriptor.texture)
            if not texture_path.is_absolute():
                texture_path = (self._manifest.root / texture_path).resolve()
            size = descriptor.size
            pivot = descriptor.pivot
            tint = descriptor.tint
            if descriptor.id:
                self._missing[descriptor.id] = self._missing.get(descriptor.id, 0) + 1
                self._logger.warning(
                    "Sprite %s not present in manifest; using descriptor fallback", descriptor.id
                )

        return SpriteHandle(
            id=sprite_id,
            texture_path=texture_path,
            size=(int(size[0]), int(size[1])),
            pivot=(float(pivot[0]), float(pivot[1])),
            tint=tint,
            manifest=manifest_sprite,
        )

    def resolve(self, descriptor: SpriteDescriptor) -> SpriteHandle:
        key = descriptor.id or descriptor.texture
        handle = self._handles.get(key)
        if handle is not None:
            return handle
        handle = self._build_handle(descriptor)
        self._handles[key] = handle
        return handle


class AudioRegistry:
    """Registry that reuses audio clips and tracks from the manifest."""

    def __init__(
        self,
        *,
        manifest_path: Path | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._path = manifest_path or DEFAULT_AUDIO_MANIFEST
        self._logger = logger or LOGGER
        self._manifest = self._load_manifest(self._path)
        self._root = self._path.parent
        self._effects: Dict[str, EffectHandle] = {}
        self._music: Dict[str, MusicHandle] = {}
        self._missing_effects: MutableMapping[str, int] = {}
        self._missing_music: MutableMapping[str, int] = {}

    @staticmethod
    def _load_manifest(path: Path) -> AudioManifestDTO:
        payload = json.loads(path.read_text())
        return AudioManifestDTO.from_dict(payload)

    @property
    def manifest(self) -> AudioManifestDTO:
        return self._manifest

    @property
    def missing_effect_counts(self) -> Mapping[str, int]:
        return dict(self._missing_effects)

    @property
    def missing_music_counts(self) -> Mapping[str, int]:
        return dict(self._missing_music)

    def resolve_effect(self, descriptor: SoundClipDescriptor) -> EffectHandle:
        key = descriptor.id or descriptor.path
        cached = self._effects.get(key)
        if cached is not None:
            return cached

        manifest_clip = self._manifest.effects.get(descriptor.id) if descriptor.id else None
        if manifest_clip is not None:
            clip_descriptor = manifest_clip
        else:
            clip_descriptor = descriptor
            if descriptor.id:
                self._missing_effects[descriptor.id] = self._missing_effects.get(descriptor.id, 0) + 1
                self._logger.warning(
                    "Effect %s not present in manifest; using descriptor fallback", descriptor.id
                )

        path = Path(clip_descriptor.path)
        if not path.is_absolute():
            path = (self._root / path).resolve()

        handle = EffectHandle(
            id=clip_descriptor.id or descriptor.id or descriptor.path,
            path=path,
            volume=float(clip_descriptor.volume),
            descriptor=clip_descriptor,
        )
        self._effects[key] = handle
        return handle

    def resolve_music(self, descriptor: MusicTrackDescriptor) -> MusicHandle:
        key = descriptor.id or descriptor.path
        cached = self._music.get(key)
        if cached is not None:
            return cached

        manifest_track = self._manifest.music.get(descriptor.id) if descriptor.id else None
        if manifest_track is not None:
            track_descriptor = manifest_track
        else:
            track_descriptor = descriptor
            if descriptor.id:
                self._missing_music[descriptor.id] = self._missing_music.get(descriptor.id, 0) + 1
                self._logger.warning(
                    "Music track %s not present in manifest; using descriptor fallback",
                    descriptor.id,
                )

        path = Path(track_descriptor.path)
        if not path.is_absolute():
            path = (self._root / path).resolve()

        handle = MusicHandle(
            id=track_descriptor.id or descriptor.id or descriptor.path,
            path=path,
            volume=float(track_descriptor.volume),
            loop=bool(track_descriptor.loop),
            descriptor=track_descriptor,
        )
        self._music[key] = handle
        return handle

    def resolve_effect_instruction(self, instruction: SoundInstructionDTO) -> EffectHandle:
        return self.resolve_effect(instruction.clip)

    def resolve_music_instruction(self, instruction: MusicInstructionDTO) -> MusicHandle | None:
        if instruction.track is None:
            return None
        return self.resolve_music(instruction.track)


__all__ = [
    "AudioRegistry",
    "EffectHandle",
    "MusicHandle",
    "SpriteHandle",
    "SpriteRegistry",
]

