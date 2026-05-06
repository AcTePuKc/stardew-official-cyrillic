from __future__ import annotations

import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


UPM = 1000
PIXEL_SIZE = 50
ASCENT_PIXELS = 14
DESCENT_PIXELS = 3


def draw_pixel_glyph(image_path: Path, *, yoffset: int, base_pixels: int):
    from PIL import Image

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


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / "russian-bg-italic-work"
    glyphs_dir = output_root / "glyphs"
    metadata_path = output_root / "glyphs_augmented.json"
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
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
    family_name = "Russian Cyrillic BG Italic Prototype V3"
    fb.setupNameTable(
        {
            "familyName": family_name,
            "styleName": "Italic",
            "fullName": f"{family_name} Italic",
            "psName": "RussianCyrillicBGItalicPrototypeV3-Italic",
            "version": "Version 3.0",
            "uniqueFontIdentifier": f"{family_name} Italic 3.0",
            "manufacturer": "Stardew Cyrillic Fonts",
            "designer": "Bitmap reconstruction and Bulgarian Cyrillic extension for Stardew Valley (Latin, Cyrillic, UI symbols)",
        }
    )
    fb.setupPost(keepGlyphNames=False, italicAngle=-12.0)
    fb.setupMaxp()
    fb.setupDummyDSIG()
    font = fb.font
    font["head"].macStyle = 0b10
    font["post"].formatType = 3.0

    ttf_path = output_root / "RussianCyrillicBGItalicPrototypeV3.ttf"
    fb.save(ttf_path)

    report = {
        "font_name": family_name,
        "glyph_count": len(data["glyphs"]),
        "metadata_path": str(metadata_path),
        "ttf_path": str(ttf_path),
        "mode": "rebuild_from_existing_glyphs",
    }
    (output_root / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
