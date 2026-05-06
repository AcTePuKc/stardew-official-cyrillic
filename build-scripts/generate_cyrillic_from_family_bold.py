from __future__ import annotations

import json
import os
import re
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
from bmfont_tool.core.models import AdvancedExportSettings, AdvancedFontSettings, OutputFormat, TextureFormat  # noqa: E402


LINE_PATTERNS = {
    "info": re.compile(r'(\w+)=(".*?"|[^ ]+)'),
    "common": re.compile(r'(\w+)=(".*?"|[^ ]+)'),
    "page": re.compile(r'(\w+)=(".*?"|[^ ]+)'),
    "chars": re.compile(r'count=(\d+)'),
    "char": re.compile(r'(\w+)=(".*?"|[^ ]+)'),
}


def backup_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(path, path.with_name(f"{path.name}.bak_before_family_bold_{stamp}"))


def parse_attrs(text: str, kind: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, raw in LINE_PATTERNS[kind].findall(text):
        if isinstance(raw, tuple):
            raw = raw[0]
        values[key] = raw.strip('"')
    return values


def bmfont_text_to_xml(text_path: Path) -> None:
    lines = [line.strip() for line in text_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    info = parse_attrs(lines[0], "info")
    common = parse_attrs(lines[1], "common")
    index = 2
    pages: list[dict[str, str]] = []
    while index < len(lines) and lines[index].startswith("page "):
        pages.append(parse_attrs(lines[index], "page"))
        index += 1
    chars_match = LINE_PATTERNS["chars"].search(lines[index])
    if chars_match is None:
        raise ValueError(f"Could not parse chars count from line: {lines[index]}")
    chars_count = chars_match.group(1)
    char_lines = lines[index + 1 :]

    def fmt_attrs(attrs: dict[str, str], ordered_keys: list[str]) -> str:
        return " ".join(f'{key}="{attrs[key]}"' for key in ordered_keys if key in attrs)

    info_keys = ["face", "size", "bold", "italic", "charset", "unicode", "stretchH", "smooth", "aa", "padding", "spacing", "outline"]
    common_keys = ["lineHeight", "base", "scaleW", "scaleH", "pages", "packed", "alphaChnl", "redChnl", "greenChnl", "blueChnl"]
    page_keys = ["id", "file"]
    char_keys = ["id", "x", "y", "width", "height", "xoffset", "yoffset", "xadvance", "page", "chnl"]

    xml_lines = [
        '<?xml version="1.0"?>',
        "<font>",
        f'  <info {fmt_attrs(info, info_keys)}/>',
        f'  <common {fmt_attrs(common, common_keys)}/>',
        "  <pages>",
    ]
    for page in pages:
        xml_lines.append(f'    <page {fmt_attrs(page, page_keys)} />')
    xml_lines.extend([
        "  </pages>",
        f'  <chars count="{chars_count}">',
    ])

    for line in char_lines:
        attrs = parse_attrs(line, "char")
        xml_lines.append(f'    <char {fmt_attrs(attrs, char_keys)} />')

    xml_lines.extend([
        "  </chars>",
        "</font>",
        "",
    ])
    text_path.write_text("\n".join(xml_lines), encoding="utf-8")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    family_root = project_root / "font-family-work"
    output_dir = family_root / "generated-cyrillic-bold"
    output_dir.mkdir(parents=True, exist_ok=True)

    ttf_path = family_root / "StardewValleyCyrillicBG-Bold.ttf"
    metadata = json.loads((project_root / "russian-bg-work" / "glyphs_augmented.json").read_text(encoding="utf-8"))
    characters = "".join(glyph["char"] for glyph in metadata["glyphs"])

    result = generate_bmfont(
        GenerateOptions(
            font_path=ttf_path,
            output_dir=output_dir,
            output_name="Cyrillic",
            characters=characters,
            font_size=50,
            atlas_width=1024,
            atlas_height=512,
            output_format=OutputFormat.TEXT,
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
            ),
        )
    )

    fnt_path = result.fnt_path
    fnt_text = fnt_path.read_text(encoding="utf-8").replace('file="Cyrillic_0.png"', 'file="Cyrillic_0"')
    fnt_path.write_text(fnt_text, encoding="utf-8")
    bmfont_text_to_xml(fnt_path)

    mod_fonts_dir = project_root.parent.parent / "assets" / "Content" / "Fonts"
    installed = []
    install_sources = [fnt_path, *result.page_paths]
    for src in install_sources:
        dst = mod_fonts_dir / src.name
        backup_existing(dst)
        shutil.copy2(src, dst)
        installed.append(str(dst))

    report = {
        "font_path": str(ttf_path),
        "output_dir": str(output_dir),
        "fnt_path": str(fnt_path),
        "page_paths": [str(page) for page in result.page_paths],
        "glyphs": len(result.font_data.glyphs),
        "line_height": result.font_data.line_height,
        "base": result.font_data.base,
        "installed": installed,
    }
    (output_dir / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
