from __future__ import annotations

import argparse
import json
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen


UPM = 1000
PIXEL_SIZE = 50
ASCENT_PIXELS = 14
DESCENT_PIXELS = 3
MANUFACTURER = "Stardew Official Cyrillic Project"
DESIGNER = "Bitmap reconstruction and Bulgarian Cyrillic extension for Stardew Valley (Latin, Cyrillic, UI symbols)"

MEMBERS = {
    "regular": {
        "work_dir": "russian-bg-work",
        "family_name": "Official Russian Cyrillic BG Prototype V2",
        "style_name": "Regular",
        "ps_name": "OfficialRussianCyrillicBGPrototypeV2-Regular",
        "version": "Version 2.0",
        "ttf_name": "OfficialRussianCyrillicBGPrototypeV2.ttf",
        "weight": 400,
        "italic": False,
        "bold": False,
    },
    "bold": {
        "work_dir": "russian-bg-bold-work",
        "family_name": "Official Russian Cyrillic BG Bold Prototype V1",
        "style_name": "Regular",
        "ps_name": "OfficialRussianCyrillicBGBoldPrototypeV1-Regular",
        "version": "Version 1.0",
        "ttf_name": "OfficialRussianCyrillicBGBoldPrototypeV1.ttf",
        "weight": 700,
        "italic": False,
        "bold": True,
    },
    "italic": {
        "work_dir": "russian-bg-italic-work",
        "family_name": "Official Russian Cyrillic BG Italic Prototype V3",
        "style_name": "Italic",
        "ps_name": "OfficialRussianCyrillicBGItalicPrototypeV3-Italic",
        "version": "Version 3.0",
        "ttf_name": "OfficialRussianCyrillicBGItalicPrototypeV3.ttf",
        "weight": 400,
        "italic": True,
        "bold": False,
    },
}


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


def build_member(member: str) -> dict[str, str | int]:
    config = MEMBERS[member]
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / config["work_dir"]
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

    italic = bool(config["italic"])
    bold = bool(config["bold"])
    selection = 0
    if italic:
        selection |= 0x01
    if bold:
        selection |= 0x20
    if not italic and not bold:
        selection |= 0x40

    fb.setupOS2(
        version=4,
        usWeightClass=int(config["weight"]),
        usWidthClass=5,
        fsSelection=selection,
        sTypoAscender=ascent,
        sTypoDescender=-descent,
        sTypoLineGap=0,
        usWinAscent=ascent,
        usWinDescent=descent,
        sxHeight=6 * PIXEL_SIZE,
        sCapHeight=10 * PIXEL_SIZE,
    )
    family_name = str(config["family_name"])
    style_name = str(config["style_name"])
    fb.setupNameTable(
        {
            "familyName": family_name,
            "styleName": style_name,
            "fullName": f"{family_name} {style_name}",
            "psName": str(config["ps_name"]),
            "version": str(config["version"]),
            "uniqueFontIdentifier": f"{family_name} {style_name} {config['version']}",
            "manufacturer": MANUFACTURER,
            "designer": DESIGNER,
        }
    )
    fb.setupPost(keepGlyphNames=False, italicAngle=-12.0 if italic else 0.0)
    fb.setupMaxp()
    fb.setupDummyDSIG()
    font = fb.font
    mac_style = 0
    if bold:
        mac_style |= 0x01
    if italic:
        mac_style |= 0x02
    font["head"].macStyle = mac_style
    font["post"].formatType = 3.0

    ttf_path = output_root / str(config["ttf_name"])
    fb.save(ttf_path)

    report = {
        "member": member,
        "font_name": family_name,
        "glyph_count": len(data["glyphs"]),
        "metadata_path": str(metadata_path),
        "ttf_path": str(ttf_path),
    }
    (output_root / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild a font family member from edited glyph PNGs.")
    parser.add_argument("--member", choices=sorted(MEMBERS.keys()), required=True)
    args = parser.parse_args()
    report = build_member(args.member)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
