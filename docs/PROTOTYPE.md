# Nightfall Survivors Text Prototype

The Python logic stack now ships with a small text-mode harness so designers can
prototype Nightfall Survivors runs without waiting for the Unity client. The
entrypoint can be executed directly from the repository root:

```bash
python -m game.prototype --seed 123 --duration 300 --tick-step 10
```

The command above runs a five-minute slice using deterministic RNG so combat and
hazard rolls are reproducible between runs.

## Options

| Option | Description |
| ------ | ----------- |
| `--hunter` | Hunter identifier to pilot (defaults to the active profile hunter). |
| `--seed` | RNG seed for deterministic simulations. |
| `--duration` | Override the total session duration in seconds (default: 1200). |
| `--tick-step` | Simulation tick granularity in seconds (default: 5). |
| `--demo` | Apply the public demo restrictions (10 minute cap, starter hunters). |
| `--event-id` | Apply a seasonal live-ops event by identifier. |
| `--event-year` | Year to evaluate when resolving `--event-id`. |
| `--profile-path` | Load an encrypted player profile before running. Requires `--key`. |
| `--key` | Decryption key used with `--profile-path`. |

## Demo Mode & Seasonal Events

To mirror the PRD's public demo, pass `--demo` when running the prototype. The
session duration is capped at ten minutes, upgrade decks are trimmed to starter
weapons, and only Varik and Mira remain selectable. Demo mode works with either
the text simulation or the curses arcade slice.

Seasonal events can be previewed inside the sandbox by supplying
`--event-id harvest_moon` (or any id from the annual schedule). The command will
boost enemy density, hazard severity, and salvage rewards to reflect the live
ops tuning for that event. Use the live-ops CLI to inspect the schedule:

```bash
python -m game.live_ops --active
```

The CLI supports listing all events for a year with `--year 2027` or printing a
specific definition via `--event-id blood_eclipse`.

## Sample Output

```
Nightfall Survivors Prototype Run
Hunter: Varik the Nightblade (hunter_varik)
Seed: 123
Outcome: Fallen
Duration: 298.4s
Encounters Resolved: 8
Relics: Moonlit Charm
Sigils Earned: 14

Event Log:
  [001] Wave 1 incoming with 6 foes.
  [002] Resolved wave defeating 6 foes in 12.5s.
  ...
```

Event logs mirror the order recorded on the `GameState`, making it easier to
validate encounter pacing, hazard cadence, and reward flow while more of the PRD
feature set is implemented.

## Content Coverage Checkpoints

The current sandbox reflects the PRD's vertical-slice expectations for combat
variety:

- **Enemies:** 12 core archetypes roll out over the four phases, while elite
  variants inject during late waves to pressure builds.
- **Weapons:** Ten weapons with full four-tier progressions are represented in
  the upgrade deck, including the unlockable Nocturne Harp.
- **Relics:** Twenty relic rewards rotate through miniboss drops to keep runs
  varied and support meta progression hooks.

Prototype transcripts enumerate these pulls so designers can verify cadence and
encounter composition before assets land in-engine.

## Challenge Builder

Community runs can now be curated with the challenge builder CLI:

```bash
python -m game.challenges --seed 777 --modifier torment --ban weapon_umbra_lash
```

The command prints a shareable code (prefixed with `NSC1-`) alongside a human
readable summary. Anyone can replay the same conditions by decoding the string:

```bash
python -m game.challenges --decode NSC1-...
```

Codes capture run seeds, optional duration overrides, difficulty labels,
modifiers, and curated reward or restriction lists so designers can circulate
weekly challenge briefs before the Unity client is playable.

## Transcript Export & Analytics

Designers can persist simulated runs to JSON for deeper telemetry analysis. After
executing a run, serialise the transcript and feed it to the analytics CLI:

```python
from game.prototype import PrototypeSession, save_transcript

session = PrototypeSession()
transcript = session.run(seed=4242, total_duration=600, tick_step=10)
save_transcript(transcript, "runs/nightfall_run.json")
```

Multiple transcripts can be analysed together to generate KPI-aligned reports:

```bash
python -m game.analytics runs/nightfall_run.json runs/elite_test.json
```

Add `--json` to emit machine-readable aggregates that plug into dashboards or
spreadsheet tooling. Metrics include survival rate, upgrade diversity, salvage
flow, and phase reach distributions to keep the project aligned with the PRD's
success criteria.

## Steam Cloud Simulation

