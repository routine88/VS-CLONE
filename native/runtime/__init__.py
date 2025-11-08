"""Bootstrap helpers for the prototype runtime renderer."""

from .bootstrap import build_placeholder_scene, main, run_demo
from .importer import EngineFrameImporter
from .loop import FrameBundle, FramePlaybackLoop, PlaybackMetrics

__all__ = [
    "AudioRegistry",
    "FrameBundle",
    "FrameBundleDTO",
    "FramePlaybackLoop",
    "PlaybackMetrics",
    "build_placeholder_scene",
    "decode_bundle",
    "iter_jsonl_lines",
    "load_bundle",
    "load_jsonl_file",
    "main",
    "run_demo",
]
