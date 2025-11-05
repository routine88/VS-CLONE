"""Utilities for decoding JSONL frame bundles exported by the prototype."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Optional, Tuple

from native.client.audio import AudioFrameDTO
from native.client.dto import RenderFrameDTO

FrameBundleDTO = Tuple[RenderFrameDTO, Optional[AudioFrameDTO]]


def decode_bundle(payload: Mapping[str, object]) -> FrameBundleDTO:
    render_payload = payload.get("render")
    if render_payload is None:
        raise KeyError("render bundle missing 'render' payload")
    render_frame = RenderFrameDTO.from_dict(render_payload)  # type: ignore[arg-type]

    audio_payload = payload.get("audio")
    audio_frame: AudioFrameDTO | None
    if audio_payload is None:
        audio_frame = None
    else:
        audio_frame = AudioFrameDTO.from_dict(audio_payload)  # type: ignore[arg-type]

    return render_frame, audio_frame


def iter_jsonl_lines(lines: Iterable[str]) -> Iterator[FrameBundleDTO]:
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        payload = json.loads(text)
        yield decode_bundle(payload)


def load_jsonl_file(path: Path) -> Tuple[FrameBundleDTO, ...]:
    with path.open("r", encoding="utf-8") as fh:
        return tuple(iter_jsonl_lines(fh))


__all__ = ["FrameBundleDTO", "decode_bundle", "iter_jsonl_lines", "load_jsonl_file"]

