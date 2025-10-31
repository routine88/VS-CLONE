from __future__ import annotations

"""CLI helper for exporting the graphics manifest."""

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from game.graphics import GraphicsEngine, SpriteBrief


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export the GraphicsEngine manifest as JSON.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional file path to write the manifest JSON to instead of stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation to use when pretty-printing JSON (default: 2).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without whitespace (overrides --indent).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format for the manifest (default: json).",
    )
    return parser


def dump_manifest(*, indent: int = 2, compact: bool = False) -> str:
    """Return the current GraphicsEngine manifest as a JSON string."""

    engine = GraphicsEngine()
    manifest = engine.build_manifest().to_dict()
    if compact:
        return json.dumps(manifest, separators=(",", ":"), sort_keys=True)
    return json.dumps(manifest, indent=indent, sort_keys=True)


def render_markdown(briefs: Iterable[SpriteBrief]) -> str:
    """Render sprite briefs into a markdown document."""

    lines = [
        "# Graphics Asset Brief",
        "",
        "Comprehensive requirements for 2D art assets referenced by the simulation graphics engine.",
        "Each section lists the context needed for concept and production teams as well as AI image generation pipelines.",
        "",
    ]

    for brief in briefs:
        lines.append(f"## {brief.name} (`{brief.id}`)")
        lines.append("")
        lines.append(f"- **Texture path**: `{brief.texture}`")
        lines.append(
            f"- **Display size**: {brief.size[0]} × {brief.size[1]} px (pivot {brief.pivot[0]:.2f}, {brief.pivot[1]:.2f})"
        )
        if brief.purpose:
            lines.append(f"- **Purpose**: {brief.purpose}")
        if brief.description:
            lines.append(f"- **Description**: {brief.description}")
        if brief.palette:
            palette = ", ".join(brief.palette)
            lines.append(f"- **Color palette**: {palette}")
        if brief.mood:
            lines.append(f"- **Mood/Story**: {brief.mood}")
        if brief.lighting:
            lines.append(f"- **Lighting direction**: {brief.lighting}")
        if brief.art_style:
            lines.append(f"- **Art style**: {brief.art_style}")
        if brief.tags:
            lines.append(f"- **Tags**: {', '.join(brief.tags)}")
        if brief.notes:
            lines.append("- **Production notes**:")
            for note in brief.notes:
                lines.append(f"  - {note}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: Any | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.format == "markdown":
        engine = GraphicsEngine()
        payload = render_markdown(engine.build_sprite_briefs())
    else:
        payload = dump_manifest(indent=args.indent, compact=args.compact)

    if args.output:
        args.output.write_text(payload if args.format == "markdown" else payload + ("" if args.compact else "\n"))
    else:
        print(payload, end="" if args.format == "markdown" else "\n")


if __name__ == "__main__":
    main()
