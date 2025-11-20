# Nightfall Survivors Clone

This repository contains design documents, gameplay prototypes, and tooling for the Nightfall Survivors project.

See `docs/GIT_SETUP.md` for instructions on configuring Git so you can pull and push from the command line.

## Quickstart

- Prerequisites: Python 3.11+ (3.13 tested), no external deps required for the text/graphics MVP. Optional: Tk support for the viewer GUI.
- Launch the graphical MVP with one command: `python -m tools.launch_game --duration 300` (auto-seeds runs and logs to `logs/mvp_launch_<timestamp>.log`).
- Clone and run a quick smoke test:
  - `python -m pytest -q` (installs: `pip install pytest` if missing)
  - `python -m game.prototype --seed 123 --duration 60 --tick-step 5 --summary`

## Playable Options

- Text Simulation (deterministic, fast):
  - `python -m game.prototype --seed 123 --duration 300 --tick-step 10 [--summary]`
- Terminal Arcade Prototype (interactive slice):
  - `python -m game.interactive --duration 180 --fps 45`
  - Windows works without curses; on other platforms install `curses` if needed.
- Graphical MVP Viewer (Tkinter):
  - `python -m tools.launch_game --duration 120 --playback 1.25`
- Arcade Prototype Viewer (Tkinter):
  - `python -m game.arcade_viewer --duration 180 --fps 45 --playback 1.0`

## Runtime Frame Export

- Export render/audio payloads for the in-house runtime using the CLI in `tools`:
  - `python -m tools.graphics_manifest --format json > manifest.json`
  - `python -m tools.export_runtime_frames --frames 120 --output exports/mvp_frames.jsonl`
- Package and validate runtime drops for QA/playtesters:
  - `ns-runtime-artifacts bundle --output dist/native-runtime.zip`
  - `ns-runtime-artifacts checksum dist/native-runtime.zip`
  - See `docs/QA_HANDOFF.md` for the full handoff checklist.

## Developer Workflow

- Run tests: `python -m pytest -q`
- Regenerate the graphics brief: `python -m tools.graphics_manifest --format markdown --output docs/GRAPHICS_ASSET_BRIEF.md`
- Launch the MVP viewer without platform-specific scripts: `python -m tools.launch_game --duration 300`
- Launchers (Windows):
  - `PLAY.bat` runs the graphical MVP via `tools.launch_game`.
  - `RUN_TESTS.bat` provides a one‑click test run.

## Binary Assets & Git LFS

- The repository now tracks production art, audio, and distribution archives with [Git LFS](https://git-lfs.com/) so binary
  payloads can live alongside the source without bloating clone sizes.
- After cloning, run `git lfs install` once on your machine and ensure future clones pull LFS objects automatically (`git lfs
  pull`).
- New binary additions matching the tracked extensions (`*.png`, `*.wav`, `*.zip`, etc.) will be stored as LFS pointers—commit
  them normally and the tooling handles the heavy lifting.
- GitHub Actions already fetches LFS content during CI runs, so build and packaging jobs will see the exact binary assets that
  ship to QA and release channels.

## Repeatability Checks

- Run the deterministic five-minute validation sweep: `python -m tools.repeatability_check --repeat 2 --duration 300`
- Results are written to `logs/repeatability_<timestamp>.json` plus a Markdown summary for quick review.

## Roadmap & MVP

- High‑level goals and milestones live in `docs/PRD.md` and `docs/ROADMAP.md`.
- Immediate execution focus is tracked in `docs/MVP_CHECKLIST.md` with a daily `docs/BUILD_NOTES_TEMPLATE.md`.
