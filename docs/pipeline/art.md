# Art Asset Import Pipeline

This guide defines the conventions the Nightfall content team follows when
preparing meshes and textures for the importer scripts located in
`tools/importers/`. The rules keep production assets predictable so automated
validation can catch mistakes before they land in the game build.

## File Naming

* **Source assets** live under `assets/source/`. Organise them by domain
  (`characters/`, `environments/`, `props/`, etc.) and name files using the
  pattern `<category>_<descriptor>_<variant>.<ext>` in snake case.
  * Example character: `characters/baseline_character_default.gltf`
  * Example prop: `props/energy_cell_damaged.fbx`
* **Texture files** must reuse the mesh prefix and append the workflow suffix:
  `<mesh>_<channel>.<ext>`. Supported channels are `_albedo`, `_normal`,
  `_metallic`, `_roughness`, `_ao`, and `_emissive`.
* **Import sidecars** (`.import.json`) capture metadata that is difficult to
  read directly from the mesh (author, collision setup, animation clip names,
  etc.). Keep the filename identical to the mesh plus the `.import.json`
  extension so tooling can locate it automatically.

## Unit Scale

* Nightfall's runtime interprets **one engine unit as one metre**.
* FBX files should be authored with `UnitScaleFactor = 1.0` and
a GLTF `asset.unitScaleFactor` of `1.0` to avoid rescaling.
* If the DCC package uses a different scene unit, bake the meshes to 1m before
  export or specify an explicit `unit_scale_meters` in the sidecar file. The
  importer will refuse files whose effective scale deviates by more than ±5%.
* Keep pivot positions centred on the gameplay origin. For environment tiles the
  pivot should sit on the ground plane so placement tooling can snap pieces
  together without vertical offsets.

## Texture Packing

* Characters and interactable props use **metallic-roughness packing**:
  * **R channel** – Ambient occlusion
  * **G channel** – Roughness
  * **B channel** – Metallic
  * **A channel** – Mask/opacity (optional)
* Environment tilables may ship as single-channel grayscale textures when only a
  height or roughness map is required.
* Provide textures as linear PNG or JPEG assets; the importer converts them into
  the packed formats expected by the engine and stores the results inside the
  generated bundles.
* Atlas textures should document their intended UV layout inside the sidecar so
  automated checks can confirm mesh UV sets stay within bounds.

By adhering to these conventions the importer can assemble deterministic bundles
in `assets/generated/`, giving engineering, QA, and design reliable references
for both runtime integration tests and content review.
