from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image


UPM = 1000
PIXEL_SIZE = 50
ASCENT_PIXELS = 14
DESCENT_PIXELS = 3
MIN_GLYPH_WIDTH = 2
BMCHAR_PATTERN = re.compile(r'<char id="(?P<id>-?\d+)".*?xadvance="(?P<xadvance>-?\d+)".*?/>')
ROW_TRIMS: dict[tuple[str, int], tuple[int, int]] = {
    ("font_colored", 2): (8, 0),
    ("font_colored", 3): (0, 8),
    ("font_colored", 4): (0, 0),
    ("font_colored", 5): (0, 16),
    ("font_bold", 2): (8, 0),
    ("font_bold", 3): (0, 8),
    ("font_bold", 4): (0, 0),
    ("font_bold", 5): (0, 16),
}


@dataclass
class SegmentedGlyph:
    char: str
    image: Image.Image
    xadvance: int
    xoffset: int = 0


def alpha_columns(image: Image.Image) -> list[int]:
    alpha = image.getchannel("A")
    cols: list[int] = []
    for x in range(image.width):
        cols.append(sum(1 for y in range(image.height) if alpha.getpixel((x, y)) > 0))
    return cols


def split_equalish(
    row_image: Image.Image,
    count: int,
    weights: list[float] | None = None,
) -> list[tuple[int, int]]:
    cols = alpha_columns(row_image)
    width = row_image.width
    if count <= 0:
        return []
    if not weights or len(weights) != count or sum(weights) <= 0:
        weights = [1.0] * count

    # Prefer true zero columns as separators when available.
    zero_positions = {i for i, value in enumerate(cols) if value == 0}
    cuts: list[int] = []
    total_weight = float(sum(weights))
    cumulative_weights: list[float] = []
    running = 0.0
    for weight in weights:
        running += float(weight)
        cumulative_weights.append(running)
    for boundary in range(1, count):
        target = round((cumulative_weights[boundary - 1] / total_weight) * width)
        best = target
        best_score = (10**9, 10**9)
        search_start = max(1, target - max(6, width // (count * 2)))
        search_end = min(width - 1, target + max(6, width // (count * 2)))
        for x in range(search_start, search_end + 1):
            score = (cols[x], abs(x - target))
            if x in zero_positions:
                score = (-1, abs(x - target))
            if score < best_score:
                best_score = score
                best = x
        if cuts and best <= cuts[-1]:
            best = min(width - 1, cuts[-1] + MIN_GLYPH_WIDTH)
        cuts.append(best)

    bounds: list[tuple[int, int]] = []
    start = 0
    for cut in cuts:
        bounds.append((start, cut))
        start = cut
    bounds.append((start, width))

    # Trim transparent side columns inside each segment.
    trimmed: list[tuple[int, int]] = []
    for start, end in bounds:
        seg_start = start
        seg_end = end
        while seg_start < seg_end and cols[seg_start] == 0:
            seg_start += 1
        while seg_end > seg_start and cols[seg_end - 1] == 0:
            seg_end -= 1
        if seg_end - seg_start < MIN_GLYPH_WIDTH:
            seg_end = min(width, seg_start + MIN_GLYPH_WIDTH)
        trimmed.append((seg_start, seg_end))
    return trimmed


def crop_to_alpha(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, image.height), (0, 0, 0, 0))
    left, top, right, bottom = bbox
    # Preserve the original row height so letters keep a shared baseline instead of
    # being vertically re-anchored by their tight alpha box.
    return image.crop((left, 0, right, image.height))


def load_russian_advance_map(project_root: Path) -> dict[int, int]:
    fnt_path = project_root / "source-assets" / "Russian.fnt"
    text = fnt_path.read_text(encoding="utf-8")
    result: dict[int, int] = {}
    for match in BMCHAR_PATTERN.finditer(text):
        char_id = int(match.group("id"))
        if char_id < 0:
            continue
        result[char_id] = int(match.group("xadvance"))
    return result


def extract_family_glyphs(project_root: Path, family_key: str, rows_prefix: str) -> tuple[list[dict[str, object]], list[SegmentedGlyph]]:
    mapping_path = project_root / "bold-work" / "row_mapping_template.json"
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    family_rows = data[family_key]
    rows_dir = project_root / "bold-work" / "rows"
    out_dir = project_root / "ttf-work" / family_key / "glyphs"
    out_dir.mkdir(parents=True, exist_ok=True)

    advance_map = load_russian_advance_map(project_root)
    metadata: list[dict[str, object]] = []
    glyphs: list[SegmentedGlyph] = []

    for row in family_rows:
        chars = row["confirmed_characters"]
        if not chars:
            continue
        row_index = row["row_index"]
        y0 = row["y0"]
        y1 = row["y1"]
        row_path = rows_dir / f"{rows_prefix}_row_{row_index:02d}_{y0}_{y1}.png"
        if not row_path.exists():
            continue
        row_image = Image.open(row_path).convert("RGBA")
        trim_left, trim_right = ROW_TRIMS.get((family_key, row_index), (0, 0))
        if trim_left or trim_right:
            effective_right = row_image.width - trim_right if trim_right else row_image.width
            row_image = row_image.crop((trim_left, 0, effective_right, row_image.height))
        weights = [float(max(1, advance_map.get(ord(char), 7))) for char in chars]
        bounds = split_equalish(row_image, len(chars), weights=weights)
        for idx, char in enumerate(chars):
            if idx >= len(bounds):
                break
            start, end = bounds[idx]
            glyph_image = crop_to_alpha(row_image.crop((start, 0, end, row_image.height)))
            filename = f"u{ord(char):04X}.png"
            glyph_image.save(out_dir / filename)
            ref_advance = int(max(1, advance_map.get(ord(char), glyph_image.width + 1)))
            xadvance = max(glyph_image.width + 1, ref_advance)
            entry = {
                "char": char,
                "char_id": ord(char),
                "image": filename,
                "width": glyph_image.width,
                "height": glyph_image.height,
                "xadvance": xadvance,
                "xoffset": 0,
                "source_row": row_index,
                "segment": idx,
            }
            metadata.append(entry)
            glyphs.append(SegmentedGlyph(char=char, image=glyph_image, xadvance=xadvance))
    return metadata, glyphs


def draw_pixel_glyph(image: Image.Image):
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


def build_ttf(output_path: Path, family_name: str, glyphs_meta: list[dict[str, object]], glyph_dir: Path) -> None:
    deduped: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    for glyph in glyphs_meta:
        char_id = int(glyph["char_id"])
        if char_id in seen_ids:
            continue
        seen_ids.add(char_id)
        deduped.append(glyph)

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

    for glyph in deduped:
        glyph_name = f"uni{glyph['char_id']:04X}"
        glyph_order.append(glyph_name)
        cmap[glyph["char_id"]] = glyph_name
        image = Image.open(glyph_dir / glyph["image"]).convert("RGBA")
        glyf[glyph_name] = draw_pixel_glyph(image)
        hmtx[glyph_name] = (max(1, glyph["xadvance"]) * PIXEL_SIZE, 0)

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
            "familyName": family_name,
            "styleName": "Regular",
            "fullName": f"{family_name} Regular",
            "psName": family_name.replace(" ", "") + "-Regular",
            "version": "Version 0.9",
            "uniqueFontIdentifier": f"{family_name} Regular 0.9",
            "manufacturer": "OpenAI Prototype Build",
            "designer": "Bitmap reconstruction from Stardew Valley font sheets",
        }
    )
    fb.setupPost(keepGlyphNames=False)
    fb.setupMaxp()
    fb.setupDummyDSIG()
    font = fb.font
    font["head"].macStyle = 0
    font["post"].formatType = 3.0
    fb.save(output_path)


def merge_synthetic_glyphs(base_glyphs: list[dict[str, object]], metadata_path: Path) -> list[dict[str, object]]:
    if not metadata_path.exists():
        return base_glyphs
    existing = json.loads(metadata_path.read_text(encoding="utf-8"))
    preserved = [
        glyph
        for glyph in existing.get("glyphs", [])
        if glyph.get("source_row") in {"synthetic", "russian_bmfont"}
    ]
    by_id: dict[int, dict[str, object]] = {int(glyph["char_id"]): glyph for glyph in base_glyphs}
    for glyph in preserved:
        by_id[int(glyph["char_id"])] = glyph
    return [by_id[key] for key in sorted(by_id)]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    out_root = project_root / "ttf-work" / "sheet-prototypes"
    out_root.mkdir(parents=True, exist_ok=True)

    families = [
        ("font_colored", "font_colored", "Stardew Valley Cyrillic Gameplay Prototype V9"),
        ("font_bold", "font_bold", "Stardew Valley Cyrillic Bold Prototype V9"),
    ]

    report: dict[str, object] = {"families": []}
    for family_key, rows_prefix, family_name in families:
        family_dir = project_root / "ttf-work" / family_key
        family_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = family_dir / "glyphs_from_rows.json"
        metadata, _glyphs = extract_family_glyphs(project_root, family_key, rows_prefix)
        metadata = merge_synthetic_glyphs(metadata, metadata_path)
        metadata_path.write_text(
            json.dumps({"family": family_key, "glyphs": metadata}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        ttf_path = out_root / (family_name.replace(" ", "") + ".ttf")
        build_ttf(ttf_path, family_name, metadata, family_dir / "glyphs")
        report["families"].append(
            {
                "family": family_key,
                "font_name": family_name,
                "glyph_count": len(metadata),
                "metadata_path": str(metadata_path),
                "ttf_path": str(ttf_path),
            }
        )

    report_path = out_root / "build-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
