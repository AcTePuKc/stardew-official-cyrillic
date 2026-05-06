from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw


def compose_double_comma(comma: Image.Image, gap: int = 0) -> Image.Image:
    result = Image.new("RGBA", (comma.width * 2 + gap, comma.height), (0, 0, 0, 0))
    result.alpha_composite(comma, (0, 0))
    result.alpha_composite(comma, (comma.width + gap, 0))
    return result


def make_diamond(size: int = 7) -> Image.Image:
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(result)
    mid = size // 2
    draw.polygon([(mid, 0), (size - 1, mid), (mid, size - 1), (0, mid)], fill=(255, 255, 255, 255))
    return result


def glyph_map(data: dict) -> dict[int, dict]:
    return {glyph["char_id"]: glyph for glyph in data["glyphs"]}


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    work_dir = project_root / "ttf-work"
    glyphs_dir = work_dir / "glyphs"
    augmented_path = work_dir / "glyphs_augmented.json"

    data = json.loads((work_dir / "glyphs.json").read_text(encoding="utf-8"))
    glyphs = glyph_map(data)

    apostrophe = Image.open(glyphs_dir / glyphs[39]["image"]).convert("RGBA")
    quote = Image.open(glyphs_dir / glyphs[34]["image"]).convert("RGBA")
    comma = Image.open(glyphs_dir / glyphs[44]["image"]).convert("RGBA")
    hyphen = Image.open(glyphs_dir / glyphs[45]["image"]).convert("RGBA")

    additions: list[dict] = []

    def add_simple(new_id: int, base_id: int, image: Image.Image | None = None, *, xoffset: int | None = None, yoffset: int | None = None, xadvance: int | None = None) -> None:
        base = dict(glyphs[base_id])
        file_name = f"u{new_id:04X}.png"
        if image is None:
            image = Image.open(glyphs_dir / base["image"]).convert("RGBA")
        image.save(glyphs_dir / file_name)
        base["char_id"] = new_id
        base["char"] = chr(new_id)
        base["image"] = file_name
        base["width"] = image.width
        base["height"] = image.height
        if xoffset is not None:
            base["xoffset"] = xoffset
        if yoffset is not None:
            base["yoffset"] = yoffset
        if xadvance is not None:
            base["xadvance"] = xadvance
        additions.append(base)

    add_simple(173, 45, hyphen)
    add_simple(8216, 39, apostrophe)
    add_simple(8217, 39, apostrophe)
    add_simple(8218, 44, comma)
    add_simple(8220, 34, quote)
    add_simple(8221, 34, quote)
    low_double = compose_double_comma(comma, gap=0)
    add_simple(8222, 44, low_double, xadvance=max(glyphs[44]["xadvance"], low_double.width + 1))
    diamond = make_diamond(7)
    add_simple(9670, 45, diamond, xadvance=9)

    existing_ids = {glyph["char_id"] for glyph in data["glyphs"]}
    for item in additions:
        if item["char_id"] not in existing_ids:
            data["glyphs"].append(item)
            existing_ids.add(item["char_id"])

    data["glyphs"] = sorted(data["glyphs"], key=lambda item: item["char_id"])
    augmented_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote augmented metadata: {augmented_path}")
    print(f"Glyph count: {len(data['glyphs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
