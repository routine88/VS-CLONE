import pytest

from game.combat import CombatSummary
from game.entities import GlyphFamily, UpgradeType
from game.meta import default_unlocks
from game.profile import PlayerProfile
from game.session import RunResult


def test_start_run_uses_active_hunter_stats():
    profile = PlayerProfile()
    profile.set_active_hunter("hunter_mira")

    state = profile.start_run()

    assert state.player.max_health == 105
    assert state.player.unlocked_weapons["Storm Siphon"] == 1
    assert state.player.unlocked_weapons["Dusk Repeater"] == 1


def test_unlock_flow_enables_new_cards():
    profile = PlayerProfile()
    cards = {card.name for card in profile.available_upgrade_cards()}
    assert "Verdant Sigil" not in cards

    unlock = next(item for item in default_unlocks() if item.id == "glyph_verdant")
    profile.apply_unlock(unlock)

    cards = {card.name for card in profile.available_upgrade_cards()}
    assert "Verdant Sigil" in cards
    assert GlyphFamily.VERDANT in profile.available_glyph_families


def test_claim_unlock_validates_requirements():
    profile = PlayerProfile()
    profile.meta.ledger.deposit(100)

    insufficient_run = RunResult(
        survived=True,
        duration=600.0,
        encounters_resolved=4,
        relics_collected=["Moonlit Charm"],
        events=[],
    )

    with pytest.raises(ValueError):
        profile.claim_unlock("glyph_verdant", run_result=insufficient_run)

    qualifying_run = RunResult(
        survived=True,
        duration=1200.0,
        encounters_resolved=8,
        relics_collected=["Moonlit Charm", "Storm Prism"],
        events=[],
    )

    profile.claim_unlock("glyph_verdant", run_result=qualifying_run)
    assert GlyphFamily.VERDANT in profile.available_glyph_families

    profile.meta.ledger.deposit(100)
    final_boss_unlock = next(item for item in default_unlocks() if item.id == "weapon_nocturne")

    final_run = RunResult(
        survived=True,
        duration=1180.0,
        encounters_resolved=10,
        relics_collected=["Moonlit Charm", "Storm Prism"],
        events=[],
        final_summary=CombatSummary(
            kind="final_boss",
            enemies_defeated=1,
            damage_taken=20,
            healing_received=10,
            souls_gained=0,
            duration=45.0,
            notes=[],
        ),
    )

    profile.claim_unlock(final_boss_unlock.id, run_result=final_run)
    cards = {card.name for card in profile.available_upgrade_cards()}
    assert final_boss_unlock.name in cards


def test_profile_exposes_full_weapon_roster_by_default():
    profile = PlayerProfile()
    cards = profile.available_upgrade_cards()
    weapon_names = {card.name for card in cards if card.type is UpgradeType.WEAPON}

    expected = {
        "Dusk Repeater",
        "Gloom Chakram",
        "Storm Siphon",
        "Bloodthorn Lance",
        "Gravebloom Staff",
        "Tempest Gauntlet",
        "Frostbrand Edge",
        "Inferno Lantern",
        "Umbral Coil",
    }

    assert expected.issubset(weapon_names)
