"""Live-ops scheduling helpers for Nightfall Survivors.

The PRD outlines seasonal events and community touch points. While the Python
prototype cannot run the full service stack, this module provides data
structures and utilities that model the live calendar so tuning can be
prototyped alongside gameplay systems.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - narrow imports for type checking
    from .game_state import GameState


@dataclass(frozen=True)
class SeasonalEvent:
    """Represents a limited-time seasonal event."""

    id: str
    name: str
    start: datetime
    end: datetime
    description: str
    enemy_density_multiplier: float = 1.0
    hazard_damage_multiplier: float = 1.0
    salvage_multiplier: float = 1.0
    featured_relics: Tuple[str, ...] = ()
    cosmetic_bundle: Optional[str] = None

    def is_active(self, moment: Optional[datetime] = None) -> bool:
        """Return whether the event is active at *moment*."""

        now = moment or datetime.now(timezone.utc)
        return self.start <= now < self.end


def _anchor_for_year(year: int) -> datetime:
    return datetime(year, 1, 1, tzinfo=timezone.utc)


def seasonal_schedule(year: Optional[int] = None) -> List[SeasonalEvent]:
    """Return the live-ops seasonal schedule for the provided year."""

    if year is None:
        year = datetime.now(timezone.utc).year

    anchor = _anchor_for_year(year)

    harvest_moon = SeasonalEvent(
        id="harvest_moon",
        name="Harvest Moon Offensive",
        start=anchor + timedelta(days=258),
        end=anchor + timedelta(days=272),
        description=(
            "Enemy tides surge beneath the crimson moon. Expect denser waves and"
            " boosted salvage as villagers rally behind the hunter."
        ),
        enemy_density_multiplier=1.25,
        hazard_damage_multiplier=1.1,
        salvage_multiplier=1.3,
        featured_relics=("Moonlit Sigil", "Harvest Totem"),
        cosmetic_bundle="Lunar Vanguard Pack",
    )

    blood_eclipse = SeasonalEvent(
        id="blood_eclipse",
        name="Blood Eclipse Siege",
        start=anchor + timedelta(days=319),
        end=anchor + timedelta(days=333),
        description=(
            "The Dawn Revenant's cultists flood the lanes. Hazards sting harder"
            " but relic caches are abundant for daring survivors."
        ),
        enemy_density_multiplier=1.15,
        hazard_damage_multiplier=1.2,
        salvage_multiplier=1.4,
        featured_relics=("Crimson Chalice", "Eclipse Dial"),
        cosmetic_bundle="Bloodforged Arsenal",
    )

    frostfall = SeasonalEvent(
        id="frostfall_jubilee",
        name="Frostfall Jubilee",
        start=anchor + timedelta(days=354),
        end=_anchor_for_year(year + 1) + timedelta(days=6),
        description=(
            "A celebratory respite introduces glacial hazards but rewards longer"
            " survival with rich salvage caches."
        ),
        enemy_density_multiplier=0.85,
        hazard_damage_multiplier=0.9,
        salvage_multiplier=1.6,
        featured_relics=("Aurora Prism", "Frostbound Idol"),
        cosmetic_bundle="Winterlight Ensemble",
    )

    events = [harvest_moon, blood_eclipse, frostfall]
    events.sort(key=lambda event: event.start)
    return events


def find_event(event_id: str, events: Iterable[SeasonalEvent]) -> SeasonalEvent:
    """Locate an event by id within *events*."""

    for event in events:
        if event.id == event_id:
            return event
    raise ValueError(f"unknown seasonal event id: {event_id}")


def active_event(
    events: Sequence[SeasonalEvent], moment: Optional[datetime] = None
) -> Optional[SeasonalEvent]:
    """Return the event active at *moment*, if any."""

    for event in events:
        if event.is_active(moment):
            return event
    return None


def activate_event(state: GameState, event: SeasonalEvent) -> None:
    """Apply event modifiers to a :class:`GameState`."""

    from .game_state import GameEvent  # local import to avoid cycles

    state.spawn_director.apply_event_modifiers(
        density_multiplier=event.enemy_density_multiplier
    )
    state.environment_director.apply_event_modifiers(
        hazard_damage_scale=event.hazard_damage_multiplier,
        salvage_scale=event.salvage_multiplier,
        resource_scale=event.salvage_multiplier,
    )
    state.event_log.append(
        GameEvent(
            f"Seasonal event active: {event.name} — {event.description}"
        )
    )


def _format_event(event: SeasonalEvent) -> str:
    featured = ", ".join(event.featured_relics) if event.featured_relics else "None"
    bundle = event.cosmetic_bundle or "None"
    return (
        f"{event.name} ({event.id})\n"
        f"  Window: {event.start.date()} → {event.end.date()}\n"
        f"  Density ×{event.enemy_density_multiplier:.2f} | Hazards ×{event.hazard_damage_multiplier:.2f} |"
        f" Salvage ×{event.salvage_multiplier:.2f}\n"
        f"  Featured Relics: {featured}\n"
        f"  Cosmetic Bundle: {bundle}\n"
        f"  {event.description}"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for ``python -m game.live_ops``."""

    parser = argparse.ArgumentParser(description="Inspect Nightfall Survivors seasonal events.")
    parser.add_argument("--year", type=int, help="Optional year to inspect")
    parser.add_argument(
        "--active",
        action="store_true",
        help="Only show the event active right now.",
    )
    parser.add_argument(
        "--event-id",
        help="Print details for a specific event id and exit.",
    )
    args = parser.parse_args(argv)

    events = seasonal_schedule(args.year)

    if args.event_id:
        event = find_event(args.event_id, events)
        print(_format_event(event))
        return 0

    if args.active:
        event = active_event(events)
        if event is None:
            print("No seasonal event is active right now.")
        else:
            print(_format_event(event))
        return 0

    for event in events:
        print(_format_event(event))
        print()
    return 0


__all__ = [
    "SeasonalEvent",
    "activate_event",
    "active_event",
    "find_event",
    "seasonal_schedule",
]

