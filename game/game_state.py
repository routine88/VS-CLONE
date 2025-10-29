"""Top-level state machine for the Nightfall Survivors logic prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from . import config
from .combat import CombatResolver, CombatSummary
from .entities import GlyphFamily, Player, UpgradeCard, UpgradeType
from .environment import (
    EnvironmentDirector,
    EnvironmentTickResult,
    HazardEvent,
    WeatherEvent,
)
from .localization import Translator, get_translator
from .systems import EncounterDirector, SpawnDirector, UpgradeDeck, resolve_experience_gain


@dataclass
class GameEvent:
    """Represents a significant game event for logging or UI."""

    message: str


@dataclass
class GameState:
    """Encapsulates the mutable state of a single survival run."""

    player: Player = field(default_factory=Player)
    time_elapsed: float = 0.0
    current_phase: int = 1
    spawn_director: SpawnDirector = field(default_factory=SpawnDirector)
    upgrade_deck: UpgradeDeck = field(default_factory=lambda: UpgradeDeck(default_upgrade_cards()))
    encounter_director: EncounterDirector = field(default_factory=EncounterDirector)
    environment_director: EnvironmentDirector = field(default_factory=EnvironmentDirector)
    combat_resolver: CombatResolver = field(default_factory=CombatResolver)
    event_log: List[GameEvent] = field(default_factory=list)
    active_hazards: List[HazardEvent] = field(default_factory=list)
    active_weather: WeatherEvent | None = None
    translator: Translator = field(default_factory=get_translator)

    def _log(self, key: str, **params) -> None:
        self.event_log.append(GameEvent(self.translator.translate(key, **params)))

    def tick(self, delta_time: float) -> EnvironmentTickResult:
        """Advance the simulation clock and update phase transitions."""

        if delta_time <= 0:
            raise ValueError("delta_time must be positive")

        self.time_elapsed += delta_time
        phase = min(4, int(self.time_elapsed // 300) + 1)
        if phase != self.current_phase:
            self.current_phase = phase
            self._log("game.phase_advance", phase=phase)

        environment_changes = self.environment_director.update(self.current_phase, delta_time)
        hazards = environment_changes.hazards
        if hazards:
            self.active_hazards.extend(hazards)
            for hazard in hazards:
                self.player.health = max(0, self.player.health - hazard.damage)
                self._log(
                    "game.hazard_trigger",
                    name=hazard.name,
                    biome=hazard.biome,
                    damage=hazard.damage,
                )
                if hazard.slow > 0:
                    percent = int(hazard.slow * 100)
                    duration = int(round(hazard.duration))
                    self._log(
                        "game.hazard_slow",
                        name=hazard.name,
                        percent=percent,
                        duration=duration,
                    )
                if self.player.health == 0:
                    self._log("game.environment_defeat")
                    break

        if environment_changes.barricades:
            for barricade in environment_changes.barricades:
                self.player.add_salvage(barricade.salvage_reward)
                self._log(
                    "game.barricade_cleared",
                    name=barricade.name,
                    salvage=barricade.salvage_reward,
                )

        if environment_changes.resource_drops:
            for cache in environment_changes.resource_drops:
                self.player.add_salvage(cache.amount)
                self._log(
                    "game.salvage_collected",
                    name=cache.name,
                    amount=cache.amount,
                )

        if environment_changes.weather_events:
            for weather_event in environment_changes.weather_events:
                if weather_event.ended:
                    self.active_weather = None
                    self._log("game.weather_clear")
                else:
                    self.active_weather = weather_event
                    move_percent = int(weather_event.movement_modifier * 100)
                    vision_percent = int(weather_event.vision_modifier * 100)
                    descriptor = weather_event.description
                    self._log(
                        "game.weather_change",
                        name=weather_event.name,
                        description=descriptor,
                        movement=move_percent,
                        vision=vision_percent,
                    )

        return environment_changes

    def grant_experience(self, amount: int) -> List[GameEvent]:
        """Grant experience and log resulting events."""

        notifications = resolve_experience_gain(self.player, amount, translator=self.translator)
        events = [GameEvent(note) for note in notifications]
        self.event_log.extend(events)
        return events

    def draw_upgrades(self) -> Sequence[UpgradeCard]:
        """Draw upgrade options for the next level-up."""

        options = self.upgrade_deck.draw_options()
        self._log("game.upgrade_presented")
        return options

    def apply_upgrade(self, card: UpgradeCard) -> None:
        completed_sets = self.player.apply_upgrade(card)
        if card.type is UpgradeType.GLYPH and card.glyph_family:
            if completed_sets:
                for family in completed_sets:
                    self._log("game.glyph_unlocked", family=family.value)
            else:
                self._log("game.glyph_added", family=card.glyph_family.value)
        elif card.type is UpgradeType.WEAPON:
            self._log("game.weapon_upgraded", name=card.name, tier=card.weapon_tier)
        else:
            self._log("game.perk_acquired", name=card.name)

    def next_encounter(self) -> "Encounter":
        """Generate the next encounter for the active phase."""

        encounter = self.encounter_director.next_encounter(self.current_phase)
        if encounter.kind == "wave" and encounter.wave:
            count = len(encounter.wave.enemies)
            number = encounter.wave.wave_index + 1
            self._log("game.wave_incoming", number=number, count=count)
        elif encounter.kind == "miniboss" and encounter.miniboss:
            self._log("game.miniboss_incoming", name=encounter.miniboss.name)
            if encounter.relic_reward:
                self.player.relics.append(encounter.relic_reward)
                self._log("game.relic_acquired", name=encounter.relic_reward)
        return encounter

    def final_encounter(self) -> "Encounter":
        """Summon the final boss encounter once dawn is near."""

        encounter = self.encounter_director.final_encounter()
        if encounter.boss_phases:
            base_name = encounter.boss_phases[0].name.split(" (")[0]
            self._log("game.final_boss", name=base_name)
        else:
            self._log("game.final_boss_generic")
        return encounter

    def resolve_encounter(self, encounter: "Encounter") -> CombatSummary:
        """Resolve combat for the provided encounter and update the run state."""

        if encounter.kind == "wave" and encounter.wave:
            summary = self.combat_resolver.resolve_wave(self.player, encounter.wave)
        elif encounter.kind == "miniboss" and encounter.miniboss:
            summary = self.combat_resolver.resolve_miniboss(self.player, encounter.miniboss)
        elif encounter.kind == "final_boss" and encounter.boss_phases:
            summary = self.combat_resolver.resolve_final_boss(self.player, encounter.boss_phases)
        else:
            raise ValueError("Encounter missing data for resolution")

        self.player.health = max(0, self.player.health - summary.damage_taken)
        if summary.healing_received:
            self.player.health = min(self.player.max_health, self.player.health + summary.healing_received)

        if summary.souls_gained:
            self.grant_experience(summary.souls_gained)

        label = summary.kind.replace("_", " ")
        self._log(
            "game.encounter_resolved",
            label=label,
            count=summary.enemies_defeated,
            duration=summary.duration,
        )
        if summary.damage_taken or summary.healing_received:
            self._log(
                "game.encounter_aftermath",
                damage=summary.damage_taken,
                healing=summary.healing_received,
            )
        for note in summary.notes:
            self.event_log.append(GameEvent(note))

        if self.player.health == 0:
            self._log("game.player_fallen")
        elif encounter.kind == "final_boss":
            self._log("game.player_survived")

        return summary


_WEAPON_CARD_DEFINITIONS = {
    "Dusk Repeater": {
        2: "Upgrade the Dusk Repeater to tier 2, firing extra bolts.",
        3: "Enhance the Dusk Repeater to tier 3, tightening spread and power.",
        4: "Max out the Dusk Repeater at tier 4 for relentless triple volleys.",
    },
    "Gloom Chakram": {
        1: "Unlock the Gloom Chakram, a bouncing blade of shadow.",
        2: "Refine the Gloom Chakram to tier 2 for twin ricochets.",
        3: "Empower the Gloom Chakram to tier 3, widening its spiral.",
        4: "Ascend the Gloom Chakram to tier 4, unleashing a trio of blades.",
    },
    "Storm Siphon": {
        1: "Harness the Storm Siphon to unleash piercing beams.",
        2: "Amplify the Storm Siphon to tier 2 for chained arcs.",
        3: "Elevate the Storm Siphon to tier 3, multiplying conduits.",
        4: "Overcharge the Storm Siphon to tier 4, releasing tempest barrages.",
    },
    "Nocturne Harp": {
        1: "Unlock the Nocturne Harp, summoning spectral chords.",
        2: "Tune the Nocturne Harp to tier 2 for layered harmonics.",
        3: "Resonate the Nocturne Harp to tier 3, echoing through crowds.",
        4: "Master the Nocturne Harp at tier 4, conducting spirit choirs.",
    },
    "Bloodthorn Lance": {
        1: "Claim the Bloodthorn Lance, a brutal piercing thrust.",
        2: "Temper the Bloodthorn Lance to tier 2 for deeper impalements.",
        3: "Enrage the Bloodthorn Lance to tier 3, draining foes swiftly.",
        4: "Crown the Bloodthorn Lance at tier 4 with devastating reach.",
    },
    "Gravebloom Staff": {
        1: "Channel the Gravebloom Staff, seeding necrotic blooms.",
        2: "Empower the Gravebloom Staff to tier 2 for extra spores.",
        3: "Envenom the Gravebloom Staff to tier 3, lingering longer.",
        4: "Awaken the Gravebloom Staff at tier 4 to carpet the field.",
    },
    "Tempest Gauntlet": {
        1: "Equip the Tempest Gauntlet for rapid shock strikes.",
        2: "Stabilize the Tempest Gauntlet to tier 2 for dual jabs.",
        3: "Ignite the Tempest Gauntlet to tier 3, chaining surges.",
        4: "Ascend the Tempest Gauntlet at tier 4 with triple storms.",
    },
    "Frostbrand Edge": {
        1: "Wield the Frostbrand Edge to cleave with chilling arcs.",
        2: "Hone the Frostbrand Edge to tier 2, biting deeper.",
        3: "Empower the Frostbrand Edge to tier 3 for twin slashes.",
        4: "Crown the Frostbrand Edge at tier 4, freezing whole ranks.",
    },
    "Inferno Lantern": {
        1: "Kindle the Inferno Lantern, scattering flame wisps.",
        2: "Stoke the Inferno Lantern to tier 2 for denser embers.",
        3: "Unleash the Inferno Lantern at tier 3, prolonging burns.",
        4: "Overheat the Inferno Lantern to tier 4, flooding fire spirits.",
    },
    "Umbral Coil": {
        1: "Bind the Umbral Coil to lash erratic shadows.",
        2: "Tighten the Umbral Coil to tier 2, splitting lashes.",
        3: "Empower the Umbral Coil to tier 3 for triple snaps.",
        4: "Unfurl the Umbral Coil at tier 4, saturating every lane.",
    },
}


def default_upgrade_cards() -> List[UpgradeCard]:
    cards = [
        UpgradeCard(
            name="Blood Sigil",
            description="Add a blood glyph, increasing life steal potential.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.BLOOD,
        ),
        UpgradeCard(
            name="Storm Sigil",
            description="Add a storm glyph, improving chain lightning chance.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.STORM,
        ),
        UpgradeCard(
            name="Frost Sigil",
            description="Add a frost glyph, bolstering damage mitigation.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.FROST,
        ),
        UpgradeCard(
            name="Inferno Sigil",
            description="Add an inferno glyph, empowering damage output.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.INFERNO,
        ),
        UpgradeCard(
            name="Clockwork Sigil",
            description="Add a clockwork glyph, enhancing cooldown reduction.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.CLOCKWORK,
        ),
        UpgradeCard(
            name="Verdant Sigil",
            description="Add a verdant glyph, amplifying regeneration.",
            type=UpgradeType.GLYPH,
            glyph_family=GlyphFamily.VERDANT,
        ),
        UpgradeCard(
            name="Reinforced Plating",
            description="Increase max health by 20.",
            type=UpgradeType.SURVIVAL,
            modifiers={"max_health": 20},
        ),
    ]

    for weapon, tiers in _WEAPON_CARD_DEFINITIONS.items():
        for tier in sorted(tiers):
            cards.append(
                UpgradeCard(
                    name=weapon,
                    description=tiers[tier],
                    type=UpgradeType.WEAPON,
                    weapon_tier=tier,
                )
            )
    return cards

