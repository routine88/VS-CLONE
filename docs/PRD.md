# Project Requirement Document: "Nightfall Survivors"

## 1. Overview
- **Elevator Pitch:** Nightfall Survivors is a 2D side-scrolling horde survival action game where players battle waves of eldritch creatures, collect souls, and upgrade their hunter with branching abilities to survive until dawn.
- **High-Level Concept:** Fast-paced auto-combat with strategic positioning. The player navigates procedurally stitched arenas, leveraging passive and active upgrades that stack into powerful synergies reminiscent of Vampire Survivors, but with a horizontal scrolling focus.
- **Target Platforms:** Windows, macOS, and Linux (Steam release). Future stretch goals include handheld consoles.
- **Game Engine:** Unity (C#) for production; prototype milestone may use an internal gameplay logic sandbox.

## 2. Objectives & Success Metrics
- **Primary Objective:** Deliver a compelling 20-30 minute survival session with escalating tension and replayable upgrade builds.
- **Secondary Objectives:**
  - Achieve >70 Metacritic equivalent score from press previews.
  - Reach a 70% positive review ratio during Early Access.
  - Retain 40% of players through three complete runs during first week post-launch.
- **KPIs:** Daily active users, average run duration, upgrade diversity (unique combination per run), difficulty retention curve, monetization conversion rate for cosmetic DLC.

## 3. Target Audience
- Fans of Vampire Survivors and bullet heaven titles.
- Action-roguelite enthusiasts aged 18-40.
- Streamers seeking high replayability and highlight moments.

## 4. Competitive Analysis
- **Vampire Survivors:** Core inspiration. We differentiate via side-scrolling traversal and environmental hazards.
- **20 Minutes Till Dawn:** Similar dusk theme; we add horizontal map control and mid-run weapon crafting.
- **Scarlet Tower:** Shares gothic theme; Nightfall Survivors emphasizes environmental interactivity (breakable barricades, traps).

## 5. Gameplay Pillars
1. **Relentless Momentum:** Constant forward scrolling arenas demand positioning decisions.
2. **Synergistic Growth:** Layered upgrade paths that combine weapons with glyph modifiers.
3. **Reactive Environment:** Dynamic weather, traps, and destructibles create tactical opportunities.
4. **Pick-up & Play:** Runs last 20 minutes with intuitive controls, but mastery is deep.

## 6. Core Game Loop
1. Spawn into dusk zone with starter weapon.
2. Defeat hordes to collect soul shards.
3. Reach experience thresholds to level up.
4. Choose from three upgrade cards (weapons, glyph modifiers, or survivability perks).
5. Unlock ultimate ability after four glyphs.
6. Fight minibosses every five minutes for relic rewards.
7. Survive until dawn or fall to the horde.

## 7. Mechanics & Systems
### 7.1 Player Controls & Movement
- **Inputs:** Left/right movement, jump/dash, manual ultimate activation, interact.
- **Movement Model:** Constant forward scrolling with backward resistance; players can slow scroll to engage waves.

### 7.2 Combat
- **Weapons:** Auto-triggered attacks with cooldowns (e.g., crossbow burst, chain whip). Additional weapons unlock as upgrades.
- **Projectiles:** Travel horizontally with limited vertical tracking; piercing and boomerang variants.
- **Collision:** Player takes contact damage with brief invulnerability.

### 7.3 Upgrades & Progression
- **Soul Shards:** Experience currency dropped by enemies.
- **Level Ups:** Offer three random upgrades out of owned weapon pool + glyphs.
- **Glyph System:** Passive modifiers in themed sets (e.g., Blood, Shadow, Storm). Completing a set grants an ultimate.
- **Relics:** Permanent run-specific buffs dropped by minibosses.
- **Meta Progression:** Unlock new hunters, weapons, and glyph sets via earned sigils across runs.

### 7.4 Enemies & Bosses
- **Enemy Archetypes:** Swarmers, bruisers, ranged casters, kamikaze.
- **AI Behavior:** Simple pursuit with lane-based variety; some enemies cling to ceilings.
- **Bosses:** Miniboss every 5 minutes (unique telegraph), final dawn boss with multi-phase mechanics.

### 7.5 Environment
- **Biomes:** Graveyard, Abandoned Village, Moonlit Forest. Each with unique hazards (spike traps, collapsing platforms).
- **Interactive Elements:** Destructible barricades dropping resources; weather events (fog reduces visibility).

### 7.6 Session Structure
- **Run Duration:** 20 minutes to dawn, segmented into 4 five-minute phases.
- **Difficulty Scaling:** Enemy density, speed, and elite modifiers ramp per phase.
- **Fail State:** HP depletion; players can spend meta currency to unlock revive blessings for future runs.

## 8. Content Scope
- **Hunters at Launch:** 4 unique characters with signature weapons.
- **Weapons:** 10 base weapons, each with 4 upgrade tiers.
- **Glyph Sets:** 6 sets (Blood, Storm, Clockwork, Frost, Inferno, Verdant).
- **Relics:** 20 run-specific relics.
- **Enemies:** 12 base types + 4 elites + 4 minibosses + 1 final boss.

## 9. Art & Audio Direction
- **Visual Style:** Pixel art with high-contrast silhouettes, parallax backgrounds, gothic neon palette.
- **Animation:** 8-direction sprite sheets for characters; procedural bone attachments for large enemies.
- **Audio:** Adaptive synth-wave soundtrack, layered enemy FX, responsive hit cues, accessibility toggles.

## 10. Technical Requirements
- **Engine:** Unity 2022 LTS, URP.
- **Multiplatform Build Targets:** PC first, future mobile in evaluation.
- **Save System:** Encrypted JSON with cloud sync via Steam.
- **Performance Targets:** 60 FPS on low-spec laptops (GTX 1050 equivalent).
- **Localization:** English at launch; support for subtitles and UI strings localization ready.

## 11. Monetization & Pricing
- **Base Price:** $9.99 USD.
- **Monetization:** Cosmetic-only DLC packs (character skins, effect recolors). No loot boxes.
- **Demo:** 10-minute run preview with two hunters.

## 12. Live Operations & Community
- **Early Access Roadmap:** Quarterly content updates introducing new hunters, biomes, and glyph sets.
- **Events:** Seasonal events (Harvest Moon, Blood Eclipse) with time-limited challenges.
- **Community Tools:** In-game challenge builder exporting shareable codes.

## 13. Production Roadmap
| Milestone | Duration | Deliverables |
|-----------|----------|--------------|
| Concept Validation | 4 weeks | Paper design, graybox prototype of movement/combat. |
| Vertical Slice | 12 weeks | Playable graveyard biome, 2 hunters, 4 weapons, core upgrade loop. |
| Content Expansion | 16 weeks | Additional biomes, weapons, enemy variants, meta progression systems. |
| Polish & Launch Prep | 8 weeks | Optimization, QA, localization, marketing assets. |
| Early Access Launch | Week 40 | Steam Early Access release. |

## 14. Risks & Mitigations
- **Scope Creep:** Prioritize vertical slice; use modular content pipeline.
- **Replayability Burnout:** Invest in glyph synergy system and dynamic events.
- **Technical Debt:** Establish code standards, weekly refactor windows.

## 15. Open Questions
- Will co-op be in scope for Early Access? (TBD post vertical slice).
- Need to evaluate accessibility options (colorblind filters, auto-aim assist levels).
- Decide on roguelite meta progression currency pacing.

