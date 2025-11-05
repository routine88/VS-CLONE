import json
import zipfile

import pytest

from native.client.cli import (
    ChecksumResult,
    bundle_native_client,
    checksum_files,
    verify_digests,
)


def test_checksum_files_and_verify(tmp_path):
    payload = tmp_path / "payload.jsonl"
    payload.write_text("line-1\nline-2\n", encoding="utf-8")

    results = checksum_files([payload])
    assert len(results) == 1
    assert isinstance(results[0], ChecksumResult)
    assert results[0].path == payload

    verified = verify_digests([payload, payload], expected=results[0].digest)
    assert verified.digest == results[0].digest

    other = tmp_path / "other.bin"
    other.write_text("different", encoding="utf-8")
    with pytest.raises(ValueError):
        verify_digests([payload, other])


def test_bundle_native_client(tmp_path, monkeypatch):
    output = tmp_path / "native-runtime.zip"
    monkeypatch.setenv("GITHUB_SHA", "deadbeef")

    bundle_native_client(output, build_id="build-42", platform="linux")
    assert output.exists()

    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        assert "native/client/harness.py" in names
        metadata = json.loads(archive.read("BUILD_METADATA.json").decode("utf-8"))

    assert metadata["build_id"] == "build-42"
    assert metadata["platform"] == "linux"
    assert metadata["entry_module"] == "native.client"
    assert metadata["source_revision"] == "deadbeef"
