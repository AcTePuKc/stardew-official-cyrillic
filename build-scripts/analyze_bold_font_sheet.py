from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


def alpha_mask(image: Image.Image) -> list[list[bool]]:
    pixels = image.load()
    return [[pixels[x, y][3] > 0 for x in range(image.width)] for y in range(image.height)]


def row_segments(mask: list[list[bool]]) -> list[tuple[int, int]]:
    rows = [sum(1 for value in row if value) for row in mask]
    segments: list[tuple[int, int]] = []
    start: int | None = None
    for idx, value in enumerate(rows):
        if value > 0 and start is None:
            start = idx
        elif value == 0 and start is not None:
            segments.append((start, idx - 1))
            start = None
    if start is not None:
        segments.append((start, len(rows) - 1))
    return segments


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "source-assets"
    work_dir = project_root / "bold-work"
    rows_dir = work_dir / "rows"
    rows_dir.mkdir(parents=True, exist_ok=True)

    bold_path = source_dir / "font_bold.png"
    colored_path = source_dir / "font_colored.png"

    bold = Image.open(bold_path).convert("RGBA")
    colored = Image.open(colored_path).convert("RGBA")
    bold_alpha = alpha_mask(bold)
    colored_alpha = alpha_mask(colored)

    bold_segments = row_segments(bold_alpha)
    colored_segments = row_segments(colored_alpha)

    for idx, (y0, y1) in enumerate(bold_segments):
        bold.crop((0, y0, bold.width, y1 + 1)).save(rows_dir / f"font_bold_row_{idx:02d}_{y0}_{y1}.png")
    for idx, (y0, y1) in enumerate(colored_segments):
        colored.crop((0, y0, colored.width, y1 + 1)).save(rows_dir / f"font_colored_row_{idx:02d}_{y0}_{y1}.png")

    report = {
        "font_bold": {
            "path": str(bold_path),
            "size": list(bold.size),
            "row_segments": bold_segments,
        },
        "font_colored": {
            "path": str(colored_path),
            "size": list(colored.size),
            "row_segments": colored_segments,
        },
        "alpha_equal": bold_alpha == colored_alpha,
        "alpha_diff_pixels": sum(
            1
            for y in range(min(len(bold_alpha), len(colored_alpha)))
            for x in range(min(len(bold_alpha[y]), len(colored_alpha[y])))
            if bold_alpha[y][x] != colored_alpha[y][x]
        ),
    }
    (work_dir / "bold_sheet_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote row slices to {rows_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
