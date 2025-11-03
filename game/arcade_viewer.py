"""Graphical viewer for the arcade (curses) prototype using Tkinter."""

from __future__ import annotations

import argparse
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .audio import AudioEngine, AudioFrame
from .graphics import GraphicsEngine, RenderFrame
from .graphics_canvas import CanvasDrawable, CanvasTranslator
from .interactive import ArcadeEngine, FrameSnapshot, InputFrame

try:  # pragma: no cover - optional dependency on some platforms
    import tkinter as tk  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency on some platforms
    tk = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ArcadeVisualizationResult:
    """Container for visualisation artefacts built from the arcade engine."""

    frames: Sequence[RenderFrame]
    audio_frames: Sequence[AudioFrame]
    snapshots: Sequence[FrameSnapshot]

    @property
    def final_snapshot(self) -> FrameSnapshot:
        if not self.snapshots:
            raise ValueError("visualisation result does not contain any snapshots")
        return self.snapshots[-1]


class ArcadeVisualizer:
    """Run the arcade prototype and capture render/audio frames for playback."""

    def __init__(
        self,
        *,
        graphics: GraphicsEngine | None = None,
        audio: AudioEngine | None = None,
        duration: float = 120.0,
        tick_step: float = 1 / 45,
        auto_dash_interval: float = 8.0,
    ) -> None:
        if tick_step <= 0:
            raise ValueError("tick_step must be positive")
        if duration <= 0:
            raise ValueError("duration must be positive")
        self.graphics = graphics or GraphicsEngine()
        self.audio = audio or AudioEngine()
        self.duration = duration
        self.tick_step = tick_step
        self.auto_dash_interval = auto_dash_interval

    def run(self, *, seed: Optional[int] = None) -> ArcadeVisualizationResult:
        engine = ArcadeEngine(target_duration=self.duration)
        if seed is not None:
            try:
                engine._rng.seed(seed)  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover - defensive guard
                logger.debug("ArcadeEngine RNG does not support seeding; proceeding without.")

        snapshots: List[FrameSnapshot] = []
        render_frames: List[RenderFrame] = []
        audio_frames: List[AudioFrame] = []

        current_time = 0.0
        last_dash_time = -self.auto_dash_interval

        while current_time <= self.duration:
            inputs = self._auto_inputs(current_time, last_dash_time)
            if inputs.dash:
                last_dash_time = current_time

            snapshot = engine.step(self.tick_step, inputs)
            snapshots.append(snapshot)

            render_frames.append(
                engine.render_frame(self.graphics, snapshot=snapshot, time_override=snapshot.elapsed)
            )
            audio_frames.append(
                engine.build_audio_frame(self.audio, snapshot=snapshot, time_override=snapshot.elapsed)
            )

            if engine.awaiting_upgrade and engine.upgrade_options:
                engine.choose_upgrade(0)

            if snapshot.defeated or snapshot.survived:
                break

            current_time = snapshot.elapsed

        return ArcadeVisualizationResult(
            frames=tuple(render_frames),
            audio_frames=tuple(audio_frames),
            snapshots=tuple(snapshots),
        )

    def _auto_inputs(self, time_elapsed: float, last_dash_time: float) -> InputFrame:
        """Generate lightweight scripted inputs to keep the demo lively."""

        inputs = InputFrame()
        sway = math.sin(time_elapsed * 0.4)
        inputs.move_right = sway >= 0.0
        inputs.move_left = sway < 0.0

        drift = math.sin(time_elapsed * 0.23)
        if drift > 0.3:
            inputs.move_up = True
        elif drift < -0.3:
            inputs.move_down = True

        if (
            self.auto_dash_interval > 0
            and time_elapsed - last_dash_time >= self.auto_dash_interval
        ):
            inputs.dash = True

        return inputs


