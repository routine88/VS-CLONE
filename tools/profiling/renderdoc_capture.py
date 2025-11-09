"""Helper CLI for collecting captures with RenderDoc."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

from . import LOGGER, normalise_environment, validate_capture_output


def _resolve_renderdoc(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    env_override = os.getenv("RENDERDOC_CLI")
    if env_override:
        return Path(env_override).expanduser()
    discovered = shutil.which("renderdoccmd")
    if discovered is None:
        raise SystemExit(
            "RenderDoc CLI not found. Install RenderDoc or set RENDERDOC_CLI to the executable path."
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
        description="Launch the game through RenderDoc and write an .rdc capture file."
    )
    parser.add_argument("--target", required=True, type=Path, help="Executable to launch.")
    parser.add_argument(
        "--capture",
        type=Path,
        default=Path("logs/profiling/latest_capture.rdc"),
        help="Destination path for the capture file.",
    )
    parser.add_argument(
        "--renderdoc",
        type=Path,
        help="Optional path to renderdoccmd. Defaults to $RENDERDOC_CLI or PATH lookup.",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        help="Working directory for the launched process. Defaults to the target's parent.",
    )
    parser.add_argument(
        "--capture-after",
        type=int,
        default=1,
        help="Number of frames to wait before triggering capture once the process starts.",
    )
    parser.add_argument(
        "--frames",
        type=str,
        help="Comma separated frame indices to capture (e.g. 10,15,30). Overrides --capture-after if provided.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Environment overrides passed to the launched process.",
    )
    parser.add_argument(
        "--keep-ui",
        action="store_true",
        help="Open the RenderDoc UI once capture completes for manual inspection.",
    )
    parser.add_argument(
        "target_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the target executable (prefix with -- to avoid parsing issues).",
    )
    return parser.parse_args(argv)


def _prepare_command(args: argparse.Namespace, capture_path: Path, renderdoc: Path) -> list[str]:
    command = [str(renderdoc), "capture", "--file", str(capture_path), "--exe", str(args.target)]
    if args.working_dir is not None:
        command.extend(["--wd", str(args.working_dir.expanduser())])
    frames = getattr(args, "frames", None)
    if frames:
        command.extend(["--captureframes", frames])
    else:
        command.extend(["--captureafter", str(max(0, args.capture_after))])
    forwarded = list(args.target_args or [])
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    if forwarded:
        quoted = " ".join(shlex.quote(token) for token in forwarded)
        command.extend(["--args", quoted])
    if args.keep_ui:
        command.append("--ui")
    LOGGER.debug("RenderDoc capture command: %s", command)
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    renderdoc = _resolve_renderdoc(args.renderdoc)
    capture_path = validate_capture_output(args.capture)
    working_dir = args.working_dir.expanduser() if args.working_dir else args.target.parent
    env = normalise_environment(tuple(_parse_env(args.env)))
    command = _prepare_command(args, capture_path, renderdoc)

    LOGGER.info("Starting RenderDoc capture to %s", capture_path)
    subprocess.run(command, check=True, cwd=working_dir, env=env)
    print(capture_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

