from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
MOD_FONTS_DIR = ROOT.parent / "assets" / "Content" / "Fonts"
BMFONT_REPO = Path(r"C:\WebStuff\BMFont-Python")
XNBNODE_DIR = BMFONT_REPO / ".private_stardew_mod" / "_tools" / "XNBNode"

if str(BMFONT_REPO) not in sys.path:
    sys.path.insert(0, str(BMFONT_REPO))

from bmfont_tool.stardew import pack_xnbnode_yaml, write_xnbnode_yaml  # noqa: E402


HEADER = {
    "target": "w",
    "formatVersion": 5,
    "hidef": False,
    "compressed": False,
}


def source_from_native_json(native_json_path: Path, texture_export_name: str) -> dict:
    data = json.loads(native_json_path.read_text(encoding="utf-8"))
    chars = data["Characters"]
    glyph_map = data["Glyphs"]

    return {
        "header": HEADER,
        "content": {
            "texture": {
                "format": 0,
                "export": texture_export_name,
            },
            "Glyphs": [glyph_map[ch]["BoundsInTexture"] for ch in chars],
            "Cropping": [glyph_map[ch]["Cropping"] for ch in chars],
            "Chars": chars,
            "Kerning": [
                {
                    "X": glyph_map[ch]["LeftSideBearing"],
                    "Y": glyph_map[ch]["Width"],
                    "Z": glyph_map[ch]["RightSideBearing"],
                }
                for ch in chars
            ],
            "LineSpacing": data["LineSpacing"],
            "Spacing": int(data["Spacing"]),
            "DefaultCharacter": data["DefaultCharacter"],
        },
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.name}.bak_before_bg_full_pack_{stamp}")
    shutil.copy2(path, backup)


def build_cyrillic_assets(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fnt_text = (ROOT / "Russian.bg.full.fnt").read_text(encoding="utf-8")
    fnt_text = fnt_text.replace('file="Russian_0.bg.full"', 'file="Cyrillic_0"')

    cyrillic_fnt = output_dir / "Cyrillic.fnt"
    cyrillic_png = output_dir / "Cyrillic_0.png"

    cyrillic_fnt.write_text(fnt_text, encoding="utf-8")
    shutil.copy2(ROOT / "Russian_0.bg.full.png", cyrillic_png)
    return [cyrillic_fnt, cyrillic_png]


def build_xnb_asset(asset_name: str, native_json_name: str, native_png_name: str, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_json = output_dir / f"{asset_name}.json"
    yaml_path = output_dir / f"{asset_name}.yaml"
    texture_path = output_dir / f"{asset_name}.texture.png"
    xnb_path = output_dir / f"{asset_name}.xnb"

    source = source_from_native_json(ROOT / native_json_name, texture_path.name)
    write_json(source_json, source)
    write_xnbnode_yaml(source, yaml_path)
    shutil.copy2(ROOT / native_png_name, texture_path)
    pack_xnbnode_yaml(xnbnode_dir=XNBNODE_DIR, yaml_path=yaml_path, output_xnb_path=xnb_path)
    return [source_json, yaml_path, texture_path, xnb_path]


def install_files(paths: list[Path], target_dir: Path) -> list[Path]:
    installed: list[Path] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        destination = target_dir / path.name
        backup_existing(destination)
        shutil.copy2(path, destination)
        installed.append(destination)
    return installed


def main() -> int:
    final_dir = ROOT / "final-assets"
    cyrillic_paths = build_cyrillic_assets(final_dir)
    small_paths = build_xnb_asset(
        asset_name="SmallFont",
        native_json_name="SmallFont.ru-RU.bg-full.json",
        native_png_name="SmallFont.ru-RU.bg-full.png",
        output_dir=final_dir,
    )
    sprite_paths = build_xnb_asset(
        asset_name="SpriteFont1",
        native_json_name="SpriteFont1.ru-RU.bg-full.json",
        native_png_name="SpriteFont1.ru-RU.bg-full.png",
        output_dir=final_dir,
    )

    installed = install_files(
        [
            *cyrillic_paths,
            next(path for path in small_paths if path.name == "SmallFont.xnb"),
            next(path for path in sprite_paths if path.name == "SpriteFont1.xnb"),
        ],
        MOD_FONTS_DIR,
    )

    summary = {
        "final_dir": str(final_dir),
        "installed": [str(path) for path in installed],
    }
    write_json(ROOT / "package-report.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
