from __future__ import annotations

"""CLI: export MVP render/audio frames as Unity-friendly JSON bundles.

Writes one JSON object per line (JSONL) so downstream tools can stream frames.
"""

import argparse
from pathlib import Path
from typing import Iterable, Optional, Sequence

from game.export import UnityFrameExporter
from game.mvp_graphics import MvpVisualizer
from game.mvp import MvpConfig


def _iter_frame_bundles(*, seed: Optional[int], cfg: MvpConfig):
    vis = MvpVisualizer()
    result = vis.run(seed=seed, config=cfg)
    exporter = UnityFrameExporter()
    if len(result.frames) != len(result.audio_frames):
        raise RuntimeError(
            "render/audio frame count mismatch: "
            f"{len(result.frames)} render vs {len(result.audio_frames)} audio"
        )
    for render_frame, audio_frame in zip(result.frames, result.audio_frames):
        yield exporter.bundle_json(render_frame=render_frame, audio_frame=audio_frame)


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export MVP frames to JSONL for Unity integration.")
    p.add_argument("--seed", type=int, help="Random seed for deterministic runs.")
    p.add_argument("--frames", type=int, default=300, help="Max frames to export (default: 300).")
    p.add_argument("--duration", type=float, help="Override simulation duration (seconds).")
    p.add_argument("--tick", type=float, help="Simulation tick rate (seconds).")
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path. If omitted, writes to stdout.",
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    cfg = MvpConfig(
        duration=args.duration if args.duration is not None else MvpConfig.duration,
        tick_rate=args.tick if args.tick is not None else MvpConfig.tick_rate,
    )
    lines: Iterable[str] = _iter_frame_bundles(seed=args.seed, cfg=cfg)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as fh:
            for i, line in enumerate(lines):
                if i >= args.frames:
                    break
                fh.write(line)
                fh.write("\n")
    else:
        for i, line in enumerate(lines):
            if i >= args.frames:
                break
            print(line)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

