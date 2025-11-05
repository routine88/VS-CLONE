"""Utility CLI for packaging native client artifacts and verifying exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for PyPy/alt builds
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True)
class ChecksumResult:
    """Digest metadata for a generated artifact."""

    path: Path
    algorithm: str
    digest: str


def _read_in_chunks(path: Path, *, chunk_size: int = 1024 * 1024) -> Iterable[bytes]:
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            yield block


def _normalise_algorithm(algorithm: str) -> str:
    algo = algorithm.lower()
    if algo not in hashlib.algorithms_available:
        raise ValueError(f"Unknown digest algorithm: {algorithm}")
    return algo


def checksum_files(paths: Sequence[Path], *, algorithm: str = "sha256") -> list[ChecksumResult]:
    """Return cryptographic digests for the provided files."""

    normalised = _normalise_algorithm(algorithm)
    results: list[ChecksumResult] = []
    for path in paths:
        digest = hashlib.new(normalised)
        for chunk in _read_in_chunks(path):
            digest.update(chunk)
        results.append(ChecksumResult(path=path, algorithm=normalised, digest=digest.hexdigest()))
    return results


def verify_digests(
    paths: Sequence[Path], *, algorithm: str = "sha256", expected: str | None = None
) -> ChecksumResult:
    """Ensure all files share the same digest (and optional expected value)."""

    if not paths:
        raise ValueError("At least one file is required for verification.")
    results = checksum_files(paths, algorithm=algorithm)
    baseline = results[0]
    mismatched = [res for res in results if res.digest != baseline.digest]
    if mismatched:
        formatted = ", ".join(f"{res.path} ({res.digest})" for res in mismatched)
        raise ValueError(f"Mismatched digests detected: {formatted}")
    if expected and baseline.digest != expected.lower():
        raise ValueError(
            "Digest mismatch against expected value: "
            f"{baseline.digest} != {expected.lower()}"
        )
    return baseline


def _project_version() -> str:
    """Best-effort lookup for the project version string."""

    try:
        from importlib import metadata

        return metadata.version("nightfall-survivors-prototype")
    except metadata.PackageNotFoundError:  # pragma: no cover - source tree execution
        root = Path(__file__).resolve().parents[2]
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project", {})
            return str(project.get("version", "0.0.0"))
        return "0.0.0"
    except Exception:  # pragma: no cover - unexpected metadata failure
        return "0.0.0"


def bundle_native_client(
    output: Path,
    *,
    build_id: str | None = None,
    platform: str = "generic",
    timestamp: datetime | None = None,
) -> Path:
    """Create a distributable archive for the native client harness."""

    package_root = Path(__file__).resolve().parents[1]
    output.parent.mkdir(parents=True, exist_ok=True)
    stamp = (timestamp or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")
    metadata = {
        "build_id": build_id or stamp,
        "platform": platform,
        "version": _project_version(),
        "generated_at": stamp,
        "source_revision": os.getenv("GITHUB_SHA"),
        "entry_module": "native.client",
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        native_root = package_root.parent
        for file_path in native_root.rglob("*.py"):
            arcname = file_path.relative_to(native_root)
            archive.write(file_path, arcname.as_posix())
        archive.writestr("BUILD_METADATA.json", json.dumps(metadata, indent=2, sort_keys=True))
    return output


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage Nightfall native runtime artifacts and QA verification outputs."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    checksum_parser = sub.add_parser("checksum", help="Write checksums for the supplied files.")
    checksum_parser.add_argument("paths", nargs="+", type=Path)
    checksum_parser.add_argument(
        "--algorithm", default="sha256", help="Hash algorithm to use (default: sha256)."
    )
    checksum_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional file path to write newline-delimited checksum entries.",
    )

    verify_parser = sub.add_parser(
        "verify", help="Validate reproducibility by comparing digests across files."
    )
    verify_parser.add_argument("paths", nargs="+", type=Path)
    verify_parser.add_argument(
        "--algorithm", default="sha256", help="Hash algorithm to use (default: sha256)."
    )
    verify_parser.add_argument(
        "--expected",
        help="Optional reference digest. Verification fails if the computed value differs.",
    )

    bundle_parser = sub.add_parser(
        "bundle", help="Package the native harness sources into a distributable archive."
    )
    bundle_parser.add_argument("--output", "-o", required=True, type=Path)
    bundle_parser.add_argument(
        "--build-id", help="Identifier embedded into the bundle metadata (defaults to timestamp)."
    )
    bundle_parser.add_argument(
        "--platform",
        default="generic",
        help="Informational platform label stored in the bundle metadata (default: generic).",
    )

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "checksum":
        results = checksum_files(args.paths, algorithm=args.algorithm)
        lines = [f"{res.digest}  {res.path}" for res in results]
        output: Path | None = getattr(args, "output", None)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            for line in lines:
                print(line)
        return 0
    if args.command == "verify":
        try:
            result = verify_digests(
                args.paths, algorithm=args.algorithm, expected=getattr(args, "expected", None)
            )
        except ValueError as exc:  # pragma: no cover - exercised through CLI integration
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Verified digest: {result.digest}  ({result.algorithm})")
        return 0
    if args.command == "bundle":
        bundle_native_client(
            args.output, build_id=getattr(args, "build_id", None), platform=args.platform
        )
        print(f"Bundle written to {args.output}")
        return 0
    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
