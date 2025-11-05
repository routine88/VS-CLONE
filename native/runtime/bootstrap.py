"""Renderer bootstrap entrypoint used by the prototype runtime."""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
from typing import List, Optional, Sequence

from game.audio import AudioEngine, AudioFrame
from game.export import EngineFrameExporter
from game.graphics import GraphicsEngine, SceneNode
from game.graphics_assets import load_asset_manifest

from .importer import EngineFrameImporter
from .loop import FrameBundle, FramePlaybackLoop

LOGGER = logging.getLogger(__name__)
ASSET_MANIFEST_PATH = Path("assets/graphics_assets/manifest.json")


def build_placeholder_scene(
    graphics: GraphicsEngine,
    *,
    duration: float,
    fps: float,
    audio: AudioEngine,
    importer: EngineFrameImporter,
    exporter: EngineFrameExporter,
) -> List[FrameBundle]:
    """Generate placeholder frames and return imported render/audio bundles."""

    total_frames = max(1, int(math.ceil(duration * fps)))
    viewport_width, viewport_height = graphics.viewport
    placeholders = graphics.build_manifest().placeholders
    background_sprite = placeholders.get("background", "placeholders/background")
    player_sprite = placeholders.get("player", "placeholders/player")

    packets: List[FrameBundle] = []
    for index in range(total_frames):
        t = index / fps
        lerp = 0.0 if total_frames <= 1 else index / (total_frames - 1)
        x_pos = -0.3 * viewport_width + (0.6 * viewport_width * lerp)
        y_pos = 0.1 * viewport_height * math.sin(lerp * math.pi * 2.0)

        nodes = [
            SceneNode(
                id="background",
                position=(0.0, 0.0),
                layer="background",
                sprite_id=background_sprite,
                metadata={"kind": "background"},
            ),
            SceneNode(
                id="hero",
                position=(x_pos, y_pos),
                layer="actors",
                sprite_id=player_sprite,
                scale=1.0 + 0.1 * math.sin(lerp * math.pi * 4.0),
                rotation=math.sin(lerp * math.pi) * 5.0,
                metadata={"kind": "player", "frame": index},
            ),
        ]

        messages = (
            f"Frame {index}",
            f"Position: ({x_pos:.1f}, {y_pos:.1f})",
        )

        render_frame = graphics.build_frame(nodes, time=t, messages=messages)

        events: List[str] = []
        if index % max(1, int(fps)) == 0:
            events.append("ui.level_up")
        audio_frame: Optional[AudioFrame]
        if events:
            audio_frame = audio.build_frame(events, time=t)
        else:
            audio_frame = audio.build_frame((), time=t)

        payload = exporter.frame_bundle(render_frame=render_frame, audio_frame=audio_frame)
        packets.append(importer.frame_bundle(payload))

    return packets


def run_demo(
    *,
    duration: float,
    fps: float,
    realtime: bool,
    logger: logging.Logger | None = None,
) -> EngineFrameImporter:
    """Run the placeholder playback demo and return the importer instance."""

    target_logger = logger or LOGGER
    graphics = GraphicsEngine()
    manifest = load_asset_manifest(ASSET_MANIFEST_PATH)
    manifest.apply(graphics, replace_existing=True, update_viewport=True)

    audio = AudioEngine()
    audio.ensure_placeholders()

    importer = EngineFrameImporter(logger=target_logger)
    exporter = EngineFrameExporter()

    bundles = build_placeholder_scene(
        graphics,
        duration=duration,
        fps=fps,
        audio=audio,
        importer=importer,
        exporter=exporter,
    )

    if realtime:
        clock = None
        sleep = None
    else:
        fake_clock = _DeterministicClock()
        clock = fake_clock.time
        sleep = fake_clock.sleep

    loop = FramePlaybackLoop(bundles, clock=clock, sleep=sleep, logger=target_logger)
    loop.run()

    target_logger.info(
        "Imported %d sprites | %d effect clips | %d music tracks",
        len(importer.sprite_table),
        len(importer.effect_table),
        len(importer.music_table),
    )

    return importer


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=1.5, help="Demo duration in seconds")
    parser.add_argument("--fps", type=float, default=24.0, help="Frame rate used for placeholder scene")
    parser.add_argument(
        "--no-realtime",
        action="store_true",
        help="Disable real-time playback to avoid sleeping (useful for tests)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level for the runtime bootstrap",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    LOGGER.info(
        "Starting renderer bootstrap (duration=%.2fs, fps=%.1f, realtime=%s)",
        args.duration,
        args.fps,
        not args.no_realtime,
    )

    run_demo(duration=args.duration, fps=args.fps, realtime=not args.no_realtime, logger=LOGGER)
    return 0


class _DeterministicClock:
    """Utility clock used for deterministic playback in tests."""

    def __init__(self) -> None:
        self._time = 0.0

    def time(self) -> float:
        return self._time

    def sleep(self, delay: float) -> None:
        if delay > 0:
            self._time += delay


if __name__ == "__main__":
    raise SystemExit(main())
