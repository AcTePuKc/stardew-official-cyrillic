from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from PIL import Image


MIN_COMPONENT_PIXELS = 4


def alpha_mask(image: Image.Image) -> list[list[bool]]:
    pixels = image.load()
    return [[pixels[x, y][3] > 0 for x in range(image.width)] for y in range(image.height)]


def row_segments(mask: list[list[bool]]) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    start: int | None = None
    for idx, row in enumerate(mask):
        active = any(row)
        if active and start is None:
            start = idx
        elif not active and start is not None:
            segments.append((start, idx - 1))
            start = None
    if start is not None:
        segments.append((start, len(mask) - 1))
    return segments


def find_components(mask: list[list[bool]]) -> list[dict[str, int]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    visited = [[False for _ in range(width)] for _ in range(height)]
    components: list[dict[str, int]] = []

    for y in range(height):
        for x in range(width):
            if not mask[y][x] or visited[y][x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y][x] = True
            min_x = max_x = x
            min_y = max_y = y
            pixels = 0
            while queue:
                cx, cy = queue.popleft()
                pixels += 1
                if cx < min_x:
                    min_x = cx
                if cx > max_x:
                    max_x = cx
                if cy < min_y:
                    min_y = cy
                if cy > max_y:
                    max_y = cy
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx] = True
                        queue.append((nx, ny))
            if pixels >= MIN_COMPONENT_PIXELS:
                components.append(
                    {
                        "x": min_x,
                        "y": min_y,
                        "width": max_x - min_x + 1,
                        "height": max_y - min_y + 1,
                        "pixels": pixels,
                    }
                )

    components.sort(key=lambda item: (item["y"], item["x"]))
    return components


def crop_components(
    image: Image.Image,
    base_name: str,
    y0: int,
    y1: int,
    output_dir: Path,
) -> list[dict[str, int | str]]:
    row_image = image.crop((0, y0, image.width, y1 + 1)).convert("RGBA")
    mask = alpha_mask(row_image)
    components = find_components(mask)
    results: list[dict[str, int | str]] = []
    for idx, component in enumerate(components):
        x = int(component["x"])
        y = int(component["y"])
        width = int(component["width"])
        height = int(component["height"])
        crop = row_image.crop((x, y, x + width, y + height))
        filename = f"{base_name}_component_{idx:03d}_x{x}_y{y}_w{width}_h{height}.png"
        crop.save(output_dir / filename)
        results.append(
            {
                "file": filename,
                "x": x,
                "y": y0 + y,
                "width": width,
                "height": height,
                "pixels": int(component["pixels"]),
            }
        )
    return results


def process_sheet(name: str, image: Image.Image, output_root: Path) -> dict[str, object]:
    mask = alpha_mask(image)
    segments = row_segments(mask)
    sheet_dir = output_root / name
    sheet_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for row_index, (y0, y1) in enumerate(segments):
        row_name = f"row_{row_index:02d}_{y0}_{y1}"
        row_dir = sheet_dir / row_name
        row_dir.mkdir(parents=True, exist_ok=True)
        components = crop_components(image, row_name, y0, y1, row_dir)
        rows.append(
            {
                "row_index": row_index,
                "y0": y0,
                "y1": y1,
                "height": y1 - y0 + 1,
                "component_count": len(components),
                "components": components,
            }
        )
    return {
        "sheet": name,
        "size": [image.width, image.height],
        "row_count": len(rows),
        "rows": rows,
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "source-assets"
    output_root = project_root / "bold-work" / "components"
    output_root.mkdir(parents=True, exist_ok=True)

    report = {
        "font_bold": process_sheet("font_bold", Image.open(source_dir / "font_bold.png"), output_root),
        "font_colored": process_sheet("font_colored", Image.open(source_dir / "font_colored.png"), output_root),
        "notes": {
            "connectivity": "4-neighbor",
            "min_component_pixels": MIN_COMPONENT_PIXELS,
        },
    }
    report_path = project_root / "bold-work" / "component_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote component crops to {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
