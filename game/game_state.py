"""Top-level state machine for the Nightfall Survivors logic prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from . import config
from .combat import CombatResolver, CombatSummary
from .entities import GlyphFamily, Player, UpgradeCard, UpgradeType
from .environment import EnvironmentDirector, HazardEvent
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

    def tick(self, delta_time: float) -> List[HazardEvent]:
        """Advance the simulation clock and update phase transitions."""

        if delta_time <= 0:
            raise ValueError("delta_time must be positive")

        self.time_elapsed += delta_time
        phase = min(4, int(self.time_elapsed // 300) + 1)
        if phase != self.current_phase:
            self.current_phase = phase
            self.event_log.append(GameEvent(f"Phase advanced to {phase}."))

        hazards = self.environment_director.update(self.current_phase, delta_time)
        if hazards:
            self.active_hazards.extend(hazards)
            for hazard in hazards:
                self.player.health = max(0, self.player.health - hazard.damage)
                self.event_log.append(
                    GameEvent(
                        f"Hazard triggered: {hazard.name} in the {hazard.biome} (-{hazard.damage} HP)."
                    )
                )
                if hazard.slow > 0:
                    percent = int(hazard.slow * 100)
                    self.event_log.append(
                        GameEvent(
                            f"Movement hindered by {hazard.name}: speed reduced by {percent}% for {hazard.duration:.0f}s."
                        )
                    )
                if self.player.health == 0:
                    self.event_log.append(GameEvent("The hunter is overwhelmed by the environment."))
                    break

        return hazards

    def grant_experience(self, amount: int) -> List[GameEvent]:
        """Grant experience and log resulting events."""

        notifications = resolve_experience_gain(self.player, amount)
        events = [GameEvent(note) for note in notifications]
        self.event_log.extend(events)
        return events

    def draw_upgrades(self) -> Sequence[UpgradeCard]:
        """Draw upgrade options for the next level-up."""

        options = self.upgrade_deck.draw_options()
        self.event_log.append(GameEvent("Upgrade options presented."))
        return options

    def apply_upgrade(self, card: UpgradeCard) -> None:
        completed_sets = self.player.apply_upgrade(card)
        if card.type is UpgradeType.GLYPH and card.glyph_family:
            if completed_sets:
                for family in completed_sets:
                    self.event_log.append(GameEvent(f"Ultimate unlocked for {family.value}!"))
            else:
                self.event_log.append(GameEvent(f"Glyph added: {card.glyph_family.value}"))
        elif card.type is UpgradeType.WEAPON:
            self.event_log.append(GameEvent(f"Weapon upgraded: {card.name} tier {card.weapon_tier}"))
        else:
            self.event_log.append(GameEvent(f"Survival perk acquired: {card.name}"))

    def next_encounter(self) -> "Encounter":
        """Generate the next encounter for the active phase."""

        encounter = self.encounter_director.next_encounter(self.current_phase)
        if encounter.kind == "wave" and encounter.wave:
            count = len(encounter.wave.enemies)
            number = encounter.wave.wave_index + 1
            self.event_log.append(GameEvent(f"Wave {number} incoming with {count} foes."))
        elif encounter.kind == "miniboss" and encounter.miniboss:
            self.event_log.append(GameEvent(f"Miniboss {encounter.miniboss.name} approaches!"))
            if encounter.relic_reward:
                self.player.relics.append(encounter.relic_reward)
                self.event_log.append(GameEvent(f"Relic acquired: {encounter.relic_reward}"))
        return encounter

    def final_encounter(self) -> "Encounter":
        """Summon the final boss encounter once dawn is near."""

        encounter = self.encounter_director.final_encounter()
        if encounter.boss_phases:
            base_name = encounter.boss_phases[0].name.split(" (")[0]
            self.event_log.append(
                GameEvent(f"The final boss {base_name} descends for the last stand.")
            )
        else:
            self.event_log.append(GameEvent("The final confrontation begins."))
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
        self.event_log.append(
            GameEvent(
                f"Resolved {label} defeating {summary.enemies_defeated} foes in {summary.duration:.1f}s."
            )
        )
        if summary.damage_taken or summary.healing_received:
            self.event_log.append(
                GameEvent(
                    f"Combat aftermath: -{summary.damage_taken} HP, +{summary.healing_received} HP."
                )
            )
        for note in summary.notes:
            self.event_log.append(GameEvent(note))

        if self.player.health == 0:
            self.event_log.append(GameEvent("The hunter succumbs to the onslaught."))
        elif encounter.kind == "final_boss":
            self.event_log.append(GameEvent("Dawn breaks! The hunter endures the night."))

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

