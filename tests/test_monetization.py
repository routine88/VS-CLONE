import pytest

from game.monetization import (
    CosmeticInventory,
    CurrencyWallet,
    Storefront,
    default_cosmetics,
    default_dlc_packs,
)


def test_storefront_purchase_unlocks_items():
    packs = default_dlc_packs()
    storefront = Storefront(packs.values())
    wallet = CurrencyWallet(balance=10.0)
    inventory = CosmeticInventory()

    granted = storefront.purchase("dlc_founders", wallet, inventory)

    assert wallet.balance == pytest.approx(5.01, abs=1e-2)
    assert {item.id for item in granted} == {"skin_varik_ashen", "trail_bloodflare"}
    assert inventory.has("skin_varik_ashen")


def test_inventory_equipping_requires_ownership():
    cosmetics = default_cosmetics()
    inventory = CosmeticInventory()

    with pytest.raises(ValueError):
        inventory.equip(cosmetics["trail_bloodflare"])

    inventory.grant(cosmetics["trail_bloodflare"])
    inventory.equip(cosmetics["trail_bloodflare"])

    assert inventory.equipped_item("dash_trail") == "trail_bloodflare"
