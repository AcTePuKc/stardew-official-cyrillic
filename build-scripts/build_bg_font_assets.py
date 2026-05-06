from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent


@dataclass
class BmGlyph:
    char_id: int
    x: int
    y: int
    width: int
    height: int
    xoffset: int
    yoffset: int
    xadvance: int
    page: int
    chnl: int


BM_RE = re.compile(
    r'<char id="(?P<id>-?\d+)" x="(?P<x>\d+)" y="(?P<y>\d+)" width="(?P<width>\d+)" '
    r'height="(?P<height>\d+)" xoffset="(?P<xoffset>-?\d+)" yoffset="(?P<yoffset>-?\d+)" '
    r'xadvance="(?P<xadvance>-?\d+)" page="(?P<page>\d+)" chnl="(?P<chnl>\d+)" />'
)


def find_free_spot(occupied: list[tuple[int, int, int, int]], atlas_size: tuple[int, int], width: int, height: int, padding: int = 1) -> tuple[int, int]:
    max_w, max_h = atlas_size
    for y in range(0, max_h - height + 1):
        for x in range(0, max_w - width + 1):
            left = x - padding
            top = y - padding
            right = x + width + padding
            bottom = y + height + padding
            collision = False
            for ox, oy, ow, oh in occupied:
                if left < ox + ow and right > ox and top < oy + oh and bottom > oy:
                    collision = True
                    break
            if not collision:
                return x, y
    raise RuntimeError(f"No free atlas space for {width}x{height}")


def expand_atlas(atlas: Image.Image, min_extra_height: int) -> Image.Image:
    extra_height = max(32, min_extra_height)
    expanded = Image.new("RGBA", (atlas.width, atlas.height + extra_height), (0, 0, 0, 0))
    expanded.alpha_composite(atlas, (0, 0))
    return expanded


def used_rects_from_bm(text: str) -> list[tuple[int, int, int, int]]:
    rects: list[tuple[int, int, int, int]] = []
    for match in BM_RE.finditer(text):
        width = int(match.group("width"))
        height = int(match.group("height"))
        if width <= 0 or height <= 0:
            continue
        rects.append((int(match.group("x")), int(match.group("y")), width, height))
    return rects


def read_bm_glyphs(text: str) -> dict[int, BmGlyph]:
    glyphs: dict[int, BmGlyph] = {}
    for match in BM_RE.finditer(text):
        glyph = BmGlyph(
            char_id=int(match.group("id")),
            x=int(match.group("x")),
            y=int(match.group("y")),
            width=int(match.group("width")),
            height=int(match.group("height")),
            xoffset=int(match.group("xoffset")),
            yoffset=int(match.group("yoffset")),
            xadvance=int(match.group("xadvance")),
            page=int(match.group("page")),
            chnl=int(match.group("chnl")),
        )
        glyphs[glyph.char_id] = glyph
    return glyphs


def glyph_bitmap(atlas: Image.Image, glyph_bounds: dict[str, int]) -> Image.Image:
    x = glyph_bounds["X"]
    y = glyph_bounds["Y"]
    w = glyph_bounds["Width"]
    h = glyph_bounds["Height"]
    return atlas.crop((x, y, x + w, y + h))


