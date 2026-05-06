from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


TARGETS = [
    "u0414.png",  # Д
    "u0434.png",  # д
]


def remove_small_island_components(
    path: Path,
    max_pixels: int = 12,
    max_right: int = 4,
    max_bottom: int = 4,
    max_top: int = 4,
) -> bool:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    changed = False

    for y in range(height):
        for x in range(width):
            if visited[y][x] or pixels[x, y][3] == 0:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y][x] = True
            component: list[tuple[int, int]] = []
            min_x = max_x = x
            min_y = max_y = y
            while queue:
                cx, cy = queue.popleft()
                component.append((cx, cy))
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx] and pixels[nx, ny][3] > 0:
                        visited[ny][nx] = True
                        queue.append((nx, ny))

            if (
                len(component) <= max_pixels
                and max_x <= max_right
                and max_y <= max_bottom
                and min_y <= max_top
            ):
                for cx, cy in component:
                    pixels[cx, cy] = (0, 0, 0, 0)
                changed = True

    if changed:
        image.save(path)
    return changed


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    changed_paths: list[str] = []
    for family in ("font_colored", "font_bold"):
        glyph_dir = project_root / "ttf-work" / family / "glyphs"
        for target in TARGETS:
            path = glyph_dir / target
            if path.exists() and remove_small_island_components(path):
                changed_paths.append(str(path))
    print("changed:")
    for path in changed_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
