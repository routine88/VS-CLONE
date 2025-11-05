"""Bootstrap helpers for the prototype runtime renderer."""

from .bootstrap import build_placeholder_scene, main, run_demo
from .importer import EngineFrameImporter
from .loop import FrameBundle, FramePlaybackLoop, PlaybackMetrics

__all__ = [
    "EngineFrameImporter",
    "FrameBundle",
    "FramePlaybackLoop",
    "PlaybackMetrics",
    "build_placeholder_scene",
    "main",
    "run_demo",
]
