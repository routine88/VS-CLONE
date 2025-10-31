"""Meta progression helpers for Nightfall Survivors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .session import RunResult, score_run


HUNTER_LUNARA_COST = 45
WEAPON_BLOODTHORN_COST = 60
GLYPH_VERDANT_COST = 55
WEAPON_NOCTURNE_COST = 110
HUNTER_AURORA_COST = 120


@dataclass(frozen=True)
class MetaRequirement:
    """Requirement that must be met to unlock a reward."""

    kind: str
    threshold: int = 0


@dataclass(frozen=True)
class RequirementStatus:
    """Snapshot describing whether a requirement was satisfied when unlocked."""

    requirement: MetaRequirement
    met: bool


@dataclass(frozen=True)
class UnlockTelemetry:
    """Telemetry entry recorded whenever an unlock is claimed."""

    unlock_id: str
    run_index: int
    total_playtime: float
    requirements: Tuple[RequirementStatus, ...]


@dataclass(frozen=True)
class Unlockable:
    """Represents a meta progression reward purchasable with sigils."""

    id: str
    name: str
    category: str
    cost: int
    description: str
    requirements: Sequence[MetaRequirement] = ()


@dataclass
class SigilLedger:
    """Track earned sigils and claimed unlocks across runs."""

    balance: int = 0
    unlocked_ids: Set[str] = field(default_factory=set)

    def deposit(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.balance += amount

    def can_afford(self, cost: int) -> bool:
        return cost <= self.balance

    def spend(self, cost: int) -> None:
        if cost < 0:
            raise ValueError("cost must be non-negative")
        if cost > self.balance:
            raise ValueError("insufficient sigils")
        self.balance -= cost

    def mark_unlocked(self, unlock_id: str) -> None:
        self.unlocked_ids.add(unlock_id)

    def is_unlocked(self, unlock_id: str) -> bool:
        return unlock_id in self.unlocked_ids


class MetaProgressionSystem:
    """Coordinates unlock evaluation and currency flow."""

    def __init__(
        self,
        unlocks: Optional[Iterable[Unlockable]] = None,
        ledger: Optional[SigilLedger] = None,
    ) -> None:
        unlock_list = list(unlocks) if unlocks is not None else default_unlocks()
        self._unlocks: Dict[str, Unlockable] = {unlock.id: unlock for unlock in unlock_list}
        self.ledger = ledger or SigilLedger()
        self._runs_recorded = 0
        self._total_playtime = 0.0
        self._unlock_log: List[UnlockTelemetry] = []
        self._last_run_result: Optional[RunResult] = None

    def record_run(self, result: RunResult) -> int:
        """Deposit sigils earned from a completed run."""

        earned = score_run(result)
        self.ledger.deposit(earned)
        self._runs_recorded += 1
        self._total_playtime += max(0.0, float(result.duration))
        self._last_run_result = result
        return earned

    @property
    def runs_recorded(self) -> int:
        """Return the number of runs processed by the meta system."""

        return self._runs_recorded

    @property
    def total_playtime(self) -> float:
        """Return the cumulative playtime of recorded runs in seconds."""

        return self._total_playtime

    @property
    def unlock_log(self) -> Sequence[UnlockTelemetry]:
        """Expose a snapshot of unlock telemetry entries."""

        return tuple(self._unlock_log)

    def available_unlocks(
        self,
        *,
        run_result: Optional[RunResult] = None,
        affordable_only: bool = False,
    ) -> List[Unlockable]:
        """Return unlocks that meet requirements and are not yet claimed."""

        candidates: List[Unlockable] = []
        for unlock in self._unlocks.values():
            if self.ledger.is_unlocked(unlock.id):
                continue
            if affordable_only and not self.ledger.can_afford(unlock.cost):
                continue
            if run_result and not _requirements_met(unlock.requirements, run_result):
                continue
            if unlock.requirements and run_result is None:
                continue
            candidates.append(unlock)
        return sorted(candidates, key=lambda item: item.cost)

    def unlock(self, unlock_id: str, run_result: Optional[RunResult] = None) -> Unlockable:
        """Spend sigils to claim an unlockable reward."""

        unlock = self._unlocks.get(unlock_id)
        if not unlock:
            raise KeyError(unlock_id)
        if self.ledger.is_unlocked(unlock_id):
            raise ValueError(f"unlock '{unlock_id}' already claimed")
        self.ledger.spend(unlock.cost)
        self.ledger.mark_unlocked(unlock_id)
        self._record_unlock(unlock, run_result)
        return unlock

    def unlocked(self) -> List[Unlockable]:
        """Return unlockables already claimed."""

        claimed = [self._unlocks[unlock_id] for unlock_id in self.ledger.unlocked_ids]
        return sorted(claimed, key=lambda item: item.cost)

    def _record_unlock(self, unlock: Unlockable, run_result: Optional[RunResult]) -> None:
        source = run_result or self._last_run_result
        statuses: List[RequirementStatus] = []
        for requirement in unlock.requirements:
            if source is None:
                met = True
            else:
                met = _requirements_met((requirement,), source)
            statuses.append(RequirementStatus(requirement=requirement, met=met))
        entry = UnlockTelemetry(
            unlock_id=unlock.id,
            run_index=self._runs_recorded,
            total_playtime=self._total_playtime,
            requirements=tuple(statuses),
        )
        self._unlock_log.append(entry)


def default_unlocks() -> List[Unlockable]:
    """Provide the default unlock track outlined in the PRD."""

    return [
        Unlockable(
            id="hunter_lunara",
            name="Lunara the Moonshadow",
            category="hunter",
            cost=HUNTER_LUNARA_COST,
            description="Agile huntress specializing in aerial glyph combos.",
            requirements=(MetaRequirement("encounters", threshold=5),),
        ),
        Unlockable(
            id="weapon_bloodthorn",
            name="Bloodthorn Lance",
            category="weapon",
            cost=WEAPON_BLOODTHORN_COST,
            description="Unlock the Bloodthorn Lance, a vampiric spear that rewards aggressive play.",
            requirements=(MetaRequirement("survive"),),
        ),
        Unlockable(
            id="weapon_nocturne",
            name="Nocturne Harp",
            category="weapon",
            cost=WEAPON_NOCTURNE_COST,
            description="Channel haunting chords into piercing shockwaves.",
            requirements=(MetaRequirement("final_boss"),),
        ),
        Unlockable(
            id="glyph_verdant",
            name="Verdant Sigil Set",
            category="glyph",
            cost=GLYPH_VERDANT_COST,
            description="Unlock the Verdant glyph family focused on regeneration.",
            requirements=(MetaRequirement("min_relics", threshold=2),),
        ),
        Unlockable(
            id="hunter_aurora",
            name="Aurora the Dawnbringer",
            category="hunter",
            cost=HUNTER_AURORA_COST,
            description="Support hunter wielding radiant slows and shields.",
            requirements=(
                MetaRequirement("survive"),
                MetaRequirement("encounters", threshold=12),
            ),
        ),
    ]


def _requirements_met(requirements: Sequence[MetaRequirement], run: RunResult) -> bool:
    for requirement in requirements:
        if requirement.kind == "survive" and not run.survived:
            return False
        if requirement.kind == "min_relics" and len(run.relics_collected) < requirement.threshold:
            return False
        if requirement.kind == "final_boss":
            if not (
                run.survived
                and run.final_summary is not None
                and run.final_summary.kind == "final_boss"
            ):
                return False
        if requirement.kind == "encounters" and run.encounters_resolved < requirement.threshold:
            return False
    return True


__all__ = [
    "MetaProgressionSystem",
    "MetaRequirement",
    "RequirementStatus",
    "SigilLedger",
    "UnlockTelemetry",
    "Unlockable",
    "default_unlocks",
]
