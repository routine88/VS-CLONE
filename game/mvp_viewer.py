"""Graphical MVP viewer powered by Tkinter."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .graphics import RenderFrame
from .graphics_canvas import CanvasDrawable, CanvasTranslator
from .mvp import MvpConfig, MvpReport
from .mvp_graphics import MvpVisualizationResult, MvpVisualizer

try:  # pragma: no cover - optional dependency on some platforms
    import tkinter as tk  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency on some platforms
    tk = None  # type: ignore


logger = logging.getLogger(__name__)

class MvpViewerApp:
    """Tkinter viewer that replays MVP simulation frames."""

    def __init__(
        self,
        *,
        visualizer: Optional[MvpVisualizer] = None,
        translator: Optional[CanvasTranslator] = None,
        playback_speed: float = 1.0,
        loop: bool = True,
        message_lines: int = 6,
        log_path: Optional[Path] = None,
    ) -> None:
        if playback_speed <= 0:
            raise ValueError("playback_speed must be positive")
        self.visualizer = visualizer or MvpVisualizer()
        self.translator = translator or CanvasTranslator()
        self.playback_speed = playback_speed
        self.loop = loop
        self.message_lines = message_lines
        self.log_path = log_path

        self._result: Optional[MvpVisualizationResult] = None
        self._drawables: List[Sequence[CanvasDrawable]] = []
        self._frame_index = 0
        self._viewport = self.visualizer.graphics.viewport

        self._root: Optional[tk.Tk] = None  # type: ignore[assignment]
        self._canvas: Optional[tk.Canvas] = None  # type: ignore[assignment]
        self._message_var: Optional[tk.StringVar] = None  # type: ignore[assignment]
        self._summary_var: Optional[tk.StringVar] = None  # type: ignore[assignment]

    def launch(self, *, seed: Optional[int] = None, config: Optional[MvpConfig] = None) -> None:
        if tk is None:  # pragma: no cover - runtime guard
            raise RuntimeError(
                "Tkinter is not available on this system. Install Tk support to run the viewer."
            )

        result = self.visualizer.run(seed=seed, config=config)
        self._result = result
        self._drawables = [self.translator.translate(frame) for frame in result.frames]
        self._viewport = result.frames[0].viewport if result.frames else self._viewport
        self._frame_index = 0

        if self.log_path is not None:
            self._write_report_log(result.report, self.log_path)

        root = tk.Tk()
        root.title("Nightfall Survivors - Graphical MVP")
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

        self._update_summary(result.report)
        self._render_current_frame()
        root.after(0, self._schedule_next_frame)
        root.mainloop()

    def _write_report_log(self, report: MvpReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = path.exists() and path.stat().st_size > 0
            with path.open("a", encoding="utf-8") as handle:
                if existing:
                    handle.write("\n")
                handle.write(self._format_report(report))
                handle.write("\n")
        except OSError as exc:
            logger.warning("Could not write viewer log at %s: %s", path, exc)

    def _format_report(self, report: MvpReport) -> str:
        enemies = ", ".join(f"{kind}: {count}" for kind, count in report.enemy_type_counts.items())
        upgrades = ", ".join(report.upgrades_applied) if report.upgrades_applied else "None"
        status = "Survived" if report.survived else "Fallen"
        lines = [
            "Nightfall Survivors MVP Run",
            f"Seed: {report.seed}",
            f"Outcome: {status}",
            f"Duration: {report.duration:.1f}s",
            f"Final Health: {report.final_health:.1f}",
            f"Enemies Defeated: {report.enemies_defeated}",
            f"Enemy Mix: {enemies}",
            f"Level Reached: {report.level_reached}",
            f"Soul Shards Collected: {report.soul_shards}",
            f"Upgrades Applied: {upgrades}",
            f"Dashes Performed: {report.dash_count}",
        ]
        return "\n".join(lines)

    def _update_summary(self, report: MvpReport) -> None:
        if not self._summary_var:
            return
        lines = [
            "Graphical MVP Overview",
            f"Outcome: {'Survived' if report.survived else 'Fallen'}",
            f"Duration: {report.duration:.1f}s",
            f"Enemies Defeated: {report.enemies_defeated}",
            f"Soul Shards: {report.soul_shards}",
            f"Level Reached: {report.level_reached}",
            f"Upgrades: {', '.join(report.upgrades_applied) if report.upgrades_applied else 'None'}",
        ]
        self._summary_var.set("\n".join(lines))

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


def run_viewer(
    *,
    seed: Optional[int] = None,
    config: Optional[MvpConfig] = None,
    playback_speed: float = 1.0,
    loop: bool = True,
    log_path: Optional[Path] = None,
) -> None:
    app = MvpViewerApp(playback_speed=playback_speed, loop=loop, log_path=log_path)
    app.launch(seed=seed, config=config)


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Nightfall Survivors graphical MVP viewer.")
    parser.add_argument("--seed", type=int, help="Random seed for deterministic runs.")
    parser.add_argument("--duration", type=float, help="Override simulation duration (seconds).")
    parser.add_argument("--tick", type=float, help="Simulation tick rate (seconds).")
    parser.add_argument("--playback", type=float, default=1.0, help="Playback speed multiplier.")
    parser.add_argument("--no-loop", action="store_true", help="Stop playback when the run ends instead of looping.")
    parser.add_argument(
        "--log",
        type=str,
        help="Optional path to write the simulation summary log.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    config = MvpConfig(
        duration=args.duration if args.duration is not None else MvpConfig.duration,
        tick_rate=args.tick if args.tick is not None else MvpConfig.tick_rate,
    )
    log_path = Path(args.log).expanduser() if args.log else None
    run_viewer(
        seed=args.seed,
        config=config,
        playback_speed=args.playback,
        loop=not args.no_loop,
        log_path=log_path,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution only
    raise SystemExit(main())
