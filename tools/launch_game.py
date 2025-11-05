"""Cross-platform helpers for launching Nightfall Survivors entry points."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

_LOG_DIR = Path("logs")


class LaunchError(RuntimeError):
    """Raised when a launch flow fails."""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch Nightfall Survivors builds without manual setup.")
    parser.add_argument(
        "--mode",
        choices=("mvp", "prototype", "interactive"),
        default="mvp",
        help="Which build to start (default: mvp).",
    )
    parser.add_argument("--seed", type=int, help="Optional RNG seed to pass through when supported.")
    parser.add_argument("--duration", type=float, help="Override the session duration in seconds.")
    parser.add_argument("--tick", type=float, help="Override the MVP simulation tick rate (seconds).")
    parser.add_argument("--tick-step", type=float, help="Override the prototype tick-step (seconds).")
    parser.add_argument("--fps", type=float, help="Target frame rate for interactive mode.")
    parser.add_argument(
        "--playback",
        type=float,
        default=1.0,
        help="Playback multiplier for the MVP viewer (default: 1.0).",
    )
    parser.add_argument("--no-loop", action="store_true", help="Disable looping playback in the MVP viewer.")
    parser.add_argument("--summary", action="store_true", help="Request a text summary when launching the prototype.")
    parser.add_argument(
        "--log",
        type=Path,
        help="Path to write launcher output. Defaults to logs/<mode>_launch_<timestamp>.log.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run 'git pull' before launching to fetch the latest code.",
    )
    parser.add_argument(
        "--export-transcript",
        type=Path,
        help="When launching the prototype, write the transcript JSON to this path.",
    )
    parser.add_argument(
        "--extra-arg",
        dest="extra_args",
        action="append",
        help="Additional raw arguments forwarded to the underlying command.",
    )
    return parser.parse_args(argv)


def _ensure_log_path(path: Path | None, mode: str) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if path is None:
        return (_LOG_DIR / f"{mode}_launch_{timestamp}.log").resolve()
    return path.expanduser().resolve()


def _run_command(command: Sequence[str], *, log_path: Path, stream_output: bool) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if stream_output:
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write(f"$ {' '.join(command)}\n\n")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="")
                handle.write(line)
            return process.wait()
    # Interactive mode needs to inherit the terminal.
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(f"$ {' '.join(command)}\n\n")
    with log_path.open("a", encoding="utf-8") as handle:
        result = subprocess.run(command, text=True)
        handle.write("(interactive session - output not captured)\n")
        return result.returncode


def _build_command(args: argparse.Namespace) -> Sequence[str]:
    command: List[str] = [sys.executable, "-m"]
    if args.mode == "mvp":
        command.append("game.mvp_viewer")
        if args.seed is not None:
            command.extend(["--seed", str(args.seed)])
        if args.duration is not None:
            command.extend(["--duration", str(args.duration)])
        if args.tick is not None:
            command.extend(["--tick", str(args.tick)])
        if args.playback != 1.0:
            command.extend(["--playback", str(args.playback)])
        if args.no_loop:
            command.append("--no-loop")
        command.extend(["--log", str(args.log_path)])
    elif args.mode == "prototype":
        command.append("game.prototype")
        if args.seed is not None:
            command.extend(["--seed", str(args.seed)])
        if args.duration is not None:
            command.extend(["--duration", str(args.duration)])
        if args.tick_step is not None:
            command.extend(["--tick-step", str(args.tick_step)])
        if args.summary:
            command.append("--summary")
        if args.export_transcript is not None:
            export_path = args.export_transcript.expanduser().resolve()
            export_path.parent.mkdir(parents=True, exist_ok=True)
            command.extend(["--export", str(export_path)])
    else:  # interactive
        command.append("game.interactive")
        if args.duration is not None:
            command.extend(["--duration", str(args.duration)])
        if args.fps is not None:
            command.extend(["--fps", str(args.fps)])
    if args.extra_args:
        command.extend(args.extra_args)
    return command


def _maybe_update_repo() -> None:
    result = subprocess.run(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise LaunchError(f"git pull failed:\n{result.stdout}")
    print(result.stdout)


def run(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    log_path = _ensure_log_path(args.log, args.mode)
    args.log_path = log_path

    if args.update:
        _maybe_update_repo()

    command = _build_command(args)
    stream_output = args.mode != "interactive"
    exit_code = _run_command(command, log_path=log_path, stream_output=stream_output)
    if exit_code != 0:
        raise LaunchError(f"Launch command failed with exit code {exit_code}")
    print(f"Launch complete. Log written to {log_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(run())
