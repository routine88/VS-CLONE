"""Data transfer objects that mirror prototype render frame exports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

Vector2 = Tuple[float, float]


@dataclass(frozen=True)
class SpriteDescriptor:
    """Runtime-friendly description of a sprite referenced in a frame."""

    id: str
    texture: str
    size: Tuple[int, int]
    pivot: Vector2
    tint: Tuple[int, int, int] | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpriteDescriptor":
        tint_payload = payload.get("tint")
        tint: Tuple[int, int, int] | None
        if tint_payload is None:
            tint = None
        else:
            tint = (
                int(tint_payload[0]),
                int(tint_payload[1]),
                int(tint_payload[2]),
            )
        return cls(
            id=str(payload["id"]),
            texture=str(payload["texture"]),
            size=(int(payload["size"][0]), int(payload["size"][1])),  # type: ignore[index]
            pivot=(float(payload["pivot"][0]), float(payload["pivot"][1])),  # type: ignore[index]
            tint=tint,
        )


@dataclass(frozen=True)
class RenderInstructionDTO:
    """Single render instruction decoded from exported JSON."""

    node_id: str
    sprite: SpriteDescriptor
    position: Vector2
    scale: float
    rotation: float
    flip_x: bool
    flip_y: bool
    layer: str
    z_index: int
    metadata: Mapping[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RenderInstructionDTO":
        position = payload.get("position", (0.0, 0.0))
        metadata_payload = payload.get("metadata", {})
        return cls(
            node_id=str(payload["node_id"]),
            sprite=SpriteDescriptor.from_dict(payload["sprite"]),  # type: ignore[arg-type]
            position=(float(position[0]), float(position[1])),  # type: ignore[index]
            scale=float(payload.get("scale", 1.0)),
            rotation=float(payload.get("rotation", 0.0)),
            flip_x=bool(payload.get("flip_x", False)),
            flip_y=bool(payload.get("flip_y", False)),
            layer=str(payload.get("layer", "")),
            z_index=int(payload.get("z_index", 0)),
            metadata=dict(metadata_payload),
        )


@dataclass(frozen=True)
class RenderFrameDTO:
    """Render frame mirroring :class:`game.graphics.RenderFrame`."""

    time: float
    viewport: Tuple[int, int]
    instructions: Tuple[RenderInstructionDTO, ...]
    messages: Tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RenderFrameDTO":
        viewport_payload = payload.get("viewport", (0, 0))
        instructions_payload = payload.get("instructions", [])
        messages_payload = payload.get("messages", [])
        return cls(
            time=float(payload.get("time", 0.0)),
            viewport=(int(viewport_payload[0]), int(viewport_payload[1])),  # type: ignore[index]
            instructions=tuple(
                RenderInstructionDTO.from_dict(instruction)
                for instruction in instructions_payload  # type: ignore[assignment]
            ),
            messages=tuple(str(message) for message in messages_payload),
        )

    @classmethod
    def from_json(cls, payload: str) -> "RenderFrameDTO":
        data: Dict[str, Any] = json.loads(payload)
        return cls.from_dict(data)


__all__ = ["RenderFrameDTO", "RenderInstructionDTO", "SpriteDescriptor"]
