# Graphics Engine Overview

## Design summary
The graphics layer is built around lightweight data classes—`Sprite`, `AnimationFrame`, `AnimationClip`, `LayerSettings`, `Camera`, `SceneNode`, `RenderInstruction`, and `RenderFrame`—that describe everything the renderer needs without tying the simulation to a specific graphics API.

The `GraphicsEngine` seeds the system with a fallback "missing" sprite, placeholder assets for common kinds (player, enemy, projectile, background), and a sensible stack of default layers so gameplay code can assume these IDs always exist. Callers can register additional sprites, animation clips, layers, and placeholder mappings through helper methods, and the engine keeps a `viewport` property to drive camera defaults.

When `build_frame` runs it projects each `SceneNode` into screen space using the supplied or default camera, applies per-layer parallax, and emits a `RenderInstruction` per node. Any unrecognised layer is created on the fly, and the final instruction list is sorted by `(z_index, layer, node_id)` so front ends can render deterministically. The resulting `RenderFrame` bundles the viewport, ordered instructions, and optional debug messages for downstream consumers.

Sprite resolution goes through `_resolve_sprite`, which first honours explicit sprite IDs, then evaluates animation clips based on the frame time, and finally falls back to placeholder sprites keyed by the node’s `kind`, ensuring every logical entity can be drawn even if content is missing.

## Integration points
Gameplay systems (for example `ArcadeEngine`) produce `SceneNode` collections representing the current world state, then delegate to `GraphicsEngine.build_frame` to obtain a renderable frame. This bridge also positions the camera around the player and forwards gameplay messages for overlays.

Downstream tooling such as the Unity bridge consumes the emitted JSON payload (sprites, transforms, metadata) to drive actual rendering in the target client.

## Validation
Unit tests exercise animation selection, placeholder resolution, and integration with the interactive prototype, demonstrating the intended behaviours and providing a safety net for future changes.

## 2D asset requirements
The following assets should be delivered into an upcoming `assets/graphics_assets` directory. Keep pivots consistent so the prototype and Unity bridge align on positioning.

| Asset ID | Purpose | Texture Path | Dimensions (px) | Shape & Notes | Pivot | Animation Guidance |
| --- | --- | --- | --- | --- | --- | --- |
| `sprites/missing.png` | Fallback sprite shown when content is missing. | `graphics_assets/sprites/missing.png` | 64 × 64 | High-contrast square with magenta/black check; obvious placeholder. | (0.5, 0.5) | Static frame. |
| `sprites/player_placeholder.png` | Temporary player representation. | `graphics_assets/sprites/player_placeholder.png` | 96 × 96 | 1:1 silhouette of hunter; readable weapon outline. | (0.5, 0.5) | Supply idle (static) pose; optional run cycle uses same silhouette. |
| `sprites/enemy_placeholder.png` | Generic foe stand-in. | `graphics_assets/sprites/enemy_placeholder.png` | 96 × 96 | 1:1 hulking silhouette with glow eyes; ensure unique silhouette from player. | (0.5, 0.5) | Single frame sufficient; optional two-frame bob for variety. |
| `sprites/projectile_placeholder.png` | Default projectile. | `graphics_assets/sprites/projectile_placeholder.png` | 32 × 32 | Diamond bolt with trail, oriented horizontally. | (0.5, 0.5) | Static frame. |
| `sprites/background_placeholder.png` | Parallax backdrop for prototype lanes. | `graphics_assets/sprites/background_placeholder.png` | 1280 × 720 | Wide parallax slice with horizon; layered silhouettes for depth. | (0.0, 0.0) | Static; consider modular tiles for scrolling. |
| `sprites/ui/health_orb.png` | HUD health indicator for overlays. | `graphics_assets/sprites/ui/health_orb.png` | 64 × 64 | Circular vial with gothic frame, alpha background. | (0.5, 0.5) | Static. |
| `sprites/ui/experience_bar.png` | HUD XP bar. | `graphics_assets/sprites/ui/experience_bar.png` | 512 × 64 | Horizontal bar with fill mask; left anchored. | (0.0, 0.5) | Static, but supply separate fill mask if possible. |
| `sprites/effects/dash_trail.png` | Dash streak effect. | `graphics_assets/sprites/effects/dash_trail.png` | 128 × 64 | Elongated swoosh aligned horizontally; tapered ends. | (0.2, 0.5) | 3-frame fade variant ideal. |
| `sprites/effects/hit_flash.png` | Enemy hit feedback. | `graphics_assets/sprites/effects/hit_flash.png` | 96 × 96 | Radial burst sized to overlay enemy placeholder. | (0.5, 0.5) | 2–3 frame burst. |
| `sprites/environment/barricade.png` | Breakable barricade element. | `graphics_assets/sprites/environment/barricade.png` | 192 × 128 | Rectangular obstacle with destruct states. | (0.5, 0.5) | Provide intact + broken variants. |

### Palette & export guidance
- Colour palette: gothic neon with high contrast; avoid muddy mid-tones to maintain readability against dark backgrounds.
- Provide sprites as PNG with transparency. Maintain pixel grid alignment at 1:1 scale to avoid shimmering.
- Ensure animation frame counts match durations specified in code (two-frame run loops and three-frame effects work best for MVP).

### Asset manifest tooling
Run `python -m tools.graphics_manifest` to print the current manifest as JSON. Pass `--output path/to/file.json` to save it for art or Unity teams.

The same CLI also supports `--format markdown`, which emits the high-level asset brief consumed by AI concept pipelines. The checked-in `docs/GRAPHICS_ASSET_BRIEF.md` file is regenerated with:

```
python -m tools.graphics_manifest --format markdown --output docs/GRAPHICS_ASSET_BRIEF.md
```

These specifications will be revisited once bespoke art direction assets replace placeholders.
