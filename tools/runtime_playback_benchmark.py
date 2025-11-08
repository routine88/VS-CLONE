"""CLI for benchmarking runtime playback performance using exported frames."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from native.runtime import EngineFrameImporter, FrameBundle, FramePlaybackLoop


class _DeterministicClock:
    """Clock helper that advances deterministically for synthetic playback."""

    def __init__(self) -> None:
        self._time = 0.0

    def time(self) -> float:
        return self._time

    def sleep(self, delay: float) -> None:
        if delay > 0:
            self._time += delay


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay an exported frame bundle and collect CPU timing metrics for "
            "regression tracking."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the JSONL frame bundle produced by ns-export-frames.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON destination for metrics. Defaults to logs/runtime_metrics_<timestamp>.json."
        ),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        help="Optional Markdown summary output. Defaults to the JSON path with .md suffix.",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Include playback sleeping to simulate real-time rendering (default: disabled).",
    )
    return parser.parse_args(argv)


def _default_output_paths(json_path: Path | None, markdown_path: Path | None) -> tuple[Path, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if json_path is None:
        json_dest = Path("logs") / f"runtime_metrics_{timestamp}.json"
    else:
        json_dest = json_path.expanduser()
    if markdown_path is None:
        md_dest = json_dest.with_suffix(".md")
    else:
        md_dest = markdown_path.expanduser()
    json_dest.parent.mkdir(parents=True, exist_ok=True)
    md_dest.parent.mkdir(parents=True, exist_ok=True)
    return json_dest, md_dest


def _load_frame_bundles(path: Path) -> Iterable[FrameBundle]:
    importer = EngineFrameImporter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            yield importer.frame_bundle_from_json(stripped)


def _render_markdown(metrics: dict[str, object], source: Path) -> str:
    lines = [
        "# Runtime Playback Metrics",
        "",
        f"- Source bundle: `{source}`",
        f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key, value in metrics.items():
        label = key.replace("_", " ").title()
        lines.append(f"| {label} | {value} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    json_path, md_path = _default_output_paths(args.output, args.markdown)

    bundles = tuple(_load_frame_bundles(args.input))
    if not bundles:
        raise SystemExit(f"No frame data found in {args.input}")

    if args.realtime:
        clock = None
        sleep = None
    else:
        det_clock = _DeterministicClock()
        clock = det_clock.time
        sleep = det_clock.sleep

    loop = FramePlaybackLoop(bundles, clock=clock, sleep=sleep)
    metrics = loop.run()

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": str(args.input),
    }
    payload.update({key: round(value, 6) if isinstance(value, float) else value for key, value in asdict(metrics).items()})

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(payload, args.input), encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
