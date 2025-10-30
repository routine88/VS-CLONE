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
from typing import Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING, Union

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


@dataclass(frozen=True)
class RoadmapMilestone:
    """Represents a production roadmap milestone from the PRD."""

    id: str
    name: str
    start: datetime
    end: datetime
    deliverables: Tuple[str, ...]
    description: Optional[str] = None

    @property
    def duration_weeks(self) -> float:
        """Return the milestone duration in weeks."""

        delta = self.end - self.start
        return delta.days / 7


@dataclass(frozen=True)
class ContentUpdate:
    """Represents a quarterly Early Access content update."""

    id: str
    name: str
    start: datetime
    end: datetime
    new_hunters: Tuple[str, ...]
    new_biomes: Tuple[str, ...]
    new_glyph_sets: Tuple[str, ...]
    headline_features: Tuple[str, ...]
    description: Optional[str] = None

    @property
    def duration_days(self) -> int:
        """Return the number of days the update campaign spans."""

        return (self.end - self.start).days


ScheduleEntry = Union[SeasonalEvent, RoadmapMilestone, ContentUpdate]


@dataclass(frozen=True)
class AnnualPlan:
    """Aggregate view of the live calendar for a given year."""

    year: int
    events: Tuple[SeasonalEvent, ...]
    milestones: Tuple[RoadmapMilestone, ...]
    updates: Tuple[ContentUpdate, ...]

    def next_items(self, moment: Optional[datetime] = None) -> List[ScheduleEntry]:
        """Return upcoming or active schedule items ordered by start date."""

        now = moment or datetime.now(timezone.utc)
        upcoming: List[ScheduleEntry] = []
        for collection in (self.milestones, self.events, self.updates):
            for item in collection:
                if item.end > now:
                    upcoming.append(item)
        upcoming.sort(key=lambda entry: entry.start)
        return upcoming


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


def roadmap_schedule(year: Optional[int] = None) -> List[RoadmapMilestone]:
    """Return the production roadmap aligned with the PRD for *year*."""

    if year is None:
        year = datetime.now(timezone.utc).year

    anchor = _anchor_for_year(year)

    phases: List[Tuple[str, str, int, Tuple[str, ...], Optional[str]]] = [
        (
            "concept_validation",
            "Concept Validation",
            4,
            ("Paper design", "Graybox prototype of movement/combat"),
            "Validate movement feel and core combat loops.",
        ),
        (
            "vertical_slice",
            "Vertical Slice",
            12,
            (
                "Playable graveyard biome",
                "Two hunters",
                "Four weapons",
                "Core upgrade loop",
            ),
            "Establish the core player experience for internal review.",
        ),
        (
            "content_expansion",
            "Content Expansion",
            16,
            (
                "Additional biomes",
                "Weapon and enemy variants",
                "Meta progression systems",
            ),
            "Build depth and variety ahead of Early Access.",
        ),
        (
            "polish_launch_prep",
            "Polish & Launch Prep",
            8,
            (
                "Optimization",
                "QA",
                "Localization",
                "Marketing assets",
            ),
            "Stabilize the build and prepare marketing beats.",
        ),
    ]

    milestones: List[RoadmapMilestone] = []
    cursor = anchor
    for identifier, name, duration_weeks, deliverables, description in phases:
        start = cursor
        end = start + timedelta(weeks=duration_weeks)
        milestones.append(
            RoadmapMilestone(
                id=identifier,
                name=name,
                start=start,
                end=end,
                deliverables=deliverables,
                description=description,
            )
        )
        cursor = end

    launch_start = anchor + timedelta(weeks=40)
    launch_end = launch_start + timedelta(days=7)
    milestones.append(
        RoadmapMilestone(
            id="early_access_launch",
            name="Early Access Launch",
            start=launch_start,
            end=launch_end,
            deliverables=("Steam Early Access release",),
            description="Initial public release and live-ops kickoff.",
        )
    )

    return milestones


def content_update_schedule(year: Optional[int] = None) -> List[ContentUpdate]:
    """Return the quarterly Early Access content update roadmap."""

    if year is None:
        year = datetime.now(timezone.utc).year

    anchor = _anchor_for_year(year)

    updates: List[ContentUpdate] = []
    for identifier, name, start_offset, duration, hunters, biomes, glyphs, features, description in [
        (
            "q1_shadows_over_ravenspire",
            "Shadows Over Ravenspire",
            74,
            10,
            ("Lyra the Riftstalker",),
            ("Ravenspire Ruins",),
            ("Umbral Sigils",),
            ("Night Trials challenge board", "Elite cultist enemy variant"),
            "Kick off Early Access with infiltration-focused content and ranked challenges.",
        ),
        (
            "q2_gilded_tempest",
            "Gilded Tempest",
            165,
            12,
            ("Darius the Arcanist",),
            ("Sunken Bazaar",),
            ("Stormbound Glyphs",),
            ("Weapon crafting benches", "Seasonal contract system"),
            "Introduce market lanes with weather-reactive hazards and expansion crafting hooks.",
        ),
        (
            "q3_wild_hunt",
            "Wild Hunt",
            258,
            11,
            ("Kaela the Warden",),
            ("Verdant Expanse",),
            ("Verdant Accord",),
            ("Co-op hunt playlists", "Beastmaster enemy family"),
            "Deliver cooperative runs alongside a sprawling forest biome teeming with fauna.",
        ),
        (
            "q4_dawnfall_reckoning",
            "Dawnfall Reckoning",
            360,
            14,
            ("Elias the Daybreaker",),
            ("Celestial Citadel",),
            ("Radiant Choir",),
            ("Ascension finale event", "Glyph rebalance pass"),
            "Close the year with a climactic assault on the Dawn Revenant's stronghold.",
        ),
    ]:
        start = anchor + timedelta(days=start_offset)
        end = start + timedelta(days=duration)
        updates.append(
            ContentUpdate(
                id=identifier,
                name=name,
                start=start,
                end=end,
                new_hunters=hunters,
                new_biomes=biomes,
                new_glyph_sets=glyphs,
                headline_features=features,
                description=description,
            )
        )

    updates.sort(key=lambda update: update.start)
    return updates


