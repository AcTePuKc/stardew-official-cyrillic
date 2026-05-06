from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def resolve_bmfont_repo() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        os.environ.get("BMFONT_PYTHON_ROOT"),
        r"C:\WebStuff\BMFont-Python",
        str(project_root.parent / "BMFont-Python"),
        str(project_root.parent.parent / "BMFont-Python"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not locate BMFont-Python. Set BMFONT_PYTHON_ROOT or place BMFont-Python next to this repo."
    )


BMFONT_REPO = resolve_bmfont_repo()
if str(BMFONT_REPO) not in sys.path:
    sys.path.insert(0, str(BMFONT_REPO))

from bmfont_tool.core.generator import GenerateOptions, generate_bmfont  # noqa: E402
from bmfont_tool.core.models import AdvancedExportSettings, AdvancedFontSettings, OutputFormat, StardewPackagingMode, TextureFormat  # noqa: E402
from bmfont_tool.stardew.spritefont import SPRITEFONT_READER_DATA  # noqa: E402


XNBNODE_DIR = BMFONT_REPO / ".private_stardew_mod" / "_tools" / "XNBNode"
HEADER = {
    "target": "w",
    "formatVersion": 5,
    "hidef": False,
    "compressed": False,
}


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, path.with_name(f"{path.name}.bak_before_family_regular_{stamp}"))


def install_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    backup_existing(dst)
    shutil.copy2(src, dst)
    return str(dst)


def native_json_to_template_source(native_json_path: Path) -> dict:
    data = json.loads(native_json_path.read_text(encoding="utf-8"))
    chars = data["Characters"]
    glyph_map = data["Glyphs"]

    return {
        "header": HEADER,
        "readers": SPRITEFONT_READER_DATA,
        "content": {
            "texture": {
                "format": 0,
                "export": "template.texture.png",
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


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    family_root = project_root / "font-family-work"
    output_root = family_root / "generated-small-sprite-regular"
    output_root.mkdir(parents=True, exist_ok=True)

    font_path = family_root / "StardewValleyCyrillicBG-Regular.ttf"
    metadata = json.loads((project_root / "russian-bg-work" / "glyphs_augmented.json").read_text(encoding="utf-8"))
    characters = "".join(glyph["char"] for glyph in metadata["glyphs"])
    mod_fonts_dir = project_root.parent.parent / "assets" / "Content" / "Fonts"

    assets = [
        ("SmallFont", project_root / "source-assets" / "SmallFont.ru-RU.json"),
        ("SpriteFont1", project_root / "source-assets" / "SpriteFont1.ru-RU.json"),
    ]

    reports: list[dict[str, object]] = []
    installed: list[str] = []

    for asset_name, template_path in assets:
        asset_output_dir = output_root / asset_name
        asset_output_dir.mkdir(parents=True, exist_ok=True)
        template_source = native_json_to_template_source(template_path)
        template_source_path = asset_output_dir / f"{asset_name}.template.source.json"
        template_source_path.write_text(json.dumps(template_source, indent=2, ensure_ascii=False), encoding="utf-8")
        result = generate_bmfont(
            GenerateOptions(
                font_path=font_path,
                output_dir=asset_output_dir,
                output_name=asset_name,
                characters=characters,
                font_size=42,
                atlas_width=1024,
                atlas_height=320,
                output_format=OutputFormat.STARDEW_VALLEY,
                advanced_settings=AdvancedFontSettings(
                    match_char_height=False,
                    height_percent=100,
                    output_invalid_glyph=False,
                    include_kerning_pairs=False,
                    render_from_outline=True,
                    true_type_hinting=False,
                    font_smoothing=False,
                    supersampling_level=1,
                ),
                advanced_export_settings=AdvancedExportSettings(
                    texture_format=TextureFormat.PNG,
                    stardew_packaging_mode=StardewPackagingMode.FULL_XNB,
                    stardew_template_path=str(template_source_path),
                    stardew_xnbnode_path=str(XNBNODE_DIR),
                ),
            )
        )

        xnb_path = next(path for path in result.extra_paths if path.suffix.lower() == ".xnb")
        installed.append(install_file(xnb_path, mod_fonts_dir / xnb_path.name))

        reports.append(
            {
                "asset_name": asset_name,
                "font_path": str(font_path),
                "template_path": str(template_path),
                "template_source_path": str(template_source_path),
                "output_dir": str(asset_output_dir),
                "generated_paths": [str(path) for path in result.extra_paths],
                "glyphs": len(result.font_data.glyphs),
                "line_height": result.font_data.line_height,
                "base": result.font_data.base,
            }
        )

    summary = {
        "font_path": str(font_path),
        "installed": installed,
        "assets": reports,
    }
    (output_root / "build-report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
