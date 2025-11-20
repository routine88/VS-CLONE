"""Analytics helpers for Nightfall Survivors prototype telemetry."""

from __future__ import annotations

import os
from typing import Optional, Sequence

LIVE_SERVICES_ENABLED = os.getenv("NIGHTFALL_ENABLE_LIVE_SERVICES") == "1"

if not LIVE_SERVICES_ENABLED:
    __all__: list[str] = []

    def main(argv: Optional[Sequence[str]] = None) -> int:
        print("Analytics module disabled; set NIGHTFALL_ENABLE_LIVE_SERVICES=1 to enable.")
        return 0
else:
    import argparse
    import json
    from typing import Iterable, List, Mapping, Sequence

    from .game_state import GameEvent
    from .metrics import (
        AggregateMetrics,
        RunMetrics,
        aggregate_by_hunter,
        aggregate_metrics,
        derive_metrics,
        hunter_kpis,
        kpi_snapshot,
    )
    from .prototype import PrototypeTranscript
    from .session import RunResult
    
    
    __all__ = [
        "AggregateMetrics",
        "RunMetrics",
        "aggregate_by_hunter",
        "aggregate_metrics",
        "derive_metrics",
        "from_transcripts",
        "hunter_kpis",
        "kpi_snapshot",
        "render_report",
    ]
    
    
    def from_transcripts(transcripts: Iterable[PrototypeTranscript]) -> List[RunMetrics]:
        """Derive metrics from prototype transcripts."""
    
        derived: List[RunMetrics] = []
        for transcript in transcripts:
            derived.append(derive_metrics(transcript.run_result, hunter_id=transcript.hunter_id))
        return derived
    
    
    def render_report(metrics: Sequence[RunMetrics]) -> str:
        """Render a formatted analytics report for console dashboards."""
    
        summary = aggregate_metrics(metrics)
        lines = [
            "Nightfall Survivors Analytics Report",
            f"Total Runs: {summary.total_runs}",
            f"Survival Rate: {summary.survival_rate:.2%}",
            f"Average Duration: {summary.average_duration:.1f}s (median {summary.median_duration:.1f}s)",
            f"Average Encounters: {summary.average_encounters:.1f}",
            f"Average Upgrade Diversity: {summary.average_upgrade_diversity:.2f}",
            f"Final Boss Rate: {summary.final_boss_rate:.2%}",
            f"Environment Death Rate: {summary.environment_death_rate:.2%}",
            f"Average Sigils: {summary.average_sigils:.1f}",
            f"Average Relics: {summary.average_relics:.1f}",
            f"Average Salvage: {summary.average_salvage:.1f}",
            "Phase Distribution:",
        ]
        for phase, share in summary.phase_distribution.items():
            lines.append(f"  Phase {phase}: {share:.2%}")
    
        hunter_breakdown = aggregate_by_hunter(metrics)
        if hunter_breakdown:
            lines.append("Hunter Breakdown:")
            for hunter_id, hunter_summary in hunter_breakdown.items():
                lines.append(
                    "  "
                    + f"{hunter_id}: runs {hunter_summary.total_runs}, "
                    + f"survival {hunter_summary.survival_rate:.1%}, "
                    + f"avg duration {hunter_summary.average_duration:.1f}s, "
                    + f"avg sigils {hunter_summary.average_sigils:.1f}"
                )
        return "\n".join(lines)
    
    
    def _load_transcript(path: str) -> PrototypeTranscript:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    
        run_payload = payload.get("run_result", {})
        events_payload = run_payload.get("events", payload.get("events", []))
        events: List[GameEvent] = []
        for entry in events_payload:
            if isinstance(entry, str):
                events.append(GameEvent(entry))
            elif isinstance(entry, Mapping):
                events.append(GameEvent(entry.get("message", "")))
            else:
                raise TypeError(f"Unsupported event payload: {entry!r}")
    
        result = RunResult(
            survived=run_payload.get("survived", payload.get("survived", False)),
            duration=float(run_payload.get("duration", payload.get("duration", 0.0))),
            encounters_resolved=int(run_payload.get("encounters_resolved", payload.get("encounters_resolved", 0))),
            relics_collected=list(run_payload.get("relics_collected", payload.get("relics_collected", []))),
            events=events,
            final_summary=None,
            sigils_earned=int(run_payload.get("sigils_earned", payload.get("sigils_earned", 0))),
        )
    
        return PrototypeTranscript(
            seed=int(payload.get("seed", 0)),
            hunter_id=payload.get("hunter_id"),
            hunter_name=payload.get("hunter_name", ""),
            survived=result.survived,
            duration=result.duration,
            encounters_resolved=result.encounters_resolved,
            relics_collected=result.relics_collected,
            sigils_earned=result.sigils_earned,
            events=[event.message for event in events],
            run_result=result,
        )
    
    
    def main(argv: Optional[Sequence[str]] = None) -> int:
        """CLI entry point to generate analytics reports from transcripts."""
    
        parser = argparse.ArgumentParser(description="Nightfall Survivors analytics generator")
        parser.add_argument("transcript", nargs="+", help="Path to transcript JSON files produced by the prototype.")
        parser.add_argument("--json", action="store_true", help="Emit JSON summary instead of text output.")
    
        args = parser.parse_args(argv)
    
        transcripts = [_load_transcript(path) for path in args.transcript]
    
        metrics = from_transcripts(transcripts)
        if args.json:
            print(json.dumps(kpi_snapshot(metrics), indent=2))
        else:
            print(render_report(metrics))
        return 0
    
    
    if __name__ == "__main__":  # pragma: no cover - CLI passthrough
        raise SystemExit(main())
