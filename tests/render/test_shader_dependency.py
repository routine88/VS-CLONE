from __future__ import annotations

from pathlib import Path

from tools.shaderc import ShaderDependencyTracker


def test_shader_dependency_tracker_propagates_changes(tmp_path: Path) -> None:
    tracker = ShaderDependencyTracker()
    vertex = tmp_path / "sprite.vert"
    include = tmp_path / "common.glsl"
    fragment = tmp_path / "sprite.frag"

    vertex.write_text("// vertex\n")
    include.write_text("// include\n")
    fragment.write_text("// fragment\n")

    tracker.register(vertex, [include])
    tracker.register(fragment, [include, vertex])
    tracker.record_build(vertex)
    tracker.record_build(fragment)

    include.write_text("// include v2\n")

    impacted = tracker.affected([include])
    assert vertex.resolve() in impacted
    assert fragment.resolve() in impacted
    assert tracker.needs_rebuild(fragment)
