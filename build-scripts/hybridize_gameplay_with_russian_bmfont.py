from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image


PATTERN = re.compile(
    r'<char id="(?P<id>-?\d+)" x="(?P<x>\d+)" y="(?P<y>\d+)" width="(?P<width>\d+)" '
    r'height="(?P<height>\d+)" xoffset="(?P<xoffset>-?\d+)" yoffset="(?P<yoffset>-?\d+)" '
    r'xadvance="(?P<xadvance>-?\d+)" page="(?P<page>\d+)" chnl="(?P<chnl>\d+)" />'
)


REPLACE_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "«»„“№"
)


def load_russian_records(project_root: Path) -> dict[int, dict[str, int]]:
    fnt_path = project_root / "source-assets" / "Russian.fnt"
    text = fnt_path.read_text(encoding="utf-8")
    records: dict[int, dict[str, int]] = {}
    for match in PATTERN.finditer(text):
        char_id = int(match.group("id"))
        if char_id < 0:
            continue
        records[char_id] = {
            "x": int(match.group("x")),
            "y": int(match.group("y")),
            "width": int(match.group("width")),
            "height": int(match.group("height")),
            "xoffset": int(match.group("xoffset")),
            "yoffset": int(match.group("yoffset")),
            "xadvance": int(match.group("xadvance")),
        }
    return records


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    records = load_russian_records(project_root)
    atlas = Image.open(project_root / "source-assets" / "Russian_0.png").convert("RGBA")

    family_dir = project_root / "ttf-work" / "font_colored"
    glyph_dir = family_dir / "glyphs"
    metadata_path = family_dir / "glyphs_from_rows.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    glyphs = payload["glyphs"]
    by_id = {int(g["char_id"]): g for g in glyphs}

    replaced: list[str] = []
    for char in REPLACE_CHARS:
        char_id = ord(char)
        record = records.get(char_id)
        if not record:
            continue
        filename = f"u{char_id:04X}_rus.png"
        width = record["width"]
        height = record["height"]
        if width > 0 and height > 0:
            crop = atlas.crop((record["x"], record["y"], record["x"] + width, record["y"] + height))
        else:
            crop = Image.new("RGBA", (1, 15), (0, 0, 0, 0))
        crop.save(glyph_dir / filename)
        by_id[char_id] = {
            "char": char,
            "char_id": char_id,
            "image": filename,
            "width": max(1, width),
            "height": max(1, crop.height),
            "xadvance": max(1, record["xadvance"]),
            "xoffset": record["xoffset"],
            "source_row": "russian_bmfont",
            "segment": 0,
        }
        replaced.append(char)

    payload["glyphs"] = [by_id[key] for key in sorted(by_id)]
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"replaced_count": len(replaced), "replaced": replaced}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
