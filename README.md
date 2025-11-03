# Nightfall Survivors Clone

This repository contains design documents, gameplay prototypes, and tooling for the Nightfall Survivors project.

See `docs/GIT_SETUP.md` for instructions on configuring Git so you can pull and push from the command line.

## Quickstart

- Prerequisites: Python 3.11+ (3.13 tested), no external deps required for the text/graphics MVP. Optional: Tk support for the viewer GUI.
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
  - `python -m game.mvp_viewer --duration 120 --playback 1.25`
- Arcade Prototype Viewer (Tkinter):
  - `python -m game.arcade_viewer --duration 180 --fps 45 --playback 1.0`

## Unity Bridge Export

- Export render/audio payloads for Unity integration using the CLI in `tools`:
  - `python -m tools.graphics_manifest --format json > manifest.json`
  - `python -m tools.export_unity_frames --frames 120 --output exports/mvp_frames.jsonl`

## Developer Workflow

- Run tests: `python -m pytest -q`
- Regenerate the graphics brief: `python -m tools.graphics_manifest --format markdown --output docs/GRAPHICS_ASSET_BRIEF.md`
- Launchers (Windows):
  - `LAUNCHMVP.bat` launches the graphical MVP and logs to `logs/mvp_last_run.log`.
  - `RUN_TESTS.bat`, `RUN_INTERACTIVE.bat`, `RUN_PROTOTYPE.bat` provide one‑click flows.

## Roadmap & MVP

- High‑level goals and milestones live in `docs/PRD.md` and `docs/ROADMAP.md`.
- Immediate execution focus is tracked in `docs/MVP_CHECKLIST.md` with a daily `docs/BUILD_NOTES_TEMPLATE.md`.
