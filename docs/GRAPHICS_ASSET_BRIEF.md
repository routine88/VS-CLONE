# Graphics Asset Brief

Comprehensive requirements for 2D art assets referenced by the simulation graphics engine.
Each section lists the context needed for concept and production teams as well as AI image generation pipelines.

> Placeholder textures are committed as `.texture.json` descriptors so the
> repository remains review-friendly on GitHub. Swap each entry to point at a
> rendered PNG (or equivalent runtime format) once production art is ready,
> keeping the documented canvas dimensions and pivots intact.

## Missing Asset Placeholder (`__fallback__`)

- **Texture path**: `sprites/missing.texture.json`
- **Display size**: 64 × 64 px (pivot 0.50, 0.50)
- **Purpose**: Fallback / debug
- **Description**: High-contrast error tile shown whenever an expected sprite is absent.
- **Color palette**: #FF00FF - neon magenta, #000000 - absolute black
- **Mood/Story**: Utility glitch
- **Lighting direction**: Flat emission, no shading.
- **Art style**: Pixel-perfect checkerboard.
- **Tags**: placeholder, debug
- **Production notes**:
  - Should be unmistakable as an error state.

## Neon Graveyard Backdrop (`placeholders/background`)

- **Texture path**: `sprites/background_placeholder.texture.json`
- **Display size**: 1280 × 720 px (pivot 0.00, 0.00)
- **Purpose**: Level background
- **Description**: Layered parallax city of gothic spires with neon signage and misty foreground graves.
- **Color palette**: #15181F - midnight blue sky, #2F3E64 - distant architecture, #6AD7FF - neon signage, #4CFFB6 - spectral accent, #1A0F24 - foreground silhouettes
- **Mood/Story**: Moody, supernatural skyline.
- **Lighting direction**: Backlit horizon glow with scattered volumetric beams.
- **Art style**: Layered painterly matte with crisp silhouettes.
- **Tags**: environment, background, parallax
- **Production notes**:
  - Deliver as looping slice suitable for horizontal scrolling.
  - Foreground graves should have cutout alpha for parallax stacking.

## Cultist Brute Placeholder (`placeholders/enemy`)

- **Texture path**: `sprites/enemy_placeholder.texture.json`
- **Display size**: 96 × 96 px (pivot 0.50, 0.50)
- **Purpose**: Enemy stand-in
- **Description**: Broad-shouldered cultist with glowing void mask and heavy melee weapon.
- **Color palette**: #341A3A - deep violet cloth, #7E2F8E - saturated magenta armour, #E6DADA - bone mask glow, #2B101F - shadow core
- **Mood/Story**: Menacing brute
- **Lighting direction**: Underlit with purple bounce, subtle top rim.
- **Art style**: Stylised cel-shaded silhouette focus.
- **Tags**: enemy, character, placeholder
- **Production notes**:
  - Maintain hulking stance distinct from player silhouette.
  - Mask glow should read at thumbnail size.

## Hunter Vanguard Placeholder (`placeholders/player`)

- **Texture path**: `sprites/player_placeholder.texture.json`
- **Display size**: 96 × 96 px (pivot 0.50, 0.50)
- **Purpose**: Player character stand-in
- **Description**: Agile hunter with arc pistol, cloak fluttering back, facing three-quarter right.
- **Color palette**: #5CF1FF - arc energy cyan, #22252B - charcoal armour, #F5F2E8 - pale fabric highlight, #EC9C47 - warm accent trims
- **Mood/Story**: Heroic and ready for action.
- **Lighting direction**: Strong top-left rim light to emphasise silhouette.
- **Art style**: Stylised cel-shaded character illustration.
- **Tags**: player, character, placeholder
- **Production notes**:
  - Weapon hand forward, muzzle pointing to screen right.
  - Cape reads as a separate shape for animation overlap.

## Arc Bolt Placeholder (`placeholders/projectile`)

- **Texture path**: `sprites/projectile_placeholder.texture.json`
- **Display size**: 32 × 32 px (pivot 0.50, 0.50)
- **Purpose**: Projectile stand-in
- **Description**: Diamond-shaped energy bolt with trailing sparks moving left to right.
- **Color palette**: #A6F3FF - electric cyan core, #174D73 - dark cyan outline, #FFFFFF - white highlight
- **Mood/Story**: Fast and crackling.
- **Lighting direction**: Self-illuminated glow with subtle bloom.
- **Art style**: Minimalist VFX sprite with soft edges.
- **Tags**: projectile, vfx, placeholder
- **Production notes**:
  - Align long axis horizontally for side-scrolling readability.

## Abyssal Matriarch Placeholder (`placeholders/boss`)

- **Texture path**: `sprites/boss_placeholder.texture.json`
- **Display size**: 192 × 192 px (pivot 0.50, 0.50)
- **Purpose**: Boss stand-in
- **Description**: Towering matriarch cloaked in void silk with radiant halo of runes and twin scythes.
- **Color palette**: #271430 - deep void core, #7E44C7 - royal violet armor, #F6D8FF - halo glyphs, #3CF0FF - arc highlights
- **Mood/Story**: Ominous and imposing.
- **Lighting direction**: High-contrast rim light with underlit core glow.
- **Art style**: Stylised boss illustration with layered armour plates.
- **Tags**: boss, character, placeholder
- **Production notes**:
  - Silhouette should read clearly at 50% scale.
  - Arms extended slightly forward for attack readability.

