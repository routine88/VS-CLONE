"""Helpers for configuring external GPU profilers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, Sequence

LOGGER = logging.getLogger(__name__)


def build_command(binary: Path, args: Sequence[str] | None = None) -> list[str]:
    """Return a command list combining the binary and optional arguments."""
    command = [str(binary)]
    if args:
        command.extend(args)
    LOGGER.debug("Profiler launch command: %s", command)
    return command


def validate_capture_output(path: Path) -> Path:
    """Ensure the capture destination exists and is writable."""
    resolved = path.expanduser()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def normalise_environment(extra_env: Iterable[tuple[str, str]] | None = None) -> dict[str, str]:
    """Build a process environment suitable for launching profilers."""
    env = dict(os.environ)
    if extra_env:
        for key, value in extra_env:
            env[key] = value
    return env


__all__ = [
    "LOGGER",
    "build_command",
    "validate_capture_output",
    "normalise_environment",
]

