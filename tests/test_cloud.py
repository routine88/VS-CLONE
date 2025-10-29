import json

from game.cloud import CloudSync, run_cli
from game.profile import PlayerProfile
from game.storage import save_profile


def test_cloud_round_trip(tmp_path):
    cloud_root = tmp_path / "cloud"
    sync = CloudSync(cloud_root)

    profile = PlayerProfile()
    profile.meta.ledger.deposit(25)
    meta = sync.upload_profile(profile, key="secret", slot="primary")

    assert meta.slot == "primary"
    assert meta.size > 0

    slots = sync.list_slots()
    assert [slot.slot for slot in slots] == ["primary"]

    downloaded = sync.download_profile(key="secret", slot="primary")
    assert downloaded.active_hunter == profile.active_hunter
    assert downloaded.meta.ledger.balance == 25


def test_cloud_cli_upload_and_list(tmp_path, monkeypatch):
    cloud_root = tmp_path / "cloud"
    local_save = tmp_path / "profile.sav"
    save_profile(PlayerProfile(), local_save, key="key")

    outputs = []

    def capture_print(message: str) -> None:
        outputs.append(message)

    monkeypatch.setattr("builtins.print", capture_print)

    exit_code = run_cli(
        [
            "--root",
            str(cloud_root),
            "upload",
            "--profile-path",
            str(local_save),
            "--key",
            "key",
            "--slot",
            "alpha",
        ]
    )
    assert exit_code == 0

    outputs.clear()
    exit_code = run_cli(["--root", str(cloud_root), "list"])
    assert exit_code == 0
    assert outputs and "alpha" in outputs[0]

    manifest = cloud_root / "manifest.json"
    data = json.loads(manifest.read_text())
    assert data["slots"][0]["slot"] == "alpha"