## Void Hazard Placeholder (`placeholders/hazard`)

- **Texture path**: `sprites/hazard_placeholder.texture.json`
- **Display size**: 128 × 128 px (pivot 0.50, 0.50)
- **Purpose**: Environmental hazard stand-in
- **Description**: Crackling void rift disc with floating debris and lightning arcs.
- **Color palette**: #140B1F - abyssal center, #503A73 - volatile rim, #9C6BFF - arcing energy, #4CF2FF - electric highlights
- **Mood/Story**: Unstable eldritch energy.
- **Lighting direction**: Self-illuminated with pulsating corona.
- **Art style**: Stylised VFX disc with layered glow.
- **Tags**: hazard, vfx, placeholder
- **Production notes**:
  - Alpha falloff should taper smoothly for additive blending.

## Soul Cluster Placeholder (`placeholders/collectible`)

- **Texture path**: `sprites/collectible_placeholder.texture.json`
- **Display size**: 72 × 72 px (pivot 0.50, 0.50)
- **Purpose**: Collectible stand-in
- **Description**: Cluster of luminous shards orbiting a central crystal core.
- **Color palette**: #60FFE3 - teal glow, #2C4060 - deep shadow, #C5FFF6 - prismatic sparkles
- **Mood/Story**: Enticing magical reward.
- **Lighting direction**: Inner glow with soft outer bloom.
- **Art style**: Stylised collectible with particle accents.
- **Tags**: collectible, vfx, placeholder
- **Production notes**:
  - Design to tile well for pickup stacks.

## Dash Trail (`sprites/effects/dash_trail`)

- **Texture path**: `sprites/effects/dash_trail.texture.json`
- **Display size**: 128 × 64 px (pivot 0.20, 0.50)
- **Purpose**: Movement VFX
- **Description**: Elongated energy swoosh tapering to wisps, oriented left-to-right motion blur.
- **Color palette**: #4FF7FF - bright cyan core, #1C5B73 - deep teal edge, #B9FFFF - soft highlight
- **Mood/Story**: Energetic burst
- **Lighting direction**: Self-illuminated with slight transparency gradient.
- **Art style**: Soft additive VFX sprite.
- **Tags**: vfx, movement, dash
- **Production notes**:
  - Provide three sequential frames fading out for animation.
  - Edge feathering should avoid hard pixels.

## Hit Flash (`sprites/effects/hit_flash`)

- **Texture path**: `sprites/effects/hit_flash.texture.json`
- **Display size**: 96 × 96 px (pivot 0.50, 0.50)
- **Purpose**: Damage feedback VFX
- **Description**: Radial burst with jagged spikes and central flash to overlay on struck enemies.
- **Color palette**: #FFD75C - golden burst, #FF9147 - orange impact, #FFFFFF - intense core, #4D1A0D - dark rim
- **Mood/Story**: Sharp impact
- **Lighting direction**: Bright center with fast falloff to transparent edges.
- **Art style**: Graphic comic-book style burst.
- **Tags**: vfx, impact, combat
- **Production notes**:
  - Two to three frames with diminishing intensity for animation.

## Soul Shard Pickup (`sprites/effects/soul_pickup`)

- **Texture path**: `sprites/effects/soul_pickup.texture.json`
- **Display size**: 80 × 80 px (pivot 0.50, 0.50)
- **Purpose**: Collectible VFX
- **Description**: Floating crystal shard orbiting smaller motes with ethereal glow.
- **Color palette**: #7FFFD4 - aqua glow, #3A1C5E - void core, #C2FFE9 - pale highlights
- **Mood/Story**: Mystical reward
- **Lighting direction**: Inner glow with subtle pulsing outer aura.
- **Art style**: Stylised magical collectible.
- **Tags**: collectible, vfx, reward
- **Production notes**:
  - Supports looping four-frame twinkle animation.

## Level Up Pulse (`sprites/effects/level_up_pulse`)

- **Texture path**: `sprites/effects/level_up_pulse.texture.json`
- **Display size**: 128 × 128 px (pivot 0.50, 0.50)
- **Purpose**: Progression VFX
- **Description**: Radiant burst with concentric sigils and trailing motes.
- **Color palette**: #FFE17A - golden flare, #FF8B5C - ember edge, #FFF7E8 - inner highlight, #5C1E3A - arcane shadow
- **Mood/Story**: Triumphant surge
- **Lighting direction**: Brilliant center fading to translucent rim.
- **Art style**: Stylised magical burst with crisp sigil lines.
- **Tags**: vfx, progression, level_up
- **Production notes**:
  - Design to scale from 64px to 160px without losing clarity.
  - Include separate alpha channel for additive bloom if available.

## Gravestone Barricade - Broken (`sprites/environment/barricade_broken`)

