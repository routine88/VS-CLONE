"""Reusable canvas helpers for translating render frames to Tk drawables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence, Tuple

from .graphics import RenderFrame


@dataclass(frozen=True)
class CanvasDrawable:
    """Simple drawing instruction consumed by a Tk canvas."""

    kind: str
    bounds: Tuple[float, float, float, float]
    color: str
    opacity: float
    metadata: Mapping[str, object]


class CanvasTranslator:
    """Convert :class:`RenderFrame` instructions into canvas-friendly drawables."""

    def __init__(self, *, palette: Mapping[str, str] | None = None) -> None:
        default_palette: MutableMapping[str, str] = {
            "background": "#0c0f1e",
            "player": "#57d9ff",
            "enemy": "#ff7676",
            "projectile": "#ffe066",
            "ui": "#9fa6c2",
            "hazard": "#e67e22",
            "collectible": "#5ee7c4",
        }
        if palette:
            default_palette.update(palette)
        self.palette = dict(default_palette)

    def translate(self, frame: RenderFrame) -> Sequence[CanvasDrawable]:
        drawables: list[CanvasDrawable] = []
        for instruction in frame.instructions:
            metadata = instruction.metadata
            kind = str(metadata.get("kind", "sprite"))
            width = instruction.sprite.size[0] * instruction.scale
            height = instruction.sprite.size[1] * instruction.scale
            x, y = instruction.position
            left = x - width * 0.5
            top = y - height * 0.5
            right = x + width * 0.5
            bottom = y + height * 0.5
            color = self.palette.get(kind, "#9aa1bd")
            opacity = max(0.0, min(1.0, instruction.opacity))
            drawables.append(
                CanvasDrawable(
                    kind=kind,
                    bounds=(left, top, right, bottom),
                    color=color,
                    opacity=opacity,
                    metadata=metadata,
                )
            )
        return tuple(drawables)


__all__ = ["CanvasDrawable", "CanvasTranslator"]

