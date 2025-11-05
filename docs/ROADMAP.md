# Project Roadmap

This roadmap translates the PRD milestones into concrete, trackable tasks.

## Milestones

- Concept Validation (4 weeks)
  - [x] Paper design and PRD baseline (`docs/PRD.md`)
  - [x] Text simulation of core loop (`game.prototype`)
  - [x] Interactive terminal slice (`game.interactive`)
  - [x] Graphics engine + placeholder pipeline (`game.graphics`, `tools.graphics_manifest`)
  - [x] Runtime bridge schema and exporter (`docs/ENGINE_RUNTIME.md`, `game.export`)

- Vertical Slice (12 weeks)
  - [ ] Graveyard biome content pass (enemies, hazards, props)
  - [ ] 2 starter hunters with signature weapons
  - [ ] 4 weapons with upgrade tiers and glyph synergies
  - [x] MVP visualizer and viewer (`game.mvp_graphics`, `game.mvp_viewer`)
  - [x] Audio cue table wired to events in viewer
  - [ ] Asset drop-in parity for runtime harness

- Content Expansion (16 weeks)
  - [ ] Additional biomes (Abandoned Village, Moonlit Forest)
  - [ ] 6 glyph sets and 20 relics represented in content tables
  - [ ] AI behaviours for ceiling clingers and ranged variants
  - [ ] Meta progression loop and profile persistence hooks

- Polish & Launch Prep (8 weeks)
  - [ ] Performance audit and optimizations
  - [ ] Localization review, add 2 additional languages
  - [ ] QA test plan and regression matrix
  - [ ] Marketing capture plan and press kit

- Early Access Launch
  - [ ] Steam page checklist and builds
  - [ ] Demo branch and EA branch management
  - [ ] Live-ops event schedule activation

## Engineering Checklist

- [x] Unit tests for all core modules (107 passing)
- [x] CI workflow for automated tests
- [ ] Package metadata (`pyproject.toml`) and console scripts
- [ ] Performance benchmarks and nightly run artifacts
- [ ] Runtime JSON exporter sample and ingestion stub in engine repo

## Art & Audio Intake

- [x] Asset briefs generated (`docs/GRAPHICS_ASSET_BRIEF.md`)
- [ ] Placeholder sprites: player, enemy, projectile, backdrop
- [ ] VFX sprites: dash trail, hit flash, soul pickup
- [ ] UI sprites: health orb, experience bar, ability icons
- [ ] Audio: SFX table + dusk/boss music loops

