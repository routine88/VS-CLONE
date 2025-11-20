"""Cosmetic monetization helpers aligned with the PRD."""

from __future__ import annotations

import os
LIVE_SERVICES_ENABLED = os.getenv("NIGHTFALL_ENABLE_LIVE_SERVICES") == "1"

if LIVE_SERVICES_ENABLED:
    from dataclasses import dataclass
    from typing import Dict, Iterable, List, Optional, Sequence, Set

    @dataclass(frozen=True)
    class CosmeticItem:
        """Represents a cosmetic reward (skin, VFX, etc)."""

        id: str
        name: str
        category: str
        description: str
        applies_to: Optional[str] = None


    @dataclass(frozen=True)
    class DlcPack:
        """Bundle of cosmetic items sold as DLC."""

        id: str
        name: str
        price: float
        items: Sequence[CosmeticItem]


    class CurrencyWallet:
        """Simple wallet to simulate premium currency spending."""

        def __init__(self, balance: float = 0.0) -> None:
            self.balance = float(balance)

        def deposit(self, amount: float) -> None:
            if amount < 0:
                raise ValueError("cannot deposit a negative amount")
            self.balance += amount

        def charge(self, amount: float) -> None:
            if amount < 0:
                raise ValueError("cannot charge a negative amount")
            if amount > self.balance:
                raise ValueError("insufficient funds to complete purchase")
            self.balance -= amount


    class CosmeticInventory:
        """Tracks owned cosmetics and equipped selections."""

        def __init__(
            self,
            owned: Optional[Iterable[str]] = None,
            equipped: Optional[Dict[str, str]] = None,
        ) -> None:
            self.owned: Set[str] = set(owned or ())
            self.equipped: Dict[str, str] = dict(equipped or {})

        def grant(self, item: CosmeticItem) -> None:
            self.owned.add(item.id)

        def has(self, item_id: str) -> bool:
            return item_id in self.owned

        def equip(self, item: CosmeticItem) -> None:
            if item.id not in self.owned:
                raise ValueError(f"cosmetic '{item.id}' is not owned")
            self.equipped[item.category] = item.id

        def equipped_item(self, category: str) -> Optional[str]:
            return self.equipped.get(category)


    class Storefront:
        """Lightweight cosmetic storefront."""

        def __init__(self, packs: Iterable[DlcPack]) -> None:
            self._packs: Dict[str, DlcPack] = {pack.id: pack for pack in packs}

        def available_packs(self) -> List[DlcPack]:
            return sorted(self._packs.values(), key=lambda pack: pack.price)

        def get_pack(self, pack_id: str) -> DlcPack:
            try:
                return self._packs[pack_id]
            except KeyError as exc:  # pragma: no cover - defensive guard
                raise ValueError(f"unknown DLC pack '{pack_id}'") from exc

        def purchase(self, pack_id: str, wallet: CurrencyWallet, inventory: CosmeticInventory) -> List[CosmeticItem]:
            pack = self.get_pack(pack_id)
            wallet.charge(pack.price)
            granted: List[CosmeticItem] = []
            for item in pack.items:
                inventory.grant(item)
                granted.append(item)
            return granted


    def default_cosmetics() -> Dict[str, CosmeticItem]:
        """Return the base set of cosmetic rewards referenced by DLC packs."""

        items = [
            CosmeticItem(
                id="skin_varik_ashen",
                name="Ashen Nightblade",
                category="hunter_skin",
                description="Varik dons pale armor with ember highlights.",
                applies_to="hunter_varik",
            ),
            CosmeticItem(
                id="skin_mira_tempest",
                name="Tempest Surgebreaker",
                category="hunter_skin",
                description="Stormcaller garb with animated lightning trim.",
                applies_to="hunter_mira",
            ),
            CosmeticItem(
                id="trail_bloodflare",
                name="Bloodflare Dash",
                category="dash_trail",
                description="Dash leaves a crimson comet trail.",
            ),
            CosmeticItem(
                id="ultimate_prismatic",
                name="Prismatic Crescendo",
                category="ultimate_vfx",
                description="Ultimate blooms with spectral petals.",
            ),
        ]
        return {item.id: item for item in items}


    def default_dlc_packs() -> Dict[str, DlcPack]:
        """Return cosmetic DLC bundles matching the monetization plan."""

        cosmetics = default_cosmetics()
        packs = [
            DlcPack(
                id="dlc_founders",
                name="Founder's Wardrobe",
                price=4.99,
                items=[
                    cosmetics["skin_varik_ashen"],
                    cosmetics["trail_bloodflare"],
                ],
            ),
            DlcPack(
                id="dlc_tempest_ritual",
                name="Tempest Ritual Pack",
                price=3.99,
                items=[
                    cosmetics["skin_mira_tempest"],
                    cosmetics["ultimate_prismatic"],
                ],
            ),
        ]
        return {pack.id: pack for pack in packs}


    __all__ = [
        "CosmeticInventory",
        "CosmeticItem",
        "CurrencyWallet",
        "DlcPack",
        "Storefront",
        "default_cosmetics",
        "default_dlc_packs",
    ]

else:  # pragma: no cover - guarded imports for gameplay-only builds
    __all__: list[str] = []

