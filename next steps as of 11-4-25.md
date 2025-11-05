# Next Steps as of 11-4-25

## Confirmation on engine direction
- The PRD explicitly commits the project to a proprietary, in-house 2D engine for rendering and simulation, along with matching in-house tooling for content and pipeline work.
- Current documentation and progress notes show that the Python sandbox exports JSON payloads specifically for a bespoke runtime, reinforcing that the downstream renderer, asset ingestion, and related tooling are meant to live inside our own engine stack rather than relying on third-party middleware.

## Next tasks to make the game executable and player-ready
1. **Stand up the native runtime harness.** Bootstrap the proprietary renderer project with a placeholder scene, wire up the JSON importer that mirrors `game.export.EngineFrameExporter`, build sprite/audio lookup tables, and implement the deterministic playback loop described in the runtime blueprint so that exported frames can be consumed in real time.
2. **Bring vertical-slice content to parity.** Fill out the Graveyard biome encounter data, two launch hunters, and four upgradeable weapons with glyph synergies so the runtime-driven build has feature-complete combat and progression during the slice milestone.
3. **Deliver placeholder and initial production assets.** Produce the sprite, VFX, UI, and audio placeholders called out in the roadmap so the in-house engine can render and mix against real assets instead of debug glyphs, enabling a shippable presentation layer.
4. **Sync audio cue handling with the runtime.** Finalize the audio cue table inside `game.mvp_viewer`/`game.audio` exports and ensure the native engine routes effect and music instructions correctly, matching the schema already defined for playback.
5. **Package and automate build distribution.** Add the missing packaging metadata and console scripts to `pyproject.toml`, expand CI so pushes produce verified artifacts, and publish a reproducible pipeline that hands off frame bundles and native builds to QA/playtesters.
6. **Capture sign-off criteria.** Once the runtime harness and content are wired, run the five-minute repeatability checks, log owner sign-off, and validate that users can launch the game through the provided scripts without manual setup.
