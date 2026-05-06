from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


PATTERNS: dict[str, list[str]] = {
    " ": [
        "..",
        "..",
        "..",
        "..",
        "..",
        "..",
        "..",
    ],
    ".": [
        "..",
        "..",
        "..",
        "..",
        "..",
        "##",
        "##",
    ],
    ",": [
        "..",
        "..",
        "..",
        "..",
        ".#",
        "##",
        "#.",
    ],
    ":": [
        "..",
        "##",
        "##",
        "..",
        "##",
        "##",
        "..",
    ],
    ";": [
        "..",
        "##",
        "##",
        "..",
        ".#",
        "##",
        "#.",
    ],
    "(": [
        "..#",
        ".#.",
        "#..",
        "#..",
        "#..",
        ".#.",
        "..#",
    ],
    ")": [
        "#..",
        ".#.",
        "..#",
        "..#",
        "..#",
        ".#.",
        "#..",
    ],
    "[": [
        "###",
        "#..",
        "#..",
        "#..",
        "#..",
        "#..",
        "###",
    ],
    "]": [
        "###",
        "..#",
        "..#",
        "..#",
        "..#",
        "..#",
        "###",
    ],
    "{": [
        "..##",
        ".#..",
        ".#..",
        "##..",
        ".#..",
        ".#..",
        "..##",
    ],
    "}": [
        "##..",
        "..#.",
        "..#.",
        "..##",
        "..#.",
        "..#.",
        "##..",
    ],
    "<": [
        "...#",
        "..#.",
        ".#..",
        "#...",
        ".#..",
        "..#.",
        "...#",
    ],
    ">": [
        "#...",
        ".#..",
        "..#.",
        "...#",
        "..#.",
        ".#..",
        "#...",
    ],
    "«": [
        ".#.#",
        "#.#.",
        ".#.#",
        "#.#.",
        ".#.#",
        "#.#.",
        ".#.#",
    ],
    "»": [
        "#.#.",
        ".#.#",
        "#.#.",
        ".#.#",
        "#.#.",
        ".#.#",
        "#.#.",
    ],
    "„": [
        "....",
        "....",
        "....",
        "....",
        ".#.#",
        "####",
        "#.#.",
    ],
    "“": [
        ".#.#",
        "####",
        "#.#.",
        "....",
        "....",
        "....",
        "....",
    ],
    "-": [
        "....",
        "....",
        "....",
        "####",
        "....",
        "....",
        "....",
    ],
    "—": [
        "......",
        "......",
        "......",
        "######",
        "......",
        "......",
        "......",
    ],
    "_": [
        "....",
        "....",
        "....",
        "....",
        "....",
        "....",
        "####",
    ],
    "=": [
        "....",
        "####",
        "....",
        "####",
        "....",
        "....",
        "....",
    ],
    "+": [
        "..#..",
        "..#..",
        "..#..",
        "#####",
        "..#..",
        "..#..",
        "..#..",
    ],
    "@": [
        ".###.",
        "#...#",
        "#.###",
        "#.#.#",
        "#.###",
        "#....",
        ".###.",
    ],
    "#": [
        ".#.#.",
        ".#.#.",
        "#####",
        ".#.#.",
        "#####",
        ".#.#.",
        ".#.#.",
    ],
    "№": [
        "##..##",
        "###.##",
        "##.###",
        "..##..",
        ".#..#.",
        "#.##.#",
        ".####.",
    ],
    "★": [
        "..#..",
        ".###.",
        "#####",
        ".###.",
        "#####",
        "#.#.#",
        "..#..",
    ],
    "◆": [
        "..#..",
        ".###.",
        "#####",
        "#####",
        "#####",
        ".###.",
        "..#..",
    ],
    "●": [
        ".###.",
        "#####",
        "#####",
        "#####",
        "#####",
        "#####",
        ".###.",
    ],
    "▲": [
        "..#..",
        ".###.",
        ".###.",
        "#####",
        "#####",
        "#####",
        "#####",
    ],
    "▼": [
        "#####",
        "#####",
        "#####",
        "#####",
        ".###.",
        ".###.",
        "..#..",
    ],
    "→": [
        ".......",
        "...#...",
        "....#..",
        "#######",
        "....#..",
        "...#...",
        ".......",
    ],
    "←": [
        ".......",
        "...#...",
        "..#....",
        "#######",
        "..#....",
        "...#...",
        ".......",
    ],
    "↑": [
        "...#...",
        "..###..",
        ".#####.",
        "...#...",
        "...#...",
        "...#...",
        "...#...",
    ],
    "↓": [
        "...#...",
        "...#...",
        "...#...",
        "...#...",
        ".#####.",
        "..###..",
        "...#...",
    ],
}


def make_image(pattern: list[str], scale: int = 1) -> Image.Image:
    width = len(pattern[0])
    height = len(pattern)
    image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    pixels = image.load()
    for y, row in enumerate(pattern):
        for x, cell in enumerate(row):
            if cell != "#":
                continue
            for sy in range(scale):
                for sx in range(scale):
                    pixels[x * scale + sx, y * scale + sy] = (255, 255, 255, 255)
    return image


def augment_family(project_root: Path, family: str) -> dict[str, object]:
    glyph_dir = project_root / "ttf-work" / family / "glyphs"
    metadata_path = project_root / "ttf-work" / family / "glyphs_from_rows.json"
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    glyphs = data["glyphs"]
    existing = {int(g["char_id"]) for g in glyphs}
    added: list[str] = []
    for char, pattern in PATTERNS.items():
        char_id = ord(char)
        if char_id in existing:
            continue
        image = make_image(pattern)
        filename = f"u{char_id:04X}.png"
        image.save(glyph_dir / filename)
        glyphs.append(
            {
                "char": char,
                "char_id": char_id,
                "image": filename,
                "width": image.width,
                "height": image.height,
                "xadvance": max(2, image.width + 1),
                "xoffset": 0,
                "source_row": "synthetic",
                "segment": 0,
            }
        )
        added.append(char)
    glyphs.sort(key=lambda item: int(item["char_id"]))
    metadata_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"family": family, "added": added, "metadata_path": str(metadata_path)}


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    report = {
        "augmented": [
            augment_family(project_root, "font_colored"),
            augment_family(project_root, "font_bold"),
        ]
    }
    report_path = project_root / "ttf-work" / "sheet-prototypes" / "augment-symbols-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
