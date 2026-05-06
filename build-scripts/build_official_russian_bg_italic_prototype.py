from __future__ import annotations

import json
import shutil
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image, ImageDraw


UPM = 1000
PIXEL_SIZE = 50
ASCENT_PIXELS = 14
DESCENT_PIXELS = 3


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


def make_bitmap(pattern: list[str]) -> Image.Image:
    width = len(pattern[0])
    height = len(pattern)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    px = image.load()
    for y, row in enumerate(pattern):
        for x, cell in enumerate(row):
            if cell == "#":
                px[x, y] = (255, 255, 255, 255)
    return image


SYMBOL_PATTERNS: dict[str, list[str]] = {
    "★": [
        "..#..",
        ".###.",
        "#####",
        ".###.",
        "#####",
        "#.#.#",
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


ITALIC_EXCLUDED_CHAR_IDS = {
    32, 33, 34, 35, 39, 40, 41, 43, 44, 45, 46, 58, 59, 60, 61, 62, 63, 64,
    91, 92, 93, 95, 171, 173, 187, 8470, 9670, 9733, 9679, 9650, 9660,
    8592, 8593, 8594, 8595, 8216, 8217, 8218, 8220, 8221, 8222,
}
ITALIC_EXCLUDED_CHAR_IDS.update(range(48, 58))


def bitmap_italicize(image: Image.Image) -> Image.Image:
    source = image.convert("RGBA")
    width, height = source.size
    max_shift = max(1, (height - 1) // 4)
    result = Image.new("RGBA", (width + max_shift, height), (0, 0, 0, 0))
    src = source.load()
    dst = result.load()

    for y in range(height):
        shift = (height - 1 - y) // 4
        for x in range(width):
            if src[x, y][3] == 0:
                continue
            dst[x + shift, y] = (255, 255, 255, 255)
            # Bridge the row-to-row slant transition so stems don't look broken.
            if shift > 0 and x + shift - 1 >= 0 and x > 0 and src[x - 1, y][3] != 0:
                dst[x + shift - 1, y] = (255, 255, 255, 255)

    return result


def draw_pixel_glyph(image_path: Path, *, yoffset: int, base_pixels: int):
    image = Image.open(image_path).convert("RGBA")
    pen = TTGlyphPen(None)
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y][3] == 0:
                continue
            left = x * PIXEL_SIZE
            top = (base_pixels - yoffset - y) * PIXEL_SIZE
            right = (x + 1) * PIXEL_SIZE
            bottom = (base_pixels - yoffset - (y + 1)) * PIXEL_SIZE
            pen.moveTo((left, top))
            pen.lineTo((right, top))
            pen.lineTo((right, bottom))
            pen.lineTo((left, bottom))
            pen.closePath()
    return pen.glyph()


def add_glyph(data: dict, glyphs_dir: Path, new_id: int, base: dict, image: Image.Image, *, xadvance_extra: int = 1) -> None:
    file_name = f"u{new_id:04X}.png"
    image.save(glyphs_dir / file_name)
    glyph = dict(base)
    glyph["char_id"] = new_id
    glyph["char"] = chr(new_id)
    glyph["image"] = file_name
    glyph["width"] = image.width
    glyph["height"] = image.height
    glyph["xadvance"] = max(int(base.get("xadvance", image.width)), image.width + xadvance_extra)
    glyphs = {item["char_id"]: item for item in data["glyphs"]}
    glyphs[new_id] = glyph
    data["glyphs"] = [glyphs[key] for key in sorted(glyphs)]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    source_root = project_root / "ttf-work"
    output_root = project_root / "russian-bg-italic-work"
    glyphs_dir = output_root / "glyphs"
    output_root.mkdir(parents=True, exist_ok=True)
    if glyphs_dir.exists():
        shutil.rmtree(glyphs_dir)
    shutil.copytree(source_root / "glyphs", glyphs_dir)

    data = json.loads((source_root / "glyphs.json").read_text(encoding="utf-8"))
    glyph_map = {glyph["char_id"]: glyph for glyph in data["glyphs"]}

    for glyph in data["glyphs"]:
        image_path = glyphs_dir / glyph["image"]
        source_image = Image.open(image_path)
        if glyph["char_id"] in ITALIC_EXCLUDED_CHAR_IDS:
            italicized = source_image.convert("RGBA")
        else:
            italicized = bitmap_italicize(source_image)
        italicized.save(image_path)
        glyph["width"] = italicized.width
        glyph["height"] = italicized.height
        glyph["xadvance"] = max(int(glyph.get("xadvance", italicized.width)), italicized.width + 1)

    glyph_map = {glyph["char_id"]: glyph for glyph in data["glyphs"]}

    apostrophe = Image.open(glyphs_dir / glyph_map[39]["image"]).convert("RGBA")
    quote = Image.open(glyphs_dir / glyph_map[34]["image"]).convert("RGBA")
    comma = Image.open(glyphs_dir / glyph_map[44]["image"]).convert("RGBA")
    hyphen = Image.open(glyphs_dir / glyph_map[45]["image"]).convert("RGBA")
    space = Image.open(glyphs_dir / glyph_map[32]["image"]).convert("RGBA")

    add_glyph(data, glyphs_dir, 173, glyph_map[45], hyphen, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8216, glyph_map[39], apostrophe, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8217, glyph_map[39], apostrophe, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8218, glyph_map[44], comma, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8220, glyph_map[34], quote, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8221, glyph_map[34], quote, xadvance_extra=0)
    add_glyph(data, glyphs_dir, 8222, glyph_map[44], compose_double_comma(comma), xadvance_extra=0)
    add_glyph(data, glyphs_dir, 9670, glyph_map[45], make_diamond(7), xadvance_extra=0)

    for char, pattern in SYMBOL_PATTERNS.items():
        add_glyph(data, glyphs_dir, ord(char), glyph_map[45], make_bitmap(pattern), xadvance_extra=0)

    add_glyph(data, glyphs_dir, 32, glyph_map[32], space, xadvance_extra=0)

    metadata_path = output_root / "glyphs_augmented.json"
    metadata_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    base_pixels = int(data["common"]["base"])

    glyph_order = [".notdef"]
    cmap: dict[int, str] = {}
    glyf = {}
    hmtx = {}

    notdef_pen = TTGlyphPen(None)
    notdef_pen.moveTo((0, 0))
    notdef_pen.lineTo((UPM // 2, 0))
    notdef_pen.lineTo((UPM // 2, UPM // 2))
    notdef_pen.lineTo((0, UPM // 2))
    notdef_pen.closePath()
    glyf[".notdef"] = notdef_pen.glyph()
    hmtx[".notdef"] = (UPM // 2, 0)

    for glyph in data["glyphs"]:
        glyph_name = f"uni{glyph['char_id']:04X}"
        glyph_order.append(glyph_name)
        cmap[glyph["char_id"]] = glyph_name
        image_path = glyphs_dir / glyph["image"]
        glyf[glyph_name] = draw_pixel_glyph(
            image_path,
            yoffset=int(glyph.get("yoffset", 0)),
            base_pixels=base_pixels,
        )
        hmtx[glyph_name] = (max(1, glyph["xadvance"]) * PIXEL_SIZE, glyph.get("xoffset", 0) * PIXEL_SIZE)

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(hmtx)
    ascent = ASCENT_PIXELS * PIXEL_SIZE
    descent = DESCENT_PIXELS * PIXEL_SIZE
    fb.setupHorizontalHeader(ascent=ascent, descent=-descent, lineGap=0)
    fb.setupOS2(
        version=4,
        usWeightClass=400,
        usWidthClass=5,
        fsSelection=0x01,
        sTypoAscender=ascent,
        sTypoDescender=-descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=descent,
        sxHeight=6 * PIXEL_SIZE,
        sCapHeight=10 * PIXEL_SIZE,
    )
    family_name = "Russian Cyrillic BG Italic Prototype V2"
    fb.setupNameTable(
        {
            "familyName": family_name,
            "styleName": "Italic",
            "fullName": f"{family_name} Italic",
            "psName": "RussianCyrillicBGItalicPrototypeV2-Italic",
            "version": "Version 2.0",
            "uniqueFontIdentifier": f"{family_name} Italic 2.0",
            "manufacturer": "Stardew Cyrillic Fonts",
            "designer": "Community reconstruction and Bulgarian Cyrillic extension for Stardew Valley (Latin, Cyrillic, UI symbols)",
        }
    )
    fb.setupPost(keepGlyphNames=False, italicAngle=-12.0)
    fb.setupMaxp()
    fb.setupDummyDSIG()
    font = fb.font
    font["head"].macStyle = 0b10
    font["post"].formatType = 3.0

    ttf_path = output_root / "RussianCyrillicBGItalicPrototypeV2.ttf"
    fb.save(ttf_path)

    report = {
        "font_name": family_name,
        "glyph_count": len(data["glyphs"]),
        "metadata_path": str(metadata_path),
        "ttf_path": str(ttf_path),
    }
    (output_root / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
