"""Test harness that replays exported frames using the manifest registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Tuple

from .dto import RenderFrameDTO, RenderInstructionDTO
from .manifest import GraphicsManifest, LayerDefinition, ManifestSprite, SpriteRegistry

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedInstruction:
    """Instruction paired with manifest lookups."""

    instruction: RenderInstructionDTO
    sprite: ManifestSprite | None
    layer: LayerDefinition | None


@dataclass(frozen=True)
class PlaybackFrame:
    """Result produced by :class:`FramePlaybackHarness`."""

    frame: RenderFrameDTO
    instructions: Tuple[ResolvedInstruction, ...]


class FramePlaybackHarness:
    """Replay exported frames using the registered manifest data."""

    def __init__(self, manifest: GraphicsManifest, *, logger: logging.Logger | None = None) -> None:
        self._manifest = manifest
        self._registry = SpriteRegistry(manifest)
        self._logger = logger or LOGGER

    @property
    def manifest(self) -> GraphicsManifest:
        return self._manifest

    @property
    def registry(self) -> SpriteRegistry:
        return self._registry

    def replay(self, payload: Mapping[str, Any]) -> PlaybackFrame:
        frame = RenderFrameDTO.from_dict(payload)
        return self._replay(frame)

    def replay_json(self, payload: str) -> PlaybackFrame:
        frame = RenderFrameDTO.from_json(payload)
        return self._replay(frame)

    def replay_many(self, payloads: Iterable[Mapping[str, Any]]) -> Tuple[PlaybackFrame, ...]:
        return tuple(self.replay(payload) for payload in payloads)

    def _replay(self, frame: RenderFrameDTO) -> PlaybackFrame:
        resolved: list[ResolvedInstruction] = []
        for instruction in frame.instructions:
            sprite = self._registry.resolve(instruction.sprite.id)
            if sprite is None:
                self._logger.warning(
                    "Unknown sprite %s (texture=%s)",
                    instruction.sprite.id,
                    instruction.sprite.texture,
                )
            layer = self._manifest.layers.get(instruction.layer)
            if layer is None:
                self._logger.warning(
                    "Unknown layer %s for node %s",
                    instruction.layer,
                    instruction.node_id,
                )
            resolved.append(
                ResolvedInstruction(
                    instruction=instruction,
                    sprite=sprite,
                    layer=layer,
                )
            )
        return PlaybackFrame(frame=frame, instructions=tuple(resolved))


__all__ = ["FramePlaybackHarness", "PlaybackFrame", "ResolvedInstruction"]
