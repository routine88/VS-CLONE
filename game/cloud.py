"""Steam-style cloud sync helpers for Nightfall Survivors."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .profile import PlayerProfile
from .storage import load_profile, save_profile


@dataclass(frozen=True)
class CloudSlot:
    """Metadata describing a stored cloud slot."""

    slot: str
    checksum: str
    size: int


class CloudSync:
    """Simple filesystem-backed Steam Cloud façade."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # internal helpers
    def _slot_path(self, slot: str) -> Path:
        safe = slot.strip() or "default"
        return self.root / f"{safe}.sav"

    def _manifest_path(self) -> Path:
        return self.root / "manifest.json"

    def _load_manifest(self) -> Dict[str, CloudSlot]:
        path = self._manifest_path()
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        slots: Dict[str, CloudSlot] = {}
        for entry in data.get("slots", []):
            slots[entry["slot"]] = CloudSlot(
                slot=entry["slot"],
                checksum=entry["checksum"],
                size=int(entry["size"]),
            )
        return slots

    def _write_manifest(self, slots: Iterable[CloudSlot]) -> None:
        payload = {
            "slots": [
                {"slot": slot.slot, "checksum": slot.checksum, "size": slot.size}
                for slot in slots
            ]
        }
        self._manifest_path().write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    # ------------------------------------------------------------------
    # public API
    def upload_profile(self, profile: PlayerProfile, *, key: str, slot: str = "default") -> CloudSlot:
        """Encrypt and upload a profile into the specified cloud slot."""

        path = self._slot_path(slot)
        save_profile(profile, path, key=key)
        encrypted = path.read_text(encoding="utf-8").encode("utf-8")
        slot_meta = CloudSlot(slot=slot, checksum=sha256(encrypted).hexdigest(), size=len(encrypted))

        slots = self._load_manifest()
        slots[slot] = slot_meta
        self._write_manifest(slots.values())
        return slot_meta

    def download_profile(
        self,
        *,
        key: str,
        slot: str = "default",
        hunters: Optional[Dict[str, "HunterDefinition"]] = None,
    ) -> PlayerProfile:
        """Download and decrypt a profile from the requested slot."""

        from .profile import HunterDefinition

        path = self._slot_path(slot)
        if not path.exists():
            raise FileNotFoundError(f"cloud slot '{slot}' has no uploaded profile")

        manifest = self._load_manifest()
        meta = manifest.get(slot)
        if meta is not None:
            encrypted = path.read_text(encoding="utf-8").encode("utf-8")
            checksum = sha256(encrypted).hexdigest()
            if checksum != meta.checksum:
                raise ValueError("cloud data failed checksum validation")

        return load_profile(path, key=key, hunters=hunters)

    def list_slots(self) -> List[CloudSlot]:
        """Return manifest metadata for all known cloud slots."""

        return sorted(self._load_manifest().values(), key=lambda slot: slot.slot)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nightfall Survivors cloud sync helper")
    parser.add_argument("--root", default=".cloud", help="Directory used to simulate the Steam Cloud")

    subparsers = parser.add_subparsers(dest="command", required=True)

    upload = subparsers.add_parser("upload", help="Upload a profile save to the cloud")
    upload.add_argument("--profile-path", required=True, help="Path to the encrypted profile save on disk")
    upload.add_argument("--key", required=True, help="Encryption key for the save")
    upload.add_argument("--slot", default="default", help="Named cloud slot to write")

    download = subparsers.add_parser("download", help="Download a profile save from the cloud")
    download.add_argument("--output", required=True, help="Destination path for the downloaded save")
    download.add_argument("--key", required=True, help="Encryption key for the save")
    download.add_argument("--slot", default="default", help="Named cloud slot to read")

    subparsers.add_parser("list", help="List cloud slots and metadata")
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    sync = CloudSync(Path(args.root))

    if args.command == "upload":
        profile = load_profile(args.profile_path, key=args.key)
        meta = sync.upload_profile(profile, key=args.key, slot=args.slot)
        print(f"Uploaded slot {meta.slot} (size={meta.size} checksum={meta.checksum})")
        return 0
    if args.command == "download":
        profile = sync.download_profile(key=args.key, slot=args.slot)
        save_profile(profile, args.output, key=args.key)
        print(f"Downloaded slot {args.slot} -> {args.output}")
        return 0

    # list command
    slots = sync.list_slots()
    if not slots:
        print("No cloud slots available")
    else:
        for slot in slots:
            print(f"{slot.slot}: size={slot.size} checksum={slot.checksum}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> None:  # pragma: no cover - thin wrapper
    sys.exit(run_cli(argv))


__all__ = ["CloudSlot", "CloudSync", "main", "run_cli"]
