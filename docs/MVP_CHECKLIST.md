# MVP Checklist

Actionable tasks to reach a playable, controller-in-hand MVP slice.

## Scope Lock

- [x] Single arena lane (Graveyard biome only)
- [x] One hunter with auto-firing starter weapon
- [x] Two enemy archetypes (swarm + bruiser) with chase AI

## Systems

- [x] Timed spawn ramps over ~5 minutes
- [x] Soul shard XP loop and level-up prompt
- [x] One upgrade option (damage or fire-rate) to demonstrate growth
- [x] Health/damage/fail state wired
- [x] Dash with cooldown and input hook

## Tooling & Build

- [x] Text simulation CLI (`game.prototype`)
- [x] Interactive terminal slice (`game.interactive`)
- [x] MVP viewer with Tk (`game.mvp_viewer`)
- [x] Runtime export payloads (`game.export`)
- [x] Windows launchers (`LAUNCHMVP.bat`, `RUN_*` scripts)
- [x] Test suite green locally
- [ ] CI green on pushes/PRs

## Runtime Harness (External Repo)

- [ ] Renderer project seeded with placeholder scene
- [ ] JSON importer for `EngineFrameExporter` payloads
- [ ] Sprite/audio lookup maps for placeholder assets
- [ ] Playback loop that applies frames deterministically

## Sign-off

- [ ] Playable for 5 minutes, repeatable outcomes with same seed
- [ ] Basic feel targets OK: pacing, density, responsiveness
- [ ] Owner sign-off captured in `logs/` and build notes

