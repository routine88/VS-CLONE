"""Bootstrap helpers for the prototype runtime renderer."""

from .bootstrap import build_placeholder_scene, main, run_demo
from .importer import EngineFrameImporter
from .loop import FrameBundle, FramePlaybackLoop

__all__ = [
    "EngineFrameImporter",
    "FrameBundle",
    "FramePlaybackLoop",
    "build_placeholder_scene",
    "main",
    "run_demo",
]
