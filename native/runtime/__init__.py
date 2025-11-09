"""Bootstrap helpers for the prototype runtime renderer."""

from .assets import AudioRegistry, SpriteRegistry
from .bootstrap import build_placeholder_scene, load_bundle, main, run_demo
from .importer import EngineFrameImporter
from .loop import FrameBundle, FramePlaybackLoop, PlaybackMetrics
from .project import RendererProject
from .stream import FrameBundleDTO, decode_bundle, iter_jsonl_lines, load_jsonl_file

__all__ = [
    "AudioRegistry",
    "EngineFrameImporter",
    "FrameBundle",
    "FrameBundleDTO",
    "FramePlaybackLoop",
    "PlaybackMetrics",
    "RendererProject",
    "SpriteRegistry",
    "build_placeholder_scene",
    "decode_bundle",
    "iter_jsonl_lines",
    "load_bundle",
    "load_jsonl_file",
    "main",
    "run_demo",
]
