# QA Regression Matrix

This matrix ties the hands-on regression coverage to the repeatability runs captured under `logs/`. Each row documents the
interactive validation required before promoting a build and references the deterministic replay evidence produced by the
latest repeatability sweep (`repeatability_20251105T034155Z`).

| Focus Area | Scenario & Inputs | Owner | Last Manual Run | Deterministic Evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| Controller Input | DualShock + Xbox via SDL shim; verify stick dead-zones, dash on face button, glyph trigger on shoulder | QA Guild | 2025-11-05 | `repeatability_20251105T034155Z.md` / `.json` | Confirm no input drift vs. scripted playback in logs seed `12345`. |
| Spawn Pacing | 5-minute Graveyard survival, seeds `12345`, `67890`, `424242`; compare swarm/boss arrival cadence | Systems QA | 2025-11-05 | `repeatability_20251105T034155Z.md` | Deterministic counts within ±1 enemy of matrix expectations. |
| Upgrade Flow | Level to tier-4 Rapid Fire path; validate menu text + stat deltas | QA Guild | 2025-11-05 | `repeatability_20251105T034155Z.md` | Run log shows identical upgrade order across repeats. |
| Hazards | Force-trigger Grave Wisp miasma + barricade salvage loops | Content QA | 2025-11-05 | `repeatability_20251105T034155Z.json` | Event digest hash parity verifies hazard scripts. |
| Runtime Playback | Tk viewer playback at 1.25x, capture audio cue alignment | Tech QA | 2025-11-05 | `repeatability_20251105T034155Z.md` | Cross-check frame timestamps with log duration 300s. |

## Usage

1. Execute `python -m tools.repeatability_check --repeat 2 --duration 300` and commit the generated Markdown/JSON logs.
2. Update the **Last Manual Run** column and annotate any drift observed between manual exercise and deterministic metrics.
3. Archive annotated captures (controller cam, viewer playback) alongside the logs under `logs/captures/<date>/`.
4. Reference this matrix from the roadmap to show ongoing QA maturity.
