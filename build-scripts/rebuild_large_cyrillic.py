from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
MOD_FONTS = ROOT.parent / "assets" / "Content" / "Fonts"
BASE_FNT = MOD_FONTS / "Cyrillic.fnt.bak_before_bg_full_pack_20260504_181907"
BASE_PNG = MOD_FONTS / "Cyrillic_0.png.bak_before_bg_full_pack_20260504_181907"


@dataclass
class Glyph:
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


PATTERN = re.compile(
    r'<char id="(?P<id>-?\d+)" x="(?P<x>\d+)" y="(?P<y>\d+)" width="(?P<width>\d+)" '
    r'height="(?P<height>\d+)" xoffset="(?P<xoffset>-?\d+)" yoffset="(?P<yoffset>-?\d+)" '
    r'xadvance="(?P<xadvance>-?\d+)" page="(?P<page>\d+)" chnl="(?P<chnl>\d+)" />'
)


def parse_glyphs(text: str) -> dict[int, Glyph]:
    glyphs: dict[int, Glyph] = {}
    for m in PATTERN.finditer(text):
        glyph = Glyph(
            char_id=int(m.group("id")),
            x=int(m.group("x")),
            y=int(m.group("y")),
            width=int(m.group("width")),
            height=int(m.group("height")),
            xoffset=int(m.group("xoffset")),
            yoffset=int(m.group("yoffset")),
            xadvance=int(m.group("xadvance")),
            page=int(m.group("page")),
            chnl=int(m.group("chnl")),
        )
        glyphs[glyph.char_id] = glyph
    return glyphs


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, path.with_name(f"{path.name}.bak_before_large_cyrillic_fix_{stamp}"))


def crop(atlas: Image.Image, glyph: Glyph) -> Image.Image:
    return atlas.crop((glyph.x, glyph.y, glyph.x + glyph.width, glyph.y + glyph.height))


def find_free_spot(occupied: list[tuple[int, int, int, int]], atlas: Image.Image, width: int, height: int, padding: int = 1) -> tuple[int, int]:
    for y in range(0, atlas.height - height + 1):
        for x in range(0, atlas.width - width + 1):
            left = x - padding
            top = y - padding
            right = x + width + padding
            bottom = y + height + padding
            hit = False
            for ox, oy, ow, oh in occupied:
                if left < ox + ow and right > ox and top < oy + oh and bottom > oy:
                    hit = True
                    break
            if not hit:
                return x, y
    raise RuntimeError(f"No free space for {width}x{height}")


def compose_grave(base: Image.Image, accent: Image.Image, accent_shift_x: int = -1, gap: int = 0) -> Image.Image:
    width = max(base.width, accent.width + max(0, accent_shift_x), base.width - min(0, accent_shift_x))
    height = accent.height + gap + base.height
    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    accent_x = max(0, (base.width - accent.width) // 2 + accent_shift_x)
    base_x = max(0, (width - base.width) // 2)
    result.alpha_composite(accent, (accent_x, 0))
    result.alpha_composite(base, (base_x, accent.height + gap))
    return result


def main() -> int:
    text = BASE_FNT.read_text(encoding="utf-8")
    atlas = Image.open(BASE_PNG).convert("RGBA")
    glyphs = parse_glyphs(text)

    upper_i = glyphs[1048]  # И
    lower_i = glyphs[1080]  # и
    accent = glyphs[96]     # `

    occupied = [(g.x, g.y, g.width, g.height) for g in glyphs.values() if g.width > 0 and g.height > 0]

    new_specs = {
        1037: (upper_i, compose_grave(crop(atlas, upper_i), crop(atlas, accent), accent_shift_x=-2), 0, -2, upper_i.xadvance),
        1117: (lower_i, compose_grave(crop(atlas, lower_i), crop(atlas, accent), accent_shift_x=-2), 0, -2, lower_i.xadvance),
    }

    for char_id, (base_glyph, image, xoffset, yoffset, xadvance) in new_specs.items():
        x, y = find_free_spot(occupied, atlas, image.width, image.height)
        atlas.alpha_composite(image, (x, y))
        occupied.append((x, y, image.width, image.height))
        glyphs[char_id] = Glyph(
            char_id=char_id,
            x=x,
            y=y,
            width=image.width,
            height=image.height,
            xoffset=xoffset,
            yoffset=yoffset,
            xadvance=xadvance,
            page=0,
            chnl=15,
        )

    chars_block = "\n".join(
        f'    <char id="{g.char_id}" x="{g.x}" y="{g.y}" width="{g.width}" height="{g.height}" '
        f'xoffset="{g.xoffset}" yoffset="{g.yoffset}" xadvance="{g.xadvance}" page="{g.page}" chnl="{g.chnl}" />'
        for g in sorted(glyphs.values(), key=lambda item: item.char_id)
    )
    text = re.sub(
        r'  <chars count="\d+">.*?  </chars>',
        f'  <chars count="{len(glyphs)}">\n{chars_block}\n  </chars>',
        text,
        flags=re.S,
    )

    out_fnt = ROOT / "final-assets" / "Cyrillic.fnt"
    out_png = ROOT / "final-assets" / "Cyrillic_0.png"
    out_fnt.parent.mkdir(parents=True, exist_ok=True)
    out_fnt.write_text(text, encoding="utf-8")
    atlas.save(out_png)

    installed_fnt = MOD_FONTS / "Cyrillic.fnt"
    installed_png = MOD_FONTS / "Cyrillic_0.png"
    backup_existing(installed_fnt)
    backup_existing(installed_png)
    shutil.copy2(out_fnt, installed_fnt)
    shutil.copy2(out_png, installed_png)

    print(f"Built {out_fnt}")
    print(f"Built {out_png}")
    print(f"Installed {installed_fnt}")
    print(f"Installed {installed_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