def find_event(event_id: str, events: Iterable[SeasonalEvent]) -> SeasonalEvent:
    """Locate an event by id within *events*."""

    for event in events:
        if event.id == event_id:
            return event
    raise ValueError(f"unknown seasonal event id: {event_id}")


def find_milestone(
    milestone_id: str, milestones: Iterable[RoadmapMilestone]
) -> RoadmapMilestone:
    """Locate a milestone by id within *milestones*."""

    for milestone in milestones:
        if milestone.id == milestone_id:
            return milestone
    raise ValueError(f"unknown roadmap milestone id: {milestone_id}")


def find_update(update_id: str, updates: Iterable[ContentUpdate]) -> ContentUpdate:
    """Locate a content update by id within *updates*."""

    for update in updates:
        if update.id == update_id:
            return update
    raise ValueError(f"unknown content update id: {update_id}")


def annual_plan(year: Optional[int] = None) -> AnnualPlan:
    """Return a combined schedule of milestones, events, and updates."""

    if year is None:
        year = datetime.now(timezone.utc).year

    milestones = tuple(roadmap_schedule(year))
    events = tuple(seasonal_schedule(year))
    updates = tuple(content_update_schedule(year))
    return AnnualPlan(year=year, milestones=milestones, events=events, updates=updates)


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


def _format_milestone(milestone: RoadmapMilestone) -> str:
    deliverables = ", ".join(milestone.deliverables)
    description = milestone.description or ""
    return (
        f"{milestone.name} ({milestone.id})\n"
        f"  Window: {milestone.start.date()} → {milestone.end.date()}"
        f" ({milestone.duration_weeks:.1f} weeks)\n"
        f"  Deliverables: {deliverables}\n"
        f"  {description}"
    ).rstrip()


def _format_update(update: ContentUpdate) -> str:
    hunters = ", ".join(update.new_hunters) if update.new_hunters else "None"
    biomes = ", ".join(update.new_biomes) if update.new_biomes else "None"
    glyphs = ", ".join(update.new_glyph_sets) if update.new_glyph_sets else "None"
    features = ", ".join(update.headline_features) if update.headline_features else "None"
    description = update.description or ""
    return (
        f"{update.name} ({update.id})\n"
        f"  Window: {update.start.date()} → {update.end.date()}"
        f" ({update.duration_days} days)\n"
        f"  New Hunters: {hunters}\n"
        f"  New Biomes: {biomes}\n"
        f"  New Glyph Sets: {glyphs}\n"
        f"  Features: {features}\n"
        f"  {description}"
    ).rstrip()


def _format_plan(plan: AnnualPlan, moment: Optional[datetime] = None) -> str:
    now = moment or datetime.now(timezone.utc)
    lines = [
        f"Nightfall Survivors {plan.year} Live Operations Plan",
        "",
        f"Roadmap milestones: {len(plan.milestones)}",
        f"Seasonal events: {len(plan.events)}",
        f"Content updates: {len(plan.updates)}",
        "",
        "Upcoming beats:",
    ]
    upcoming = plan.next_items(now)
    if not upcoming:
        lines.append("  (No remaining beats this year.)")
    else:
        for entry in upcoming[:8]:
            if isinstance(entry, RoadmapMilestone):
                label = "Milestone"
            elif isinstance(entry, ContentUpdate):
                label = "Content Update"
            else:
                label = "Seasonal Event"
            lines.append(
                f"  - {entry.start.date()}: {entry.name} [{label}]"
            )
    return "\n".join(lines)


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
    parser.add_argument(
        "--roadmap",
        action="store_true",
        help="Print the production roadmap instead of seasonal events.",
    )
    parser.add_argument(
        "--milestone-id",
        help="Show details for a specific roadmap milestone when used with --roadmap.",
    )
    parser.add_argument(
        "--updates",
        action="store_true",
        help="Print the Early Access content update schedule.",
    )
    parser.add_argument(
        "--update-id",
        help="Show details for a specific content update (implies --updates).",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Summarise the combined live operations plan for the year.",
    )
    args = parser.parse_args(argv)

    if args.plan:
        plan = annual_plan(args.year)
        print(_format_plan(plan))
        return 0

    if args.roadmap:
        milestones = roadmap_schedule(args.year)
        if args.milestone_id:
            milestone = find_milestone(args.milestone_id, milestones)
            print(_format_milestone(milestone))
            return 0
        for milestone in milestones:
            print(_format_milestone(milestone))
            print()
        return 0

    if args.updates or args.update_id:
        updates = content_update_schedule(args.year)
        if args.update_id:
            update = find_update(args.update_id, updates)
            print(_format_update(update))
            return 0
        for update in updates:
            print(_format_update(update))
            print()
        return 0

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
    "RoadmapMilestone",
    "ContentUpdate",
    "AnnualPlan",
    "activate_event",
    "active_event",
    "find_event",
    "find_milestone",
    "find_update",
    "seasonal_schedule",
    "roadmap_schedule",
    "content_update_schedule",
    "annual_plan",
]


if __name__ == "__main__":  # pragma: no cover - CLI passthrough
    raise SystemExit(main())

