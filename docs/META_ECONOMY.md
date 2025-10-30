# Meta Economy Pacing

This document outlines the updated sigil economy for the Nightfall Survivors prototype, covering the scoring model, unlock cadence, and telemetry checkpoints needed to validate the progression targets.

## Prototype Baseline

| Scenario | Command | Result |
| --- | --- | --- |
| Default run snapshot | `python -m game.prototype --summary` | Fallen at wave 2, 14 sigils earned. |
| 20-run sampling | Inline harness calling `PrototypeSession().run(seed=i)` | Average defeat payout of 14 sigils per run (280 total balance across 20 runs). |
| Final boss clear (powered state) | `RunSimulator` with `_build_powered_state(3)` | Successful clear producing 2,914 sigils thanks to capped encounter rewards. |

These snapshots give us the bookends for economy tuning: short defeats award enough currency to make steady progress, while full clears deliver a large lump sum for late-track unlocks.

## Sigil Scoring Model

The scoring constants now live in `game/session.py` and apply uniformly to prototype and live progression. The table below summarizes each component.

| Component | Constant | Payout |
| --- | --- | --- |
| Baseline entry | `SIGIL_BASELINE` | 10 sigils for any completed run. |
| Survival bonus | `SIGIL_SURVIVAL_BONUS` | +30 for surviving to dawn. |
| Final boss bonus | `SIGIL_FINAL_BOSS_BONUS` | +25 when the final encounter summary is `final_boss`. |
| Relics | `SIGIL_PER_RELIC` | +6 per relic collected. |
| Encounter clears | `SIGIL_PER_ENCOUNTER` (capped at 40 clears) | +2 per encounter up to 80 sigils. |
| Encounter streaks | `SIGIL_ENCOUNTER_MILESTONE_BONUS` (capped at six milestones) | +5 for every five encounters, up to +30. |
| Time survived | `SIGIL_PER_MINUTE_BUCKET` (15 bucket cap) | +3 per full minute survived, up to +45. |

The caps on encounters and milestones prevent hyper-optimized builds from breaking the economy while still rewarding long survival sessions.

## Launch Unlock Cadence

Launch progression focuses on the two starter hunters and two featured weapons. Unlock costs are tuned around the 14-sigil defeat average so that players unlock new options every 3–5 unsuccessful runs, with full clears allowing multiple purchases at once.

| Unlock | Requirement | Cost (Sigils) | Expected Runs to Unlock* | Notes |
| --- | --- | --- | --- | --- |
| Lunara the Moonshadow (`hunter_lunara`) | Resolve 5 encounters in a run | 45 | ~4 short runs | Designed as the first unlock; achievable through consistent wave progress even on defeats. |
| Bloodthorn Lance (`weapon_bloodthorn`) | Survive to dawn | 60 | 1 successful clear or ~5 defeats | Unlocks the first advanced weapon once players post a full run. |
| Verdant Sigil Set (`glyph_verdant`) | Collect 2 relics in a run | 55 | ~4–5 runs with miniboss success | Encourages relic hunting before pursuing Aurora. |
| Nocturne Harp (`weapon_nocturne`) | Defeat the final boss | 110 | Immediate upon first final boss clear | Large payout from the final encounter instantly covers this cost. |
| Aurora the Dawnbringer (`hunter_aurora`) | Survive to dawn and resolve 12 encounters | 120 | 1 clear plus a supplemental run | Positioned as the capstone reward of the launch track. |

\*Expected runs assumes the 14-sigil defeat average; survival rewards dramatically reduce the real run count once players reach consistent clears.

## Telemetry Hooks

To verify pacing once live data arrives, instrument the following signals:

- **Sigil acquisition** – `RunMetrics.sigils_earned` in `game/metrics.py` already captures per-run earnings. Add dashboards aggregating mean, median, and 95th percentile sigils per run.
- **Unlock acquisition timing** – Log unlock claims via `MetaProgressionSystem.unlock()`; capture run index, total playtime, and the triggering requirements to measure cadence vs. targets.
- **Encounter depth** – Track `encounters_resolved` and survival rate from `RunResult` payloads to correlate unlock timing with player skill progression.
- **Relic collection** – Monitor relic counts to ensure the Verdant Sigil requirement remains attainable without grind spikes.

These hooks should flow into whatever telemetry backend we stand up for the prototype so we can adjust constants quickly if the live distribution diverges from the modeled cadence above.
