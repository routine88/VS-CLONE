"""High-level render graph orchestration."""

from __future__ import annotations

import logging
from typing import Tuple

from native.client.dto import RenderFrameDTO

from .config import RenderPipelineConfig
from .model import AppliedRenderFrame, AppliedRenderInstruction
from .passes import GBufferPass, LightingPass
from .post import PostProcessingChain

LOGGER = logging.getLogger(__name__)


class RenderGraph:
    """Applies render frames using the deferred shading pipeline."""

    def __init__(
        self,
        pipeline: RenderPipelineConfig,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or LOGGER
        self._pipeline = pipeline
        self._gbuffer = GBufferPass(pipeline.material_registry)
        self._lighting = LightingPass(pipeline.lighting)
        self._post = pipeline.build_post_chain()

    def apply(
        self,
        frame: RenderFrameDTO,
        resolve_sprite,
    ) -> Tuple[AppliedRenderFrame, int]:
        resolved: list[AppliedRenderInstruction] = []
        missing = 0
        for instruction in frame.instructions:
            sprite = resolve_sprite(instruction.sprite)
            if getattr(sprite, "manifest", None) is None:
                missing += 1
                self._logger.debug(
                    "Sprite %s missing from manifest (texture=%s)",
                    instruction.sprite.id,
                    instruction.sprite.texture,
                )
            resolved.append(
                AppliedRenderInstruction(
                    instruction=instruction,
                    sprite=sprite,
                )
            )
        gbuffer = self._gbuffer.build(resolved)
        lighting = self._lighting.shade(gbuffer)
        post = self._post.apply(lighting.surfaces)
        applied = AppliedRenderFrame(
            frame=frame,
            instructions=tuple(resolved),
            gbuffer=gbuffer,
            lighting=lighting,
            post_process=post,
        )
        return applied, missing


__all__ = ["RenderGraph"]
