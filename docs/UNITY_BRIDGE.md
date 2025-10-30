# Unity Bridge Integration Blueprint

## Frame Payload Catalog

### Render Frames

Render frames originate from `game.graphics.GraphicsEngine.build_frame` and carry all data required for sprite-based rendering.

| Field | Type | Description |
| --- | --- | --- |
| `time` | `float` | Simulation time in seconds when the frame was generated. |
| `viewport` | `List[int]` | Width and height of the active camera viewport. |
| `messages` | `List[str]` | Optional debug or UI messages associated with the frame. |
| `instructions` | `List[Instruction]` | Ordered draw commands for sprites. |

Each instruction object contains:

| Field | Type | Description |
| --- | --- | --- |
| `node_id` | `str` | Identifier that links back to the logical scene node. |
| `sprite` | `SpriteDescriptor` | Metadata for the sprite asset that should be drawn. |
| `position` | `List[float]` | Screen-space X/Y coordinates after camera projection. |
| `scale` | `float` | Uniform scale factor already multiplied by camera zoom. |
| `rotation` | `float` | Rotation in radians, clockwise. |
| `flip_x` / `flip_y` | `bool` | Mirroring flags for sprite orientation. |
| `layer` | `str` | Render layer grouping used for batching and sorting. |
| `z_index` | `int` | Depth ordering key within the layer. |
| `metadata` | `Dict[str, Any]` | Arbitrary tags (e.g., `kind`, gameplay identifiers). |

A sprite descriptor resolves as:

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Unique identifier of the sprite definition. |
| `texture` | `str` | Asset path for the texture in the content pipeline. |
| `size` | `List[int]` | Pixel width and height of the sprite source rectangle. |
| `pivot` | `List[float]` | Normalized pivot point used for rotation and alignment. |
| `tint` | `List[int] \| null` | Optional RGB tint override. |

### Audio Frames

Audio frames are produced by `game.audio.AudioEngine.build_audio_frame` and represent all sound actions for a tick.

| Field | Type | Description |
| --- | --- | --- |
| `time` | `float` | Simulation timestamp matching the render frame. |
| `effects` | `List[EffectInstruction]` | Discrete sound effect triggers. |
| `music` | `List[MusicInstruction]` | Background music directives. |
| `metadata` | `Dict[str, Any]` | Extensible payload for additional routing data. |

Effect instructions expand to:

| Field | Type | Description |
| --- | --- | --- |
| `clip` | `ClipDescriptor` | Identifies the audio file to play and defaults. |
| `volume` | `float` | Playback volume multiplier after routing. |
| `pan` | `float` | Stereo pan offset in range [-1, 1]. |

Music instructions expand to:

| Field | Type | Description |
| --- | --- | --- |
| `track` | `TrackDescriptor \| null` | Target music track; `null` for stop commands. |
| `action` | `str` | `"play"`, `"refresh"`, `"stop"`, etc., telling Unity how to update state. |
| `volume` | `float \| null` | Optional override for track volume. |

Clip and track descriptors map directly to registered assets:

| Field | Type | Description |
| --- | --- | --- |
| `id` | `str` | Stable identifier for resolving lookups. |
| `path` | `str` | Resource path inside the audio bundle. |
| `volume` | `float` | Default gain for the asset. |
| `loop` | `bool` (tracks only) | Whether music should loop automatically. |

## Serialization Strategy

1. **Structure Preservation** – The exporter mirrors the dataclass layout while converting tuples to lists and dataclass objects to plain dictionaries so Unity can decode the payload with `JsonUtility` or a custom reader.
2. **Deterministic Keys** – Sorting dictionary keys in JSON output ensures diff-friendly payloads and consistent hashing for network transport.
3. **Extensibility** – Metadata blobs remain dictionaries so gameplay teams can add fields without changing the contract, while consumers should ignore unknown keys.

## Asset Mapping

- Maintain a central lookup table that maps sprite `id` values to Unity `Sprite` or `Texture2D` assets and audio identifiers to `AudioClip` objects.
- Use the `texture`/`path` strings as fallback resource locations when the identifier is unknown, enabling rapid iteration without strict asset bundles.
- Populate placeholder assets mirroring the prototype defaults (`placeholders/player`, `effects/ui.confirm`, etc.) so early integration keeps parity even before final content is authored.

## Update Loop Integration

1. **Frame Polling** – Fetch synchronized render and audio JSON blobs once per Unity frame. Deserialize into lightweight DTOs.
2. **Graphics Application** – Iterate `instructions`, resolve sprites via the lookup table, and spawn or reuse pooled `GameObject` instances. Apply `position`, `scale`, `rotation`, and flip flags (by adjusting local scale) before rendering.
3. **Audio Routing** – For each effect instruction, request the associated `AudioClip` from the asset map and play it via an audio pool. Inspect music instructions to start, refresh, or fade tracks using Unity's `AudioSource` components.
4. **Messaging Hooks** – Surface `messages` in debug overlays or logs to match prototype tooling.
5. **Loopback Telemetry** – When Unity determines the frame is fully applied, send acknowledgements or performance metrics back to the prototype if required to keep the simulation authoritative.

## Testing with the Prototype Exporter

- Use `game.export.UnityFrameExporter` to generate JSON payloads for render and audio frames.
- Validate the structure through unit tests or editor scripts before wiring into gameplay scenes.
- The included Unity stub validator in the test suite demonstrates the minimal requirements Unity must satisfy to consume the payload without schema mismatches.
