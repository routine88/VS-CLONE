"""Dependency tracking utilities for shader hot-reload flows."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Iterable, MutableMapping, Set


class ShaderDependencyTracker:
    """Tracks shader include relationships to determine rebuild sets."""

    def __init__(self) -> None:
        self._graph: Dict[Path, Set[Path]] = {}
        self._reverse: Dict[Path, Set[Path]] = {}
        self._timestamps: MutableMapping[Path, float] = {}

    def register(self, shader: Path | str, dependencies: Iterable[Path | str] | None = None) -> None:
        """Record that *shader* depends on *dependencies*."""

        shader_path = Path(shader).resolve()
        deps: Set[Path] = set()
        if dependencies is not None:
            for entry in dependencies:
                deps.add(Path(entry).resolve())
        previous = self._graph.get(shader_path)
        if previous:
            for dep in previous:
                dependents = self._reverse.get(dep)
                if dependents is not None:
                    dependents.discard(shader_path)
                    if not dependents:
                        self._reverse.pop(dep, None)
        self._graph[shader_path] = deps
        for dep in deps:
            self._reverse.setdefault(dep, set()).add(shader_path)
        if shader_path not in self._timestamps:
            self._timestamps[shader_path] = self._probe_timestamp(shader_path)

    def record_build(self, shader: Path | str, timestamp: float | None = None) -> None:
        """Update the known build timestamp for *shader*."""

        shader_path = Path(shader).resolve()
        self._timestamps[shader_path] = timestamp or time.time()

    def needs_rebuild(self, shader: Path | str) -> bool:
        """Return ``True`` if *shader* has stale dependencies."""

        shader_path = Path(shader).resolve()
        shader_time = self._timestamps.get(shader_path, 0.0)
        for dep in self._graph.get(shader_path, set()):
            dep_time = self._timestamps.get(dep)
            if dep_time is None:
                dep_time = self._probe_timestamp(dep)
                self._timestamps[dep] = dep_time
            if dep_time >= shader_time:
                return True
        return False

    def affected(self, changed: Iterable[Path | str]) -> Set[Path]:
        """Return the shaders impacted by *changed* dependency files."""

        initial = {Path(path).resolve() for path in changed}
        queue = list(initial)
        affected: Set[Path] = set()
        visited: Set[Path] = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if current in initial:
                current_time = self._probe_timestamp(current)
                self._timestamps[current] = max(current_time, time.time(), self._timestamps.get(current, 0.0))
            for shader in self._reverse.get(current, set()):
                if shader not in affected:
                    affected.add(shader)
                    queue.append(shader)
        return affected

    def invalidate(self, shader: Path | str) -> None:
        """Remove *shader* and its edges from the graph."""

        shader_path = Path(shader).resolve()
        deps = self._graph.pop(shader_path, set())
        for dep in deps:
            dependents = self._reverse.get(dep)
            if dependents is None:
                continue
            dependents.discard(shader_path)
            if not dependents:
                self._reverse.pop(dep, None)
        self._timestamps.pop(shader_path, None)

    @staticmethod
    def _probe_timestamp(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except FileNotFoundError:
            return 0.0


__all__ = ["ShaderDependencyTracker"]
