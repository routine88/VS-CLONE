"""Performance regression benchmarks executed in CI."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_LOG_DIR = Path(os.getenv("PERF_LOG_DIR", "logs/perf"))
DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

__all__ = ["DEFAULT_LOG_DIR"]

