"""Helper CLI for collecting GPU captures with PIX."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

from . import LOGGER, normalise_environment, validate_capture_output


def _resolve_pix(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    env_override = os.getenv("PIX_CLI")
    if env_override:
        return Path(env_override).expanduser()
    discovered = shutil.which("pix")
    if discovered is None:
        raise SystemExit(
            "PIX CLI not found. Install PIX or set PIX_CLI to the executable path (pix.exe)."
        )
    return Path(discovered)


def _parse_env(overrides: Sequence[str]) -> Iterable[tuple[str, str]]:
    for entry in overrides:
        if "=" not in entry:
            raise SystemExit(f"Invalid environment override '{entry}', expected KEY=VALUE format.")
        key, value = entry.split("=", 1)
        yield key, value


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the game via PIX and save a GPU timing capture."
    )
    parser.add_argument("--target", required=True, type=Path, help="Executable to launch.")
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("logs/profiling/latest_capture.wpixcapture"),
        help="Destination capture file.",
    )
    parser.add_argument(
        "--pix",
        type=Path,
        help="Optional path to pix CLI. Defaults to $PIX_CLI or PATH lookup.",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        help="Working directory for the launched process. Defaults to the target's parent.",
    )
    parser.add_argument(
        "--mode",
        choices=("timing", "gpu"),
        default="timing",
        help="Capture mode (CPU timing summary or GPU event capture).",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Optional duration for timing captures (in frames).",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help="Frames to skip before capture begins.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Environment overrides passed to the launched process.",
    )
    parser.add_argument(
        "target_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the target executable (prefix with -- to avoid parsing issues).",
    )
    return parser.parse_args(argv)


def _prepare_command(args: argparse.Namespace, capture_path: Path, pix: Path) -> list[str]:
    command = [str(pix), "capture", "--target", str(args.target), "--file", str(capture_path)]
    forwarded = list(args.target_args or [])
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    if forwarded:
        quoted = " ".join(shlex.quote(token) for token in forwarded)
        command.extend(["--args", quoted])
    if args.mode == "timing":
        command.append("--timing")
        if args.duration:
            command.extend(["--duration", str(max(0, args.duration))])
    else:
        command.append("--gpu")
    if args.delay:
        command.extend(["--delay", str(max(0, args.delay))])
    LOGGER.debug("PIX capture command: %s", command)
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    pix_cli = _resolve_pix(args.pix)
    capture_path = validate_capture_output(args.capture)
    working_dir = args.working_dir.expanduser() if args.working_dir else args.target.parent
    env = normalise_environment(tuple(_parse_env(args.env)))
    command = _prepare_command(args, capture_path, pix_cli)

    LOGGER.info("Starting PIX capture to %s", capture_path)
    subprocess.run(command, check=True, cwd=working_dir, env=env)
    print(capture_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

