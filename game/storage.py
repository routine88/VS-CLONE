"""Persistence helpers for Nightfall Survivors profile data."""

from __future__ import annotations

import base64
import binascii
import json
import os
from hashlib import sha256
from itertools import cycle
from pathlib import Path
from typing import Dict, Iterable, Optional

from .entities import GlyphFamily
from .meta import MetaProgressionSystem, SigilLedger
from .profile import PlayerProfile


_SAVE_VERSION = 1


def _derive_key(key: str) -> bytes:
    if not key:
        raise ValueError("encryption key must be non-empty")
    return sha256(key.encode("utf-8")).digest()


def _xor_bytes(payload: bytes, key: bytes) -> bytes:
    return bytes(b ^ k for b, k in zip(payload, cycle(key)))


def encrypt_data(plaintext: str, key: str) -> str:
    """Encrypt the provided plaintext string using a hashed XOR stream."""

    key_bytes = _derive_key(key)
    cipher = _xor_bytes(plaintext.encode("utf-8"), key_bytes)
    return base64.urlsafe_b64encode(cipher).decode("utf-8")


def decrypt_data(ciphertext: str, key: str) -> str:
    """Decrypt an encrypted payload produced by :func:`encrypt_data`."""

    key_bytes = _derive_key(key)
    try:
        cipher = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
    except (ValueError, binascii.Error) as exc:
        raise ValueError("invalid encrypted payload") from exc

    try:
        plaintext = _xor_bytes(cipher, key_bytes).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid decryption key or payload") from exc
    return plaintext


def _glyphs_to_names(glyphs: Iterable[GlyphFamily]) -> Iterable[str]:
    return [glyph.name for glyph in glyphs]


def _glyphs_from_names(names: Iterable[str]) -> Iterable[GlyphFamily]:
    return [GlyphFamily[name] for name in names]


def _profile_payload(profile: PlayerProfile) -> Dict[str, object]:
    ledger = profile.ledger
    return {
        "version": _SAVE_VERSION,
        "active_hunter": profile.active_hunter,
        "owned_hunters": sorted(profile.owned_hunters),
        "weapon_cards": sorted(profile.available_weapon_cards),
        "glyph_families": list(_glyphs_to_names(sorted(profile.available_glyph_families, key=lambda g: g.name))),
        "ledger": {
            "balance": ledger.balance,
            "unlocked_ids": sorted(ledger.unlocked_ids),
        },
    }


def save_profile(profile: PlayerProfile, path: os.PathLike[str] | str, *, key: str) -> Path:
    """Serialize and encrypt the supplied profile to disk."""

    payload = _profile_payload(profile)
    serialized = json.dumps(payload, sort_keys=True)
    encrypted = encrypt_data(serialized, key)

    save_path = Path(path)
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(encrypted, encoding="utf-8")
    return save_path


def load_profile(
    path: os.PathLike[str] | str,
    *,
    key: str,
    hunters: Optional[Dict[str, "HunterDefinition"]] = None,
) -> PlayerProfile:
    """Load an encrypted profile save from disk."""

    from .profile import HunterDefinition  # Local import to avoid cycles.

    save_path = Path(path)
    encrypted = save_path.read_text(encoding="utf-8")
    serialized = decrypt_data(encrypted, key)

    try:
        data = json.loads(serialized)
    except json.JSONDecodeError as exc:
        raise ValueError("decrypted payload is not valid JSON") from exc

    if data.get("version") != _SAVE_VERSION:
        raise ValueError("unsupported save version")

    ledger_data = data.get("ledger", {})
    ledger = SigilLedger(
        balance=int(ledger_data.get("balance", 0)),
        unlocked_ids=set(ledger_data.get("unlocked_ids", [])),
    )

    meta = MetaProgressionSystem(ledger=ledger)
    profile = PlayerProfile(
        hunters=hunters,
        meta=meta,
        owned_hunters=data.get("owned_hunters"),
        weapon_cards=data.get("weapon_cards"),
        glyph_families=_glyphs_from_names(data.get("glyph_families", [])),
    )

    active_hunter = data.get("active_hunter")
    if active_hunter:
        profile.set_active_hunter(active_hunter)

    return profile


__all__ = [
    "decrypt_data",
    "encrypt_data",
    "load_profile",
    "save_profile",
]
