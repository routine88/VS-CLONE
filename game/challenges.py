"""Challenge builder utilities for Nightfall Survivors.

The PRD calls for a community challenge-code builder so players can share
curated rule sets. This module provides a small data model plus encode/decode
helpers that translate challenge parameters into short, shareable strings.

Codes are prefixed with a version flag (``NSC1``), followed by a base32 payload
and a checksum segment to guard against transcription mistakes. The payload is
compressed JSON so new fields can be added without breaking existing clients as
long as they default sensibly during decoding.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
import zlib
from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Iterable, Sequence


_CODE_PREFIX = "NSC1"


def _normalise(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(sorted({v.strip() for v in values if v.strip()}))


@dataclass(frozen=True)
class ChallengeConfig:
    """Serializable challenge definition used for shareable codes."""

    seed: int
    duration: int | None = None
    difficulty: str | None = None
    modifiers: tuple[str, ...] = field(default_factory=tuple)
    banned_weapons: tuple[str, ...] = field(default_factory=tuple)
    required_glyphs: tuple[str, ...] = field(default_factory=tuple)
    starting_relics: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        """Return a JSON-serialisable payload."""

        payload: dict[str, object] = {"seed": int(self.seed)}
        if self.duration is not None:
            payload["duration"] = int(self.duration)
        if self.difficulty:
            payload["difficulty"] = self.difficulty
        if self.modifiers:
            payload["modifiers"] = list(self.modifiers)
        if self.banned_weapons:
            payload["banned_weapons"] = list(self.banned_weapons)
        if self.required_glyphs:
            payload["required_glyphs"] = list(self.required_glyphs)
        if self.starting_relics:
            payload["starting_relics"] = list(self.starting_relics)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "ChallengeConfig":
        """Create an instance from JSON payload data."""

        seed = int(payload["seed"])
        duration = payload.get("duration")
        difficulty = payload.get("difficulty")

        def _tuple(name: str) -> tuple[str, ...]:
            values = payload.get(name)
            if not values:
                return ()
            if not isinstance(values, Sequence):
                raise TypeError(f"Expected sequence for {name!r}, got {type(values)}")
            return tuple(str(v) for v in values)

        return cls(
            seed=seed,
            duration=int(duration) if duration is not None else None,
            difficulty=str(difficulty) if difficulty else None,
            modifiers=_tuple("modifiers"),
            banned_weapons=_tuple("banned_weapons"),
            required_glyphs=_tuple("required_glyphs"),
            starting_relics=_tuple("starting_relics"),
        )


def encode_challenge(config: ChallengeConfig) -> str:
    """Encode a :class:`ChallengeConfig` into a shareable challenge code."""

    payload = config.to_payload()
    json_blob = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    compressed = zlib.compress(json_blob)
    encoded = base64.b32encode(compressed).decode().rstrip("=")
    checksum = blake2b(json_blob, digest_size=3).hexdigest()
    return f"{_CODE_PREFIX}-{encoded}-{checksum}"


def decode_challenge(code: str) -> ChallengeConfig:
    """Decode a challenge code back into a :class:`ChallengeConfig`."""

    try:
        prefix, payload, checksum = code.split("-")
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Challenge code must contain three segments") from exc

    if prefix != _CODE_PREFIX:
        raise ValueError(f"Unsupported challenge prefix: {prefix!r}")

    padding = "=" * (-len(payload) % 8)
    try:
        compressed = base64.b32decode(payload + padding)
    except (ValueError, binascii.Error) as exc:  # pragma: no cover - defensive
        raise ValueError("Challenge payload is not valid base32") from exc

    json_blob = zlib.decompress(compressed)
    expected_checksum = blake2b(json_blob, digest_size=3).hexdigest()
    if checksum != expected_checksum:
        raise ValueError("Challenge checksum mismatch")

    payload_dict = json.loads(json_blob)
    if not isinstance(payload_dict, dict):  # pragma: no cover - defensive
        raise ValueError("Challenge payload must decode to an object")
    return ChallengeConfig.from_payload(payload_dict)


def build_config(
    *,
    seed: int,
    duration: int | None = None,
    difficulty: str | None = None,
    modifiers: Iterable[str] | None = None,
    banned_weapons: Iterable[str] | None = None,
    required_glyphs: Iterable[str] | None = None,
    starting_relics: Iterable[str] | None = None,
) -> ChallengeConfig:
    """Convenience builder that normalises iterables before instantiating."""

    return ChallengeConfig(
        seed=int(seed),
        duration=int(duration) if duration is not None else None,
        difficulty=difficulty.strip() if difficulty else None,
        modifiers=_normalise(modifiers),
        banned_weapons=_normalise(banned_weapons),
        required_glyphs=_normalise(required_glyphs),
        starting_relics=_normalise(starting_relics),
    )


def _format_listing(values: Sequence[str], label: str) -> str:
    if not values:
        return f"{label}: —"
    return f"{label}: " + ", ".join(values)


def describe_challenge(config: ChallengeConfig) -> str:
    """Return a multi-line human description for CLI output."""

    lines = [
        f"Seed: {config.seed}",
        f"Duration: {config.duration or 'default'}",
        f"Difficulty: {config.difficulty or 'standard'}",
        _format_listing(config.modifiers, "Modifiers"),
        _format_listing(config.banned_weapons, "Banned weapons"),
        _format_listing(config.required_glyphs, "Required glyphs"),
        _format_listing(config.starting_relics, "Starting relics"),
    ]
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nightfall Survivors challenge builder")
    parser.add_argument("--seed", type=int, help="Base RNG seed for the challenge")
    parser.add_argument("--duration", type=int, help="Override run duration in seconds")
    parser.add_argument("--difficulty", help="Optional difficulty label (e.g. torment)")
    parser.add_argument(
        "--modifier",
        action="append",
        default=None,
        help="Challenge modifier to apply (can be provided multiple times)",
    )
    parser.add_argument(
        "--ban",
        dest="banned_weapons",
        action="append",
        default=None,
        help="Weapon identifier to ban from the run (repeat for multiple)",
    )
    parser.add_argument(
        "--require",
        dest="required_glyphs",
        action="append",
        default=None,
        help="Glyph identifier that must be taken during the run",
    )
    parser.add_argument(
        "--start",
        dest="starting_relics",
        action="append",
        default=None,
        help="Relic identifier to grant at the beginning of the run",
    )
    parser.add_argument(
        "--decode",
        help="Decode an existing challenge code instead of creating a new one",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.decode:
        config = decode_challenge(args.decode)
    else:
        if args.seed is None:
            parser.error("--seed is required when building a new challenge")
        config = build_config(
            seed=args.seed,
            duration=args.duration,
            difficulty=args.difficulty,
            modifiers=args.modifier,
            banned_weapons=args.banned_weapons,
            required_glyphs=args.required_glyphs,
            starting_relics=args.starting_relics,
        )

    code = encode_challenge(config)
    description = describe_challenge(config)
    print("Nightfall Survivors Challenge")
    print(f"Code: {code}")
    print(description)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual entrypoint
    sys.exit(main())