class ArcadeViewerApp:
    """Tkinter-based playback UI for :class:`ArcadeVisualizer` output."""

    def __init__(
        self,
        *,
        visualizer: ArcadeVisualizer | None = None,
        translator: CanvasTranslator | None = None,
        playback_speed: float = 1.0,
        loop: bool = False,
        message_lines: int = 8,
        log_path: Path | None = None,
    ) -> None:
        if playback_speed <= 0:
            raise ValueError("playback_speed must be positive")
        self.visualizer = visualizer or ArcadeVisualizer()
        self.translator = translator or CanvasTranslator()
        self.playback_speed = playback_speed
        self.loop = loop
        self.message_lines = message_lines
        self.log_path = log_path

        self._result: ArcadeVisualizationResult | None = None
        self._drawables: List[Sequence[CanvasDrawable]] = []
        self._frame_index = 0
        self._viewport = self.visualizer.graphics.viewport

        self._root: tk.Tk | None = None  # type: ignore[assignment]
        self._canvas: tk.Canvas | None = None  # type: ignore[assignment]
        self._message_var: tk.StringVar | None = None  # type: ignore[assignment]
        self._summary_var: tk.StringVar | None = None  # type: ignore[assignment]

    def launch(self, *, seed: Optional[int] = None) -> None:
        if tk is None:  # pragma: no cover - runtime guard
            raise RuntimeError(
                "Tkinter is not available on this system. Install Tk support to run the arcade viewer."
            )

        result = self.visualizer.run(seed=seed)
        if not result.frames:
            raise RuntimeError("arcade visualizer did not produce any frames")

        self._result = result
        self._drawables = [self.translator.translate(frame) for frame in result.frames]
        self._viewport = result.frames[0].viewport
        self._frame_index = 0

        if self.log_path is not None:
            self._write_run_log(result, self.log_path)

        root = tk.Tk()
        root.title("Nightfall Survivors - Arcade Viewer")
        root.configure(bg="#070912")
        self._root = root

        width, height = self._viewport
        panel_width = 320
        root.geometry(f"{width + panel_width}x{height + 40}")
        root.minsize(width + panel_width, height + 40)

        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=0)

        canvas = tk.Canvas(root, width=width, height=height, bg="#0c0f1e", highlightthickness=0)
        canvas.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="nsew")
        self._canvas = canvas

        self._summary_var = tk.StringVar()
        summary_label = tk.Label(
            root,
            textvariable=self._summary_var,
            justify=tk.LEFT,
            anchor="nw",
            fg="#e8ecff",
            bg="#11162a",
            font=("Segoe UI", 11, "bold"),
            wraplength=panel_width - 24,
            padx=12,
            pady=12,
        )
        summary_label.grid(row=0, column=1, sticky="new", padx=(0, 12), pady=(12, 6))

        self._message_var = tk.StringVar()
        message_label = tk.Label(
            root,
            textvariable=self._message_var,
            justify=tk.LEFT,
            anchor="nw",
            fg="#d9deff",
            bg="#0d1324",
            font=("Consolas", 10),
            wraplength=panel_width - 24,
            padx=12,
            pady=12,
        )
        message_label.grid(row=1, column=1, sticky="new", padx=(0, 12), pady=(6, 12))

        self._update_summary(result)
        self._render_current_frame()
        root.after(0, self._schedule_next_frame)
        root.mainloop()

    def _write_run_log(self, result: ArcadeVisualizationResult, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = path.exists() and path.stat().st_size > 0
            with path.open("a", encoding="utf-8") as handle:
                if existing:
                    handle.write("\n")
                handle.write(self._format_summary(result))
                handle.write("\n")
        except OSError as exc:
            logger.warning("Could not write arcade viewer log at %s: %s", path, exc)

    def _format_summary(self, result: ArcadeVisualizationResult) -> str:
        snapshot = result.final_snapshot
        outcome = "Survived" if snapshot.survived else ("Fallen" if snapshot.defeated else "In Progress")
        relics = ", ".join(snapshot.relics) if snapshot.relics else "None"
        lines = [
            "Arcade Prototype Run",
            f"Duration: {snapshot.elapsed:.1f}s",
            f"Outcome: {outcome}",
            f"Health: {snapshot.health}/{snapshot.max_health}",
            f"Level: {snapshot.level}",
            f"Score: {snapshot.score}",
            f"Phase Reached: {snapshot.phase}",
            f"Salvage: {snapshot.salvage_total}",
            f"Relics: {relics}",
        ]
        return "\n".join(lines)

    def _update_summary(self, result: ArcadeVisualizationResult) -> None:
        if not self._summary_var:
            return
        self._summary_var.set(self._format_summary(result))

    def _render_current_frame(self) -> None:
        if not self._canvas or not self._result:
            return
        if not self._drawables:
            self._canvas.delete("all")
            self._canvas.create_text(
                self._viewport[0] * 0.5,
                self._viewport[1] * 0.5,
                text="No frames to display",
                fill="#ffffff",
                font=("Segoe UI", 16, "bold"),
            )
            return

        frame = self._result.frames[self._frame_index]
        drawables = self._drawables[self._frame_index]

        self._canvas.delete("all")
        for drawable in drawables:
            left, top, right, bottom = drawable.bounds
            if drawable.kind == "background":
                self._canvas.create_rectangle(
                    0,
                    0,
                    self._viewport[0],
                    self._viewport[1],
                    fill=drawable.color,
                    outline="",
                )
            else:
                self._canvas.create_rectangle(
                    left,
                    top,
                    right,
                    bottom,
                    fill=drawable.color,
                    outline="",
                    width=0,
                )
                if drawable.kind == "player":
                    self._canvas.create_text(
                        (left + right) * 0.5,
                        top - 18,
                        text=f"HP: {drawable.metadata.get('health', 0):.0f}",
                        fill="#ffffff",
                        font=("Segoe UI", 10, "bold"),
                    )

        if self._message_var:
            messages = list(frame.messages[: self.message_lines])
            if not messages:
                messages = ["Simulation running..."]
            self._message_var.set("\n".join(messages))

    def _schedule_next_frame(self) -> None:
        if not self._root or not self._result:
            return
        frame_count = len(self._result.frames)
        if frame_count == 0:
            return

        next_index = self._frame_index + 1
        if next_index >= frame_count:
            if self.loop:
                next_index = 0
            else:
                return

        current_time = self._result.frames[self._frame_index].time
        next_time = self._result.frames[next_index].time
        delta = max(next_time - current_time, 1 / 60)
        delay_ms = max(int(delta * 1000 / self.playback_speed), 16)

        def advance() -> None:
            self._frame_index = next_index
            self._render_current_frame()
            self._schedule_next_frame()

        self._root.after(delay_ms, advance)


def run_arcade_viewer(
    *,
    seed: Optional[int] = None,
    duration: float = 120.0,
    fps: float = 45.0,
    playback_speed: float = 1.0,
    loop: bool = False,
    log_path: Path | None = None,
) -> None:
    visualizer = ArcadeVisualizer(duration=duration, tick_step=1.0 / fps)
    app = ArcadeViewerApp(
        visualizer=visualizer,
        playback_speed=playback_speed,
        loop=loop,
        log_path=log_path,
    )
    app.launch(seed=seed)


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the arcade graphical viewer.")
    parser.add_argument("--seed", type=int, help="Optional RNG seed for deterministic runs.")
    parser.add_argument("--duration", type=float, default=120.0, help="Duration of the simulated run (seconds).")
    parser.add_argument("--fps", type=float, default=45.0, help="Simulation tick rate (frames per second).")
    parser.add_argument("--playback", type=float, default=1.0, help="Playback speed multiplier.")
    parser.add_argument("--no-loop", action="store_true", help="Stop at the end of the run instead of looping.")
    parser.add_argument("--log", type=str, help="Optional path to append the run summary log.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    duration = max(1.0, args.duration)
    fps = max(1.0, args.fps)
    log_path = Path(args.log).expanduser() if args.log else None
    run_arcade_viewer(
        seed=args.seed,
        duration=duration,
        fps=fps,
        playback_speed=args.playback,
        loop=not args.no_loop,
        log_path=log_path,
    )
    return 0


__all__ = [
    "ArcadeVisualizationResult",
    "ArcadeVisualizer",
    "ArcadeViewerApp",
    "run_arcade_viewer",
]


if __name__ == "__main__":  # pragma: no cover - manual execution only
    raise SystemExit(main())

