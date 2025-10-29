"""Distribution and demo-mode helpers for Nightfall Survivors.

The PRD calls for a downloadable demo with limited content plus PC build
targets across Steam platforms. This module codifies those requirements so the
prototype can simulate demo constraints and surface the supported build
matrix for tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Optional, Sequence, Set, TYPE_CHECKING

from . import config

if TYPE_CHECKING:  # pragma: no cover - import guarded for typing only
    from .profile import PlayerProfile
    from .session import RunSimulator


class Platform(Enum):
    """Enumerates PC build targets outlined in the PRD."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


@dataclass(frozen=True)
class BuildTarget:
    """Represents a single distributable build configuration."""

    platform: Platform
    architecture: str
    graphics_api: str
    steam_app_id: int
    demo_supported: bool = True


def default_build_matrix() -> Dict[Platform, BuildTarget]:
    """Return the default PC build targets for Steam distribution."""

    return {
        Platform.WINDOWS: BuildTarget(
            platform=Platform.WINDOWS,
            architecture="x86_64",
            graphics_api="DirectX 11",
            steam_app_id=313370,
            demo_supported=True,
        ),
        Platform.MACOS: BuildTarget(
            platform=Platform.MACOS,
            architecture="universal",
            graphics_api="Metal",
            steam_app_id=313371,
            demo_supported=True,
        ),
        Platform.LINUX: BuildTarget(
            platform=Platform.LINUX,
            architecture="x86_64",
            graphics_api="Vulkan",
            steam_app_id=313372,
            demo_supported=True,
        ),
    }


def validate_build_targets(targets: Iterable[BuildTarget]) -> None:
    """Ensure build targets have unique Steam IDs and platforms."""

    seen_ids: Set[int] = set()
    seen_platforms: Set[Platform] = set()
    for target in targets:
        if target.platform in seen_platforms:
            raise ValueError(f"duplicate build platform: {target.platform.value}")
        if target.steam_app_id in seen_ids:
            raise ValueError(f"duplicate Steam app id: {target.steam_app_id}")
        seen_platforms.add(target.platform)
        seen_ids.add(target.steam_app_id)


@dataclass(frozen=True)
class DemoRestrictions:
    """Limits applied to the public demo build."""

    max_duration: float = 600.0
    allowed_hunters: Optional[Sequence[str]] = None
    weapon_limit: Optional[int] = 4
    glyph_limit: Optional[int] = 3

    def normalised_hunters(self) -> Optional[Set[str]]:
        if self.allowed_hunters is None:
            return None
        cleaned = {hunter.strip() for hunter in self.allowed_hunters if hunter.strip()}
        return cleaned or None


def default_demo_restrictions() -> DemoRestrictions:
    """Return the default constraints for the vertical-slice demo."""

    return DemoRestrictions(
        max_duration=600.0,
        allowed_hunters=("hunter_varik", "hunter_mira"),
        weapon_limit=4,
        glyph_limit=3,
    )


def apply_demo_restrictions(profile: PlayerProfile, restrictions: DemoRestrictions) -> None:
    """Clamp the supplied profile to the demo's content limits."""

    allowed = restrictions.normalised_hunters()
    if allowed is not None:
        owned = profile.owned_hunters & allowed
        if not owned:
            raise ValueError("demo restrictions do not include any owned hunters")
        profile.owned_hunters = owned
        if profile.active_hunter not in owned:
            profile.active_hunter = next(iter(sorted(owned)))

    if restrictions.weapon_limit is not None:
        if restrictions.weapon_limit <= 0:
            raise ValueError("weapon_limit must be positive")
        cards = sorted(profile.available_weapon_cards)
        profile.available_weapon_cards = set(cards[: restrictions.weapon_limit])
        if not profile.available_weapon_cards:
            raise ValueError("demo restrictions removed all weapon cards")

    if restrictions.glyph_limit is not None:
        if restrictions.glyph_limit <= 0:
            raise ValueError("glyph_limit must be positive")
        glyphs = sorted(profile.available_glyph_families, key=lambda g: g.name)
        profile.available_glyph_families = set(glyphs[: restrictions.glyph_limit])
        if not profile.available_glyph_families:
            raise ValueError("demo restrictions removed all glyph families")


def configure_simulator_for_demo(simulator: RunSimulator, restrictions: DemoRestrictions) -> None:
    """Apply runtime limits to a :class:`RunSimulator` for demo sessions."""

    simulator.total_duration = min(simulator.total_duration, restrictions.max_duration)
    simulator.tick_step = min(simulator.tick_step, max(1.0, restrictions.max_duration / 120))


def demo_duration(default: float | None = None, restrictions: DemoRestrictions | None = None) -> float:
    """Return the session duration that should be used for demo runs."""

    base = default if default is not None else config.RUN_DURATION_SECONDS
    if restrictions is None:
        return min(base, default_demo_restrictions().max_duration)
    return min(base, restrictions.max_duration)


__all__ = [
    "Platform",
    "BuildTarget",
    "DemoRestrictions",
    "apply_demo_restrictions",
    "configure_simulator_for_demo",
    "default_build_matrix",
    "default_demo_restrictions",
    "demo_duration",
    "validate_build_targets",
]

