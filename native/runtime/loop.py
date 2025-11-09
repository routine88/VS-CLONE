"""Deterministic playback loop for render/audio frame bundles."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from statistics import mean
from typing import Callable, Iterable, Mapping, Optional, Sequence, Tuple

from native.client.audio import AudioFrameDTO
from native.client.dto import RenderFrameDTO

from .project import AppliedFrame, RendererProject

LOGGER = logging.getLogger(__name__)

FrameBundle = Tuple[RenderFrameDTO, Optional[AudioFrameDTO]]
ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
OnFrameFn = Callable[[int, RenderFrameDTO, Optional[AudioFrameDTO]], None]
OnAppliedFn = Callable[[int, AppliedFrame], None]
InputOverrideFn = Callable[[RenderFrameDTO, Optional[AudioFrameDTO]], Mapping[str, object] | None]


@dataclass(frozen=True)
class PlaybackMetrics:
    """Summary statistics collected during frame playback."""

    frame_count: int
    total_cpu_time: float
    average_frame_time: float
    min_frame_time: float
    max_frame_time: float
    fps: float


class FramePlaybackLoop:
    """Play back exported frames using a monotonic clock."""

    def __init__(
        self,
        frames: Sequence[FrameBundle] | Iterable[FrameBundle],
        *,
        clock: ClockFn | None = None,
        sleep: SleepFn | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._frames = tuple(frames)
        self._clock = clock or time.perf_counter
        self._sleep = sleep or time.sleep
        self._logger = logger or LOGGER

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    def run(
        self,
        project: RendererProject | None = None,
        *,
        on_frame: OnFrameFn | None = None,
        input_override: InputOverrideFn | None = None,
        on_applied: OnAppliedFn | None = None,
    ) -> PlaybackMetrics:
        if not self._frames:
            self._logger.warning("No frames scheduled for playback")
            return PlaybackMetrics(
                frame_count=0,
                total_cpu_time=0.0,
                average_frame_time=0.0,
                min_frame_time=0.0,
                max_frame_time=0.0,
                fps=0.0,
            )

        start_time = self._clock()
        base_time = self._frames[0][0].time
        cpu_start = time.perf_counter()
        previous_mark = cpu_start
        frame_intervals: list[float] = []

        for index, (render_frame, audio_frame) in enumerate(self._frames):
            target = max(0.0, render_frame.time - base_time)
            self._sync_to_target(start_time, target)

            self._logger.debug(
                "Frame %03d | time=%.3f | instructions=%d | messages=%d | audio_effects=%d | audio_music=%d",
                index,
                render_frame.time,
                len(render_frame.instructions),
                len(render_frame.messages),
                len(audio_frame.effects) if audio_frame is not None else 0,
                len(audio_frame.music) if audio_frame is not None else 0,
            )

            if on_frame is not None:
                on_frame(index, render_frame, audio_frame)

            applied: AppliedFrame | None = None
            if project is not None:
                overrides = (
                    input_override(render_frame, audio_frame) if input_override is not None else None
                )
                applied = project.apply_frame(
                    render_frame,
                    audio_frame,
                    overrides=overrides,
                )

            if applied is not None and on_applied is not None:
                on_applied(index, applied)

            current_mark = time.perf_counter()
            frame_intervals.append(current_mark - previous_mark)
            previous_mark = current_mark

        cpu_end = time.perf_counter()
        total_cpu_time = cpu_end - cpu_start
        if frame_intervals:
            average = mean(frame_intervals)
            min_frame = min(frame_intervals)
            max_frame = max(frame_intervals)
        else:
            average = min_frame = max_frame = 0.0

        fps = (self.frame_count / total_cpu_time) if total_cpu_time > 0 else 0.0

        return PlaybackMetrics(
            frame_count=self.frame_count,
            total_cpu_time=total_cpu_time,
            average_frame_time=average,
            min_frame_time=min_frame,
            max_frame_time=max_frame,
            fps=fps,
        )

    def _sync_to_target(self, start: float, target_offset: float) -> None:
        while True:
            now = self._clock()
            elapsed = now - start
            remaining = target_offset - elapsed
            if remaining <= 0:
                break
            self._sleep(remaining)


__all__ = ["FramePlaybackLoop", "FrameBundle", "PlaybackMetrics"]
