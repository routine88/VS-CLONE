"""Automated frame-time benchmark for continuous integration."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import pytest

from native.client.dto import RenderFrameDTO, RenderInstructionDTO, SpriteDescriptor
from native.runtime.loop import FramePlaybackLoop

from . import DEFAULT_LOG_DIR

LOGGER = logging.getLogger(__name__)


class _DeterministicClock:
    """Monotonic clock replacement used to avoid real sleeps during benchmarks."""

    def __init__(self) -> None:
        self._time = 0.0

    def time(self) -> float:
        return self._time

    def sleep(self, duration: float) -> None:
        if duration > 0:
            self._time += duration


def _build_render_frames(frame_count: int) -> list[RenderFrameDTO]:
    sprite = SpriteDescriptor(
        id="bench_sprite",
        texture="/virtual/test.png",
        size=(64, 64),
        pivot=(0.5, 0.5),
    )
    frames: list[RenderFrameDTO] = []
    for index in range(frame_count):
        instructions = tuple(
            RenderInstructionDTO(
                node_id=f"node_{index}_{instruction}",
                sprite=sprite,
                position=(float(instruction), float(instruction)),
                scale=1.0,
                rotation=0.0,
                flip_x=False,
                flip_y=False,
                layer="default",
                z_index=instruction,
                metadata={"batch": instruction % 4},
            )
            for instruction in range(48)
        )
        frames.append(
            RenderFrameDTO(
                time=index * 0.002,
                viewport=(1920, 1080),
                instructions=instructions,
                messages=(),
            )
        )
    return frames


@pytest.mark.perf
def test_frame_time_benchmark_logs_metrics(tmp_path: Path, caplog: pytest.LogCaptureFixture, record_property: pytest.RecordProperty) -> None:
    caplog.set_level(logging.INFO)
    deterministic_clock = _DeterministicClock()
    render_frames = _build_render_frames(60)
    frame_stream = [(frame, None) for frame in render_frames]

    def _simulate_cpu_cost() -> None:
        start = time.perf_counter()
        while time.perf_counter() - start < 0.0002:
            pass

    loop = FramePlaybackLoop(frame_stream, clock=deterministic_clock.time, sleep=deterministic_clock.sleep)
    metrics = loop.run(on_frame=lambda *_: _simulate_cpu_cost())

    assert metrics.frame_count == len(render_frames)

    payload = {
        "frame_count": metrics.frame_count,
        "total_cpu_time_ms": round(metrics.total_cpu_time * 1000, 3),
        "average_frame_time_ms": round(metrics.average_frame_time * 1000, 3),
        "min_frame_time_ms": round(metrics.min_frame_time * 1000, 3),
        "max_frame_time_ms": round(metrics.max_frame_time * 1000, 3),
        "fps": round(metrics.fps, 3),
    }

    LOGGER.info("Frame time benchmark payload: %s", payload)
    record_property("frame_time_metrics", payload)

    destination = DEFAULT_LOG_DIR / "frame_time_benchmark.json"
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert destination.exists()
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written["frame_count"] == metrics.frame_count
    assert written["fps"] == payload["fps"]

    assert any("Frame time benchmark payload" in message for message in caplog.messages)

