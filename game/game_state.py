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
    upgrade_deck: UpgradeDeck = field(default_factory=lambda: UpgradeDeck(_default_cards()))
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


def _default_cards() -> List[UpgradeCard]:
    return [
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
            name="Reinforced Plating",
            description="Increase max health by 20.",
            type=UpgradeType.SURVIVAL,
            modifiers={"max_health": 20},
        ),
        UpgradeCard(
            name="Dusk Repeater",
            description="Upgrade the Dusk Repeater to tier 2, firing extra bolts.",
            type=UpgradeType.WEAPON,
            weapon_tier=2,
        ),
        UpgradeCard(
            name="Gloom Chakram",
            description="Unlock the Gloom Chakram, a bouncing blade of shadow.",
            type=UpgradeType.WEAPON,
            weapon_tier=1,
        ),
        UpgradeCard(
            name="Storm Siphon",
            description="Harness the Storm Siphon to unleash piercing beams.",
            type=UpgradeType.WEAPON,
            weapon_tier=1,
        ),
    ]

