"""Deterministic playback loop for render/audio frame bundles."""

from __future__ import annotations

import logging
import time
from typing import Callable, Iterable, Optional, Sequence, Tuple

from game.audio import AudioFrame
from game.graphics import RenderFrame

LOGGER = logging.getLogger(__name__)

FrameBundle = Tuple[RenderFrame, Optional[AudioFrame]]
ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
OnFrameFn = Callable[[int, RenderFrame, Optional[AudioFrame]], None]


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

    def run(self, on_frame: OnFrameFn | None = None) -> None:
        if not self._frames:
            self._logger.warning("No frames scheduled for playback")
            return

        start_time = self._clock()
        base_time = self._frames[0][0].time

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

    def _sync_to_target(self, start: float, target_offset: float) -> None:
        while True:
            now = self._clock()
            elapsed = now - start
            remaining = target_offset - elapsed
            if remaining <= 0:
                break
            self._sleep(remaining)


__all__ = ["FramePlaybackLoop", "FrameBundle"]
