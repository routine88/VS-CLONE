# Graphics Engine Overview

## Design summary
The graphics layer is built around lightweight data classes—`Sprite`, `AnimationFrame`, `AnimationClip`, `LayerSettings`, `Camera`, `SceneNode`, `RenderInstruction`, and `RenderFrame`—that describe everything the renderer needs without tying the simulation to a specific graphics API.

The `GraphicsEngine` seeds the system with a fallback "missing" sprite, placeholder assets for common kinds (player, enemy, projectile, background), and a sensible stack of default layers so gameplay code can assume these IDs always exist. Callers can register additional sprites, animation clips, layers, and placeholder mappings through helper methods, and the engine keeps a `viewport` property to drive camera defaults.

When `build_frame` runs it projects each `SceneNode` into screen space using the supplied or default camera, applies per-layer parallax, and emits a `RenderInstruction` per node. Any unrecognised layer is created on the fly, and the final instruction list is sorted by `(z_index, layer, node_id)` so front ends can render deterministically. The resulting `RenderFrame` bundles the viewport, ordered instructions, and optional debug messages for downstream consumers.

Sprite resolution goes through `_resolve_sprite`, which first honours explicit sprite IDs, then evaluates animation clips based on the frame time, and finally falls back to placeholder sprites keyed by the node’s `kind`, ensuring every logical entity can be drawn even if content is missing.

## Integration points
Gameplay systems (for example `ArcadeEngine`) produce `SceneNode` collections representing the current world state, then delegate to `GraphicsEngine.build_frame` to obtain a renderable frame. This bridge also positions the camera around the player and forwards gameplay messages for overlays.

Downstream tooling such as the runtime bridge consumes the emitted JSON payload (sprites, transforms, metadata) to drive actual rendering in the target client.

## Validation
Unit tests exercise animation selection, placeholder resolution, and integration with the interactive prototype, demonstrating the intended behaviours and providing a safety net for future changes.

### Asset validation check
Run `pytest tests/test_graphics_assets_validation.py` to confirm that every entry in `assets/graphics_assets/manifest.json` has a matching texture with the expected dimensions. The test wraps `SpriteAssetManifest.validate_assets(Path("assets/graphics_assets"))` and fails if any warnings are emitted so issues are surfaced early to content teams.

If you are working without the optional art pack, set `VS_SKIP_OPTIONAL_ART_PACK_VALIDATION=1` in your environment to skip the check temporarily. Re-enable the test once the pack is available so regression coverage remains intact.

## 2D asset requirements
The following assets should be delivered into an upcoming `assets/graphics_assets` directory. Keep pivots consistent so the prototype and runtime bridge align on positioning. Placeholder entries in source control are recorded as `.texture.json` descriptors, but production teams can now check in the final PNG exports directly—Git LFS keeps the binary payloads manageable inside the repository.