- **Texture path**: `sprites/environment/barricade_broken.texture.json`
- **Display size**: 192 × 128 px (pivot 0.50, 0.50)
- **Purpose**: Breakable obstacle debris
- **Description**: Fragments of gravestones scattered with fading chain energy and dust.
- **Color palette**: #515B67 - shattered stone, #161B22 - deep crevice, #68D7E8 - dissipating magic, #B7BEC9 - dust motes
- **Mood/Story**: Aftermath of destruction.
- **Lighting direction**: Residual glow concentrated near fragments, softer shadows.
- **Art style**: Painterly shards with motion hints.
- **Tags**: environment, obstacle, debris
- **Production notes**:
  - Pairs with intact version; ensure silhouettes align for swap.

## Gravestone Barricade - Intact (`sprites/environment/barricade_intact`)

- **Texture path**: `sprites/environment/barricade_intact.texture.json`
- **Display size**: 192 × 128 px (pivot 0.50, 0.50)
- **Purpose**: Breakable obstacle
- **Description**: Cluster of ruined gravestones bound by arcane chains blocking the lane.
- **Color palette**: #5F6B7A - weathered stone, #1D242C - deep cracks, #8FF2FF - arcane chain glow, #2B1A33 - damp earth base
- **Mood/Story**: Ancient and oppressive.
- **Lighting direction**: Top-down moonlight with subsurface glow in runes.
- **Art style**: Painterly environment prop with crisp edges.
- **Tags**: environment, obstacle, breakable
- **Production notes**:
  - Design to break cleanly into two halves for destruction state.
  - Alpha fringe should remain tight for collision accuracy.

## Ability Icon - Dash (`sprites/ui/ability_icon_dash`)

- **Texture path**: `sprites/ui/ability_icon_dash.texture.json`
- **Display size**: 96 × 96 px (pivot 0.50, 0.50)
- **Purpose**: UI ability icon
- **Description**: Icon depicting motion-blurred boots streaking forward with cyan energy trail.
- **Color palette**: #3AF2FF - dash energy, #133649 - deep teal shadow, #F7F9FB - highlight streak, #1A0E24 - vignette background
- **Mood/Story**: Kinetic speed.
- **Lighting direction**: Directional motion blur with bright leading edge.
- **Art style**: Painterly icon with hard-edged rim lights.
- **Tags**: ui, icon, ability
- **Production notes**:
  - Rounded square canvas with transparent corners.
  - Keep icon readable at 48px.

## HUD Experience Bar (`sprites/ui/experience_bar`)

- **Texture path**: `sprites/ui/experience_bar.texture.json`
- **Display size**: 512 × 64 px (pivot 0.00, 0.50)
- **Purpose**: UI progression indicator
- **Description**: Horizontal bar with ornate frame and inner neon fill mask progressing left to right.
- **Color palette**: #2E1A3B - dark frame base, #8B4CC5 - mystical violet fill, #F0E6FF - highlight trims, #1B0F29 - deep shadow
- **Mood/Story**: Arcane progression.
- **Lighting direction**: Soft inner glow emanating from fill, metallic specular on frame.
- **Art style**: Stylised UI with crisp vector-like edges.
- **Tags**: ui, hud, progression
- **Production notes**:
  - Supply separate alpha mask for animated fill if possible.
  - Left edge should align at pixel 0 for layout anchoring.

## Soul Shard Counter (`sprites/ui/soul_counter`)

- **Texture path**: `sprites/ui/soul_counter.texture.json`
- **Display size**: 160 × 128 px (pivot 0.50, 0.50)
- **Purpose**: UI collectible tracker
- **Description**: Gothic frame containing floating shards and numeric counter window.
- **Color palette**: #1C1627 - obsidian frame, #71FFE5 - shard glow, #F5F2FF - highlight filigree, #362A4F - recess shadow
- **Mood/Story**: Arcane trophy display.
- **Lighting direction**: Backlit crystal cavity with metallic rim lights.
- **Art style**: High-fidelity UI ornament with translucent glass.
- **Tags**: ui, hud, collectible
- **Production notes**:
  - Reserve lower third for dynamic text overlay.
  - Provide layered PSD if possible for count animation.

## HUD Health Orb (`sprites/ui/health_orb`)

- **Texture path**: `sprites/ui/health_orb.texture.json`
- **Display size**: 64 × 64 px (pivot 0.50, 0.50)
- **Purpose**: UI health indicator
- **Description**: Circular vial with crimson liquid suspended in ornate brass frame and glass shine.
- **Color palette**: #C7313F - vibrant blood red, #571212 - deep burgundy, #D9B676 - aged brass, #0A0C10 - near-black background
- **Mood/Story**: Urgent survival HUD.
- **Lighting direction**: Glowing internal liquid with specular rim and subtle emissive tick marks.
- **Art style**: High-fidelity UI illustration with clean transparency.
- **Tags**: ui, hud, health
- **Production notes**:
  - Provide layered source if possible: frame, liquid, highlights.
  - Alpha background must be perfectly clean for overlay.
