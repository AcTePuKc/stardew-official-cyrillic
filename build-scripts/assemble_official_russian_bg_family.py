from __future__ import annotations

import json
from pathlib import Path

from fontTools.ttLib import TTFont


FAMILY_NAME = "Stardew Valley Official Cyrillic BG"
MANUFACTURER = "Stardew Official Cyrillic Project"
DESIGNER = "Bitmap reconstruction and Bulgarian Cyrillic extension for Stardew Valley (Latin, Cyrillic, UI symbols)"


def set_name(font: TTFont, name_id: int, value: str) -> None:
    name_table = font["name"]
    for record in name_table.names:
        if record.nameID == name_id:
            record.string = value.encode("utf-16-be")


def configure_font(font: TTFont, *, style_name: str, full_name: str, ps_name: str, version: str, unique_id: str, weight: int, italic: bool, bold: bool) -> None:
    set_name(font, 1, FAMILY_NAME)
    set_name(font, 2, style_name)
    set_name(font, 3, unique_id)
    set_name(font, 4, full_name)
    set_name(font, 5, version)
    set_name(font, 6, ps_name)
    set_name(font, 16, FAMILY_NAME)
    set_name(font, 17, style_name)
    set_name(font, 8, MANUFACTURER)
    set_name(font, 9, DESIGNER)

    font["OS/2"].usWeightClass = weight
    selection = font["OS/2"].fsSelection
    if italic:
        selection |= 0x01
    else:
        selection &= ~0x01
    if bold:
        selection |= 0x20
    else:
        selection &= ~0x20
    if not italic and not bold:
        selection |= 0x40
    else:
        selection &= ~0x40
    font["OS/2"].fsSelection = selection

    mac_style = 0
    if bold:
        mac_style |= 0x01
    if italic:
        mac_style |= 0x02
    font["head"].macStyle = mac_style
    font["post"].italicAngle = -12.0 if italic else 0.0


def build_member(source_path: Path, dest_path: Path, *, style_name: str, ps_suffix: str, weight: int, italic: bool, bold: bool) -> dict[str, str]:
    font = TTFont(source_path)
    full_name = f"{FAMILY_NAME} {style_name}"
    ps_name = f"StardewValleyOfficialCyrillicBG-{ps_suffix}"
    version = "Version 1.0"
    unique_id = f"{full_name} 1.0"
    configure_font(
        font,
        style_name=style_name,
        full_name=full_name,
        ps_name=ps_name,
        version=version,
        unique_id=unique_id,
        weight=weight,
        italic=italic,
        bold=bold,
    )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(dest_path)
    return {
        "source": str(source_path),
        "output": str(dest_path),
        "style": style_name,
        "ps_name": ps_name,
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    family_root = project_root / "font-family-work"
    family_root.mkdir(parents=True, exist_ok=True)

    regular_src = project_root / "russian-bg-work" / "OfficialRussianCyrillicBGPrototypeV2.ttf"
    bold_src = project_root / "russian-bg-bold-work" / "OfficialRussianCyrillicBGBoldPrototypeV1.ttf"
    italic_src = project_root / "russian-bg-italic-work" / "OfficialRussianCyrillicBGItalicPrototypeV3.ttf"

    members = [
        build_member(
            regular_src,
            family_root / "StardewValleyOfficialCyrillicBG-Regular.ttf",
            style_name="Regular",
            ps_suffix="Regular",
            weight=400,
            italic=False,
            bold=False,
        ),
        build_member(
            bold_src,
            family_root / "StardewValleyOfficialCyrillicBG-Bold.ttf",
            style_name="Bold",
            ps_suffix="Bold",
            weight=700,
            italic=False,
            bold=True,
        ),
        build_member(
            italic_src,
            family_root / "StardewValleyOfficialCyrillicBG-Italic.ttf",
            style_name="Italic",
            ps_suffix="Italic",
            weight=400,
            italic=True,
            bold=False,
        ),
    ]

    report = {
        "family_name": FAMILY_NAME,
        "members": members,
    }
    (family_root / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