| Asset ID | Purpose | Texture Path | Dimensions (px) | Shape & Notes | Pivot | Animation Guidance |
| --- | --- | --- | --- | --- | --- | --- |
| `sprites/missing.texture.json` | Fallback sprite shown when content is missing. | `assets/graphics_assets/sprites/missing.texture.json` | 64 × 64 | High-contrast square with magenta/black check; obvious placeholder. | (0.5, 0.5) | Static frame. |
| `sprites/player_placeholder.texture.json` | Temporary player representation. | `assets/graphics_assets/sprites/player_placeholder.texture.json` | 96 × 96 | 1:1 silhouette of hunter; readable weapon outline. | (0.5, 0.5) | Supply idle (static) pose; optional run cycle uses same silhouette. |
| `sprites/enemy_placeholder.texture.json` | Generic foe stand-in. | `assets/graphics_assets/sprites/enemy_placeholder.texture.json` | 96 × 96 | 1:1 hulking silhouette with glow eyes; ensure unique silhouette from player. | (0.5, 0.5) | Single frame sufficient; optional two-frame bob for variety. |
| `sprites/projectile_placeholder.texture.json` | Default projectile. | `assets/graphics_assets/sprites/projectile_placeholder.texture.json` | 32 × 32 | Diamond bolt with trail, oriented horizontally. | (0.5, 0.5) | Static frame. |
| `sprites/background_placeholder.texture.json` | Parallax backdrop for prototype lanes. | `assets/graphics_assets/sprites/background_placeholder.texture.json` | 1280 × 720 | Wide parallax slice with horizon; layered silhouettes for depth. | (0.0, 0.0) | Static; consider modular tiles for scrolling. |
| `sprites/ui/health_orb.texture.json` | HUD health indicator for overlays. | `assets/graphics_assets/sprites/ui/health_orb.texture.json` | 64 × 64 | Circular vial with gothic frame, alpha background. | (0.5, 0.5) | Static. |
| `sprites/ui/experience_bar.texture.json` | HUD XP bar. | `assets/graphics_assets/sprites/ui/experience_bar.texture.json` | 512 × 64 | Horizontal bar with fill mask; left anchored. | (0.0, 0.5) | Static, but supply separate fill mask if possible. |
| `sprites/effects/dash_trail.texture.json` | Dash streak effect. | `assets/graphics_assets/sprites/effects/dash_trail.texture.json` | 128 × 64 | Elongated swoosh aligned horizontally; tapered ends. | (0.2, 0.5) | 3-frame fade variant ideal. |
| `sprites/effects/hit_flash.texture.json` | Enemy hit feedback. | `assets/graphics_assets/sprites/effects/hit_flash.texture.json` | 96 × 96 | Radial burst sized to overlay enemy placeholder. | (0.5, 0.5) | 2–3 frame burst. |
| `sprites/environment/barricade_intact.texture.json` | Breakable barricade element (intact). | `assets/graphics_assets/sprites/environment/barricade_intact.texture.json` | 192 × 128 | Rectangular obstacle prior to destruction. | (0.5, 0.5) | Static frame. |
| `sprites/environment/barricade_broken.texture.json` | Breakable barricade element (destroyed). | `assets/graphics_assets/sprites/environment/barricade_broken.texture.json` | 192 × 128 | Debris silhouette matching intact footprint. | (0.5, 0.5) | Static frame. |

> **Note:** The texture paths reference `.texture.json` descriptors committed to the repository so they remain diff-friendly on GitHub. When production art lands, replace the descriptor with a real PNG (and update the manifest path). The Git LFS configuration automatically stores the binary sprite without inflating the repo size.

### Palette & export guidance
- Colour palette: gothic neon with high contrast; avoid muddy mid-tones to maintain readability against dark backgrounds.
- Provide final sprites as PNG (or preferred runtime format) with transparency. The repository stores `.texture.json` descriptors for review, and Git LFS now tracks the actual PNG when swapped in—keep pixel grid alignment at 1:1 scale to avoid shimmering.
- Ensure animation frame counts match durations specified in code (two-frame run loops and three-frame effects work best for MVP).

### Asset manifest tooling
Run `python -m tools.graphics_manifest` to print the current manifest as JSON. Pass `--output path/to/file.json` to share with art or runtime teams.

The checked-in `assets/graphics_assets/manifest.json` mirrors this payload and is consumed by
`game.graphics_assets.load_asset_manifest` to populate the runtime catalogue. Updating the manifest
and regenerating the placeholder textures keeps the Python prototype and the native renderer in sync.

The same CLI also supports `--format markdown`, which emits the high-level asset brief consumed by AI concept pipelines. The checked-in `docs/GRAPHICS_ASSET_BRIEF.md` file is regenerated with:

```
python -m tools.graphics_manifest --format markdown --output docs/GRAPHICS_ASSET_BRIEF.md
```

These specifications will be revisited once bespoke art direction assets replace placeholders.