def compose_grave_glyph(base: Image.Image, grave: Image.Image, top_gap: int, accent_shift_x: int) -> Image.Image:
    width = max(base.width, grave.width + max(accent_shift_x, 0), base.width - min(accent_shift_x, 0))
    height = grave.height + top_gap + base.height
    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    accent_x = max(0, (base.width - grave.width) // 2 + accent_shift_x)
    base_x = max(0, (width - base.width) // 2)
    result.alpha_composite(grave, (accent_x, 0))
    result.alpha_composite(base, (base_x, grave.height + top_gap))
    return result


def compose_double_comma(comma: Image.Image, gap: int = 1) -> Image.Image:
    result = Image.new("RGBA", (comma.width * 2 + gap, comma.height), (0, 0, 0, 0))
    result.alpha_composite(comma, (0, 0))
    result.alpha_composite(comma, (comma.width + gap, 0))
    return result


def make_diamond(size: int = 9) -> Image.Image:
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(result)
    mid = size // 2
    points = [(mid, 0), (size - 1, mid), (mid, size - 1), (0, mid)]
    draw.polygon(points, fill=(255, 255, 255, 255))
    return result


def add_spritefont_glyphs(json_name: str, png_name: str, out_json_name: str, out_png_name: str) -> dict[str, list[str]]:
    data = json.loads((ROOT / json_name).read_text(encoding="utf-8"))
    atlas = Image.open(ROOT / png_name).convert("RGBA")
    glyphs: dict[str, dict] = data["Glyphs"]
    occupied = []
    for glyph in glyphs.values():
        bounds = glyph["BoundsInTexture"]
        if bounds["Width"] > 0 and bounds["Height"] > 0:
            occupied.append((bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"]))

    missing_before = [ch for ch in ["Ѝ", "ѝ", "„", "“", "◆"] if ch not in glyphs]

    upper_base = glyph_bitmap(atlas, glyphs["И"]["BoundsInTexture"])
    lower_base = glyph_bitmap(atlas, glyphs["и"]["BoundsInTexture"])
    grave = glyph_bitmap(atlas, glyphs["`"]["BoundsInTexture"])
    comma = glyph_bitmap(atlas, glyphs[","]["BoundsInTexture"])

    generated = {
        "Ѝ": (
            compose_grave_glyph(upper_base, grave, top_gap=0, accent_shift_x=-2),
            {
                "Character": "Ѝ",
                "Cropping": {"X": 0, "Y": 2, "Width": 16, "Height": 34},
                "LeftSideBearing": glyphs["Й"]["LeftSideBearing"],
                "RightSideBearing": glyphs["Й"]["RightSideBearing"],
                "Width": 16.0,
                "WidthIncludingBearings": glyphs["Й"]["WidthIncludingBearings"],
            },
        ),
        "ѝ": (
            compose_grave_glyph(lower_base, grave, top_gap=0, accent_shift_x=-2),
            {
                "Character": "ѝ",
                "Cropping": {"X": 0, "Y": 6, "Width": 12, "Height": 34},
                "LeftSideBearing": glyphs["й"]["LeftSideBearing"],
                "RightSideBearing": glyphs["й"]["RightSideBearing"],
                "Width": 12.0,
                "WidthIncludingBearings": glyphs["й"]["WidthIncludingBearings"],
            },
        ),
        "„": (
            compose_double_comma(comma),
            {
                "Character": "„",
                "Cropping": {"X": 0, "Y": 22, "Width": comma.width * 2 + 1, "Height": 34},
                "LeftSideBearing": glyphs[","]["LeftSideBearing"],
                "RightSideBearing": glyphs[","]["RightSideBearing"],
                "Width": float(comma.width * 2 + 1),
                "WidthIncludingBearings": float(comma.width * 2 + 1 + glyphs[","]["LeftSideBearing"] + glyphs[","]["RightSideBearing"]),
            },
        ),
        "◆": (
            make_diamond(9),
            {
                "Character": "◆",
                "Cropping": {"X": 0, "Y": 15, "Width": 9, "Height": 34},
                "LeftSideBearing": 2.0,
                "RightSideBearing": 2.0,
                "Width": 9.0,
                "WidthIncludingBearings": 13.0,
            },
        ),
    }

    # The left double quote can safely reuse the straight double quote glyph.
    if "“" not in glyphs:
        quote_glyph = json.loads(json.dumps(glyphs['"']))
        quote_glyph["Character"] = "“"
        glyphs["“"] = quote_glyph

    for char, (image, glyph_template) in generated.items():
        if char in glyphs:
            continue
        try:
            x, y = find_free_spot(occupied, atlas.size, image.width, image.height)
        except RuntimeError:
            atlas = expand_atlas(atlas, image.height + 8)
            x, y = find_free_spot(occupied, atlas.size, image.width, image.height)
        atlas.alpha_composite(image, (x, y))
        occupied.append((x, y, image.width, image.height))
        glyph = dict(glyph_template)
        glyph["BoundsInTexture"] = {"X": x, "Y": y, "Width": image.width, "Height": image.height}
        glyphs[char] = glyph

    ordered_chars = sorted(glyphs.keys(), key=ord)
    data["Characters"] = ordered_chars
    data["Glyphs"] = {ch: glyphs[ch] for ch in ordered_chars}

    (ROOT / out_json_name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    atlas.save(ROOT / out_png_name)

    missing_after = [ch for ch in ["Ѝ", "ѝ", "„", "“", "◆"] if ch not in glyphs]
    return {
        "before": missing_before,
        "after": missing_after,
    }


def add_bmfont_glyphs() -> dict[str, list[str]]:
    fnt_path = ROOT / "Russian.fnt"
    png_path = ROOT / "Russian_0.png"
    text = fnt_path.read_text(encoding="utf-8")
    atlas = Image.open(png_path).convert("RGBA")
    occupied = used_rects_from_bm(text)
    glyphs = read_bm_glyphs(text)

    missing_before = [char for char in ["\u00ad", "„", "“", "◆"] if ord(char) not in glyphs]

    comma = atlas.crop((glyphs[44].x, glyphs[44].y, glyphs[44].x + glyphs[44].width, glyphs[44].y + glyphs[44].height))
    double_quote = atlas.crop((glyphs[34].x, glyphs[34].y, glyphs[34].x + glyphs[34].width, glyphs[34].y + glyphs[34].height))

    generated_images: dict[int, tuple[Image.Image, BmGlyph]] = {
        173: (
            Image.new("RGBA", (1, 1), (0, 0, 0, 0)),
            BmGlyph(173, 0, 0, 1, 1, 0, 14, 0, 0, 15),
        ),
        8222: (
            compose_double_comma(comma, gap=0),
            BmGlyph(8222, 0, 0, comma.width * 2, comma.height, 1, 8, comma.width * 2 + 2, 0, 15),
        ),
        9670: (
            make_diamond(7),
            BmGlyph(9670, 0, 0, 7, 7, 1, 4, 9, 0, 15),
        ),
    }

    # Reuse the straight quote bitmap for the left double quote.
    if 8220 not in glyphs:
        x, y = glyphs[34].x, glyphs[34].y
        glyphs[8220] = BmGlyph(8220, x, y, glyphs[34].width, glyphs[34].height, glyphs[34].xoffset, glyphs[34].yoffset, glyphs[34].xadvance, 0, 15)

    for char_id, (image, glyph) in generated_images.items():
        if char_id in glyphs:
            continue
        x, y = find_free_spot(occupied, atlas.size, image.width, image.height)
        atlas.alpha_composite(image, (x, y))
        occupied.append((x, y, image.width, image.height))
        glyph.x = x
        glyph.y = y
        glyphs[char_id] = glyph

    sorted_glyphs = sorted(glyphs.values(), key=lambda item: item.char_id)
    char_lines = "\n".join(
        f'    <char id="{glyph.char_id}" x="{glyph.x}" y="{glyph.y}" width="{glyph.width}" height="{glyph.height}" '
        f'xoffset="{glyph.xoffset}" yoffset="{glyph.yoffset}" xadvance="{glyph.xadvance}" page="{glyph.page}" chnl="{glyph.chnl}" />'
        for glyph in sorted_glyphs
    )
    chars_block = f'  <chars count="{len(sorted_glyphs)}">\n{char_lines}\n  </chars>'
    updated, count = re.subn(r'  <chars count="\d+">.*?  </chars>', chars_block, text, flags=re.S)
    if count != 1:
        raise RuntimeError("Failed to rewrite <chars> block")
    updated = updated.replace('<page id="0" file="Russian_0" />', '<page id="0" file="Russian_0.bg.full" />')
    (ROOT / "Russian.bg.full.fnt").write_text(updated, encoding="utf-8")
    atlas.save(ROOT / "Russian_0.bg.full.png")

    missing_after = [char for char in ["\u00ad", "„", "“", "◆"] if ord(char) not in {glyph.char_id for glyph in sorted_glyphs}]
    return {
        "before": missing_before,
        "after": missing_after,
    }


def encode_chars(chars: Iterable[str]) -> list[str]:
    return [char.encode("unicode_escape").decode() for char in chars]


def main() -> None:
    sprite_report = add_spritefont_glyphs(
        json_name="SpriteFont1.ru-RU.json",
        png_name="SpriteFont1.ru-RU.png",
        out_json_name="SpriteFont1.ru-RU.bg-full.json",
        out_png_name="SpriteFont1.ru-RU.bg-full.png",
    )
    small_report = add_spritefont_glyphs(
        json_name="SmallFont.ru-RU.json",
        png_name="SmallFont.ru-RU.png",
        out_json_name="SmallFont.ru-RU.bg-full.json",
        out_png_name="SmallFont.ru-RU.bg-full.png",
    )
    bm_report = add_bmfont_glyphs()

    summary = {
        "SpriteFont1.ru-RU": {key: encode_chars(value) for key, value in sprite_report.items()},
        "SmallFont.ru-RU": {key: encode_chars(value) for key, value in small_report.items()},
        "Russian.fnt": {key: encode_chars(value) for key, value in bm_report.items()},
    }
    (ROOT / "build-report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
