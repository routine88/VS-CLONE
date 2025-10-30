# Nightfall Survivors Co-Op Scoping Brief

## 1. Stakeholder Inputs
- **Design (A. Serrano):** Wants two-player synchronous runs that preserve the existing power-fantasy arc and pacing. Requests shared progression for glyph sets and a revive loop so failure states remain recoverable.
- **Production (L. Chen):** Targets a 10-week vertical slice to validate retention lift before committing to Early Access scope. Flags risk on networking staffing and recommends re-using existing solo content where possible.

## 2. Solo System Inventory & Co-Op Blockers
| Area | Current State (Solo) | Blockers for Co-Op |
| --- | --- | --- |
| Session flow (`game/session.py`) | `RunSimulator` advances a single `GameState` and assumes one `Player` avatar with local mutation. | Requires session authority layer, multi-player lifecycle (ready checks, disconnections), and shared encounter pacing per party rather than a single health gate. |
| Core state (`game/game_state.py`) | `GameState` owns one `Player`, single `event_log`, and applies upgrades/glyphs directly to that player. | Must refactor to support multiple player instances, separate inventories, shared event broadcast, and synchronized upgrade choices; encounter resolution currently mutates one health pool. |
| Combat resolution (`game/combat.py`) | Damage, healing, and glyph bonuses are computed against one `Player`; enemies are resolved with no notion of multiple targets. | Need multi-target damage allocation, threat/aggro rules, and shared rewards (souls, relic drops). Network-safe determinism missing. |
| Systems directors (`game/systems.py`) | `SpawnDirector`/`EncounterDirector` scale difficulty off solo pacing tables and assume deterministic local RNG. | Co-op requires difficulty scaling by party size, host-authoritative RNG seeding, and event replication. |
| Networking | No networking/client-server abstraction; all logic runs in-process. | Introduce deterministic lockstep or authoritative server, replication of state deltas, lag compensation. |

## 3. Estimated Engineering Effort (Person-Weeks)
| Workstream | Estimate | Notes |
| --- | --- | --- |
| Multiplayer architecture & netcode foundation | 12 | Stand up session service, deterministic simulation hooks, rollback-safe combat loops. |
| GameState/Player refactor for multi-actor support | 8 | Split inventories, health, revive logic, synchronized upgrades. |
| Combat & encounter scaling updates | 6 | Co-op enemy tuning, reward splitting, revive mechanics. |
| UI/UX adjustments & messaging | 4 | Lobby flow, party HUD, co-op notifications. |
| QA automation & tooling | 3 | Deterministic replay capture, latency harnesses. |
| **Total** | **33 person-weeks** | Assumes 3 engineers + 1 UI contractor over ~3 months. |

## 4. Content & Production Adjustments
- Repurpose existing solo waves/minibosses with HP/damage multipliers; defer bespoke co-op bosses until Early Access.
- Implement limited revive tokens per run to preserve tension.
- Share glyph progression account-wide; gate unique co-op relics behind party achievements.
- Voice-over and localization updates constrained to systemic barks to stay within vertical slice timeline.

## 5. Roadmap Impact
- **Vertical Slice (10 weeks):** Shipping two-player online runs on two maps with limited relic pool. Success metric: +8% D2 retention in playtests.
- **Early Access (post-slice, +16 weeks):** Expand to four-player support, dedicated co-op relic track, and scalable backend services once slice KPIs met.

## 6. Lead Review Outcome
- **Decision:** Proceed with **vertical slice only**; defer Early Access commitment until slice KPI review.
- **Required Follow-Up Backlog Items:**
  1. Authoritative session service spike (netcode team).
  2. GameState multi-avatar refactor design doc & task breakdown.
  3. Combat scaling prototype with party size parameter.
  4. UX wireframes for lobby/readiness flows.
  5. QA plan for latency/rollback testing harness.

- **Next Checkpoint:** Slice mid-mortem review in 5 weeks.
