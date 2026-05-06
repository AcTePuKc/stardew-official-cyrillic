from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


@dataclass
class GlyphRecord:
    char_id: int
    char: str
    x: int
    y: int
    width: int
    height: int
    xoffset: int
    yoffset: int
    xadvance: int
    page: int
    chnl: int
    image: str


PATTERN = re.compile(
    r'<char id="(?P<id>-?\d+)" x="(?P<x>\d+)" y="(?P<y>\d+)" width="(?P<width>\d+)" '
    r'height="(?P<height>\d+)" xoffset="(?P<xoffset>-?\d+)" yoffset="(?P<yoffset>-?\d+)" '
    r'xadvance="(?P<xadvance>-?\d+)" page="(?P<page>\d+)" chnl="(?P<chnl>\d+)" />'
)


def slug(char_id: int, char: str) -> str:
    return f"u{char_id:04X}"


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "source-assets"
    work_dir = project_root / "ttf-work"
    glyphs_dir = work_dir / "glyphs"
    metadata_path = work_dir / "glyphs.json"

    fnt_path = source_dir / "Russian.fnt"
    atlas_path = source_dir / "Russian_0.png"

    if glyphs_dir.exists():
        shutil.rmtree(glyphs_dir)
    glyphs_dir.mkdir(parents=True, exist_ok=True)
    atlas = Image.open(atlas_path).convert("RGBA")
    text = fnt_path.read_text(encoding="utf-8")

    common = re.search(
        r'<common lineHeight="(?P<lineHeight>\d+)" base="(?P<base>\d+)" scaleW="(?P<scaleW>\d+)" scaleH="(?P<scaleH>\d+)"',
        text,
    )
    if not common:
        raise RuntimeError("Could not parse BMFont common block.")

    records: list[GlyphRecord] = []
    for match in PATTERN.finditer(text):
        char_id = int(match.group("id"))
        if char_id < 0:
            continue
        char = chr(char_id)
        x = int(match.group("x"))
        y = int(match.group("y"))
        width = int(match.group("width"))
        height = int(match.group("height"))
        image_name = f"{slug(char_id, char)}.png"

        if width > 0 and height > 0:
            crop = atlas.crop((x, y, x + width, y + height))
            crop.save(glyphs_dir / image_name)
        else:
            Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(glyphs_dir / image_name)

        records.append(
            GlyphRecord(
                char_id=char_id,
                char=char,
                x=x,
                y=y,
                width=width,
                height=height,
                xoffset=int(match.group("xoffset")),
                yoffset=int(match.group("yoffset")),
                xadvance=int(match.group("xadvance")),
                page=int(match.group("page")),
                chnl=int(match.group("chnl")),
                image=image_name,
            )
        )

    payload = {
        "source": {
            "fnt": str(fnt_path),
            "atlas": str(atlas_path),
        },
        "common": {
            "lineHeight": int(common.group("lineHeight")),
            "base": int(common.group("base")),
            "scaleW": int(common.group("scaleW")),
            "scaleH": int(common.group("scaleH")),
        },
        "glyphs": [asdict(record) for record in records],
    }
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Extracted {len(records)} glyphs to {glyphs_dir}")
    print(f"Wrote metadata: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
