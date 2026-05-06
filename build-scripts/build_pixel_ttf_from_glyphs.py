from __future__ import annotations

import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


UPM = 1000
PIXEL_SIZE = 50
DESCENT_PIXELS = 3
ASCENT_PIXELS = 14


def draw_pixel_glyph(image_path: Path):
    from PIL import Image

    image = Image.open(image_path).convert("RGBA")
    pen = TTGlyphPen(None)
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y][3] == 0:
                continue
            left = x * PIXEL_SIZE
            top = -y * PIXEL_SIZE
            right = (x + 1) * PIXEL_SIZE
            bottom = -(y + 1) * PIXEL_SIZE
            pen.moveTo((left, top))
            pen.lineTo((right, top))
            pen.lineTo((right, bottom))
            pen.lineTo((left, bottom))
            pen.closePath()
    return pen.glyph()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    work_dir = project_root / "ttf-work"
    glyphs_dir = work_dir / "glyphs"
    metadata_path = work_dir / "glyphs_augmented.json"
    if not metadata_path.exists():
        metadata_path = work_dir / "glyphs.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    output_path = work_dir / "output" / "StardewCyrillicPrototype-Win.ttf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    for glyph in metadata["glyphs"]:
        glyph_name = f"uni{glyph['char_id']:04X}"
        glyph_order.append(glyph_name)
        cmap[glyph["char_id"]] = glyph_name
        image_path = glyphs_dir / glyph["image"]

        if glyph["width"] <= 0 or glyph["height"] <= 0:
            pen = TTGlyphPen(None)
            glyf[glyph_name] = pen.glyph()
        else:
            glyf[glyph_name] = draw_pixel_glyph(image_path)

        advance_width = max(1, glyph["xadvance"]) * PIXEL_SIZE
        left_bearing = glyph["xoffset"] * PIXEL_SIZE
        hmtx[glyph_name] = (advance_width, left_bearing)

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
        fsSelection=0x40,
        sTypoAscender=ascent,
        sTypoDescender=-descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=descent,
        sxHeight=6 * PIXEL_SIZE,
        sCapHeight=10 * PIXEL_SIZE,
    )
    fb.setupNameTable(
        {
            "familyName": "Stardew Cyrillic Prototype",
            "styleName": "Regular",
            "fullName": "Stardew Cyrillic Prototype Regular",
            "psName": "StardewCyrillicPrototype-Regular",
            "version": "Version 0.1",
            "uniqueFontIdentifier": "Stardew Cyrillic Prototype Regular 0.1",
            "manufacturer": "Stardew Cyrillic Fonts",
            "designer": "Community bitmap reconstruction from Stardew Valley Russian font assets",
        }
    )
    fb.setupPost(keepGlyphNames=False)
    fb.setupMaxp()
    fb.setupDummyDSIG()

    font = fb.font
    font["head"].macStyle = 0
    font["OS/2"].version = 4
    font["OS/2"].fsSelection = 0x40
    font["OS/2"].usWeightClass = 400
    font["OS/2"].usWidthClass = 5
    font["post"].formatType = 3.0
    if hasattr(font["post"], "extraNames"):
        font["post"].extraNames = []
    if hasattr(font["post"], "mapping"):
        font["post"].mapping = {}

    fb.save(output_path)
    print(f"Wrote {output_path}")
    print(f"Glyphs: {len(glyph_order) - 1}")
    print(f"Metadata source: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
