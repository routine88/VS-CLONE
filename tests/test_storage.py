import json
from pathlib import Path

import pytest

from game.entities import GlyphFamily
from game.meta import SigilLedger
from game.profile import PlayerProfile
from game.storage import decrypt_data, encrypt_data, load_profile, save_profile


def test_encrypt_round_trip():
    payload = json.dumps({"hello": "world", "value": 42})
    key = "hunter-key"

    encrypted = encrypt_data(payload, key)
    assert encrypted != payload

    decrypted = decrypt_data(encrypted, key)
    assert decrypted == payload

    with pytest.raises(ValueError):
        decrypt_data(encrypted, "wrong-key")


def test_save_and_load_profile(tmp_path: Path):
    ledger = SigilLedger(balance=75, unlocked_ids={"hunter_lunara", "glyph_verdant"})
    profile = PlayerProfile(
        meta=None,
        owned_hunters={"hunter_varik", "hunter_lunara"},
        weapon_cards={"Dusk Repeater", "Gloom Chakram", "Storm Siphon", "Nocturne Harp"},
        glyph_families={
            GlyphFamily.BLOOD,
            GlyphFamily.STORM,
            GlyphFamily.CLOCKWORK,
            GlyphFamily.VERDANT,
        },
    )
    profile.meta.ledger = ledger
    profile.set_active_hunter("hunter_lunara")

    save_path = tmp_path / "profile.sav"
    save_profile(profile, save_path, key="moonlight")

    # Ensure ciphertext hides clear data
    contents = save_path.read_text(encoding="utf-8")
    assert "hunter_lunara" not in contents

    loaded = load_profile(save_path, key="moonlight")
    assert loaded.active_hunter == "hunter_lunara"
    assert set(loaded.owned_hunters) == {"hunter_lunara", "hunter_varik"}
    assert "Nocturne Harp" in loaded.available_weapon_cards
    assert GlyphFamily.VERDANT in loaded.available_glyph_families
    assert loaded.ledger.balance == 75
    assert "glyph_verdant" in loaded.ledger.unlocked_ids

    with pytest.raises(ValueError):
        load_profile(save_path, key="incorrect")
