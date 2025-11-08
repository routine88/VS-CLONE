# Graphics Asset Library

This directory contains the placeholder texture descriptors used by the Python
prototype. Each descriptor records the canvas size, palette hints, and purpose
for a sprite so runtime teams can swap in production-ready imagery later while
keeping filenames and dimensions consistent. Git LFS support is now enabled for
PNG assets, so production art can be committed directly alongside the manifest
when it is ready.

```
assets/
  graphics_assets/
    manifest.json             # Machine-readable description of sprite expectations.
    sprites/
      missing.texture.json
      player_placeholder.texture.json
      enemy_placeholder.texture.json
      projectile_placeholder.texture.json
      background_placeholder.texture.json
      ui/
        health_orb.texture.json
        experience_bar.texture.json
        ability_icon_dash.texture.json
      effects/
        dash_trail.texture.json
        hit_flash.texture.json
        soul_pickup.texture.json
      environment/
        barricade_intact.texture.json
        barricade_broken.texture.json
```

Each JSON file follows a lightweight schema:

```json
{
  "name": "Human readable title",
  "width": 96,
  "height": 96,
  "description": "What the sprite represents",
  "palette": ["#hex", "#values"],
  "notes": ["Guidance for the art team"]
}
```

Only the `width` and `height` fields are required by the tooling; the remaining
keys provide reference material for artists. Replace a descriptor with an actual
PNG (or point the manifest at a new file) once final art is ready. The
`game.graphics_assets.read_texture_dimensions` helper will validate either a
`.texture.json` descriptor or a `.png` file, allowing a smooth transition from
placeholder data to production sprites. Commit new PNGs directly—Git LFS stores
the binary payload while keeping diffs compact.

For teams that prefer to generate quick visual stand-ins, the JSON can be fed
into a build step that emits PNGs or sprite sheets. The descriptors remain handy
for reviews and automated validation, while the Git LFS configuration keeps the
committed PNGs lightweight for collaborators pulling the repository.