A lightweight Steam Cloud façade is available to sync encrypted saves between
machines while the Unity client is under construction. Upload your local save
into a named slot:

```bash
python -m game.cloud --root .cloud upload --profile-path saves/profile.sav --key hunter --slot home
```

List remote slots or download them back to disk when moving to a different
machine:

```bash
python -m game.cloud --root .cloud list
python -m game.cloud --root .cloud download --slot home --key hunter --output saves/profile.sav
```

Manifest checksums guard against corruption so meta progression isn't lost while
passing saves around.

## Cosmetic DLC & Demo Restrictions

The monetization plan now has a functional mock via `game.monetization`. Packs
are cosmetic-only in line with the PRD. Designers can script purchases and apply
skins to hunter loadouts using the storefront helpers:

```python
from game.monetization import Storefront, CurrencyWallet, default_dlc_packs

store = Storefront(default_dlc_packs().values())
wallet = CurrencyWallet(balance=10.0)
inventory = profile.cosmetics

store.purchase("dlc_founders", wallet, inventory)
inventory.equip(next(item for item in store.get_pack("dlc_founders").items if item.category == "hunter_skin"))
```

Equipped cosmetics flow into the profile so future runs and the Unity client can
reflect owned skins and VFX.

## Arcade Playable Prototype

The repo now includes a curses-powered arcade loop that surfaces an interactive
2D slice using the same combat math and upgrade decks as the simulations. Launch
it from a terminal window:

```bash
python -m game.interactive --duration 180 --fps 45 --language es
```

Use the optional `--language` flag to localize the interface strings. The default
catalog currently ships English (`en`) and Spanish (`es`) tables, and additional
languages can be registered through `game.localization.default_catalog()`.

Controls are intentionally lightweight so design can focus on pacing:

| Input | Action |
| ----- | ------ |
| Arrow keys | Move the hunter through the lanes. |
| Space / `D` | Dash burst (2s cooldown). |
| `U` | Fire any unlocked glyph ultimate (18s cooldown). |
| `1`-`3` | Select upgrades when a level-up prompt appears. |
| `Q` | Quit the run early. |

## Accessibility Support

To keep playtests inclusive while the Unity client is in development, the arcade
loop now exposes accessibility toggles directly from the CLI:

| Option | Effect |
| ------ | ------ |
| `--assist-radius <float>` | Widens projectile hit checks for players who benefit from auto-aim. |
| `--damage-multiplier <float>` | Scales incoming damage; values below `1.0` reduce pressure. |
| `--speed-scale <float>` | Slows or speeds overall simulation time to accommodate reaction needs. |
| `--projectile-speed <float>` | Adjusts projectile velocity so inputs remain readable on lower framerates. |
| `--high-contrast` | Swaps the ASCII palette for high-contrast glyphs that pop on dim terminals. |
| `--message-log <int>` | Controls how many event messages persist on screen for easier tracking. |

Flags can be combined, and all numeric inputs are clamped to sensible ranges so
the prototype remains stable even when extreme values are supplied. These
options will inform the accessibility matrix that the Unity implementation ships
with later in the roadmap.

## Graphics Engine Bridge

The new `game.graphics` module converts gameplay snapshots into renderer-ready
instructions. It packages placeholder sprites, parallax-aware layers, and camera
helpers so the forthcoming Unity client (or any interim renderer) can ingest the
same data contract:

```python
from game.graphics import GraphicsEngine
from game.interactive import ArcadeEngine, InputFrame

engine = ArcadeEngine(target_duration=30.0)
graphics = GraphicsEngine()

snapshot = engine.step(0.16, InputFrame(move_right=True))
render_frame = engine.render_frame(graphics, snapshot=snapshot)
```

`render_frame.instructions` lists sprite draw calls sorted by z-index, giving the
front end sprite ids, screen positions, scale, and flip metadata. While we wait
for the Unity project to stand up, this bridge keeps combat/system updates
flowing into a structured render feed.

Enemy routing now honours the content lane assignments introduced in the PRD:
ground units hug the cobblestones, air casters swoop between jump arcs, and
ceiling clingers stalk overhead before pouncing. Behaviours such as ranged
volleying, kamikaze dives, and shielded juggernauts push extra pressure that the
combat resolver surfaces inside the encounter notes, giving designers quick
feedback on how mixed-lane waves tax the player.

Enemy spawns escalate with time, use the full enemy library, and award souls to
drive level-ups. The UI renders health, phase, XP, and upgrade prompts so
playtesters can exercise the core loop before the Unity client lands.
