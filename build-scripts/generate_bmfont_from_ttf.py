from __future__ import annotations

import json
import sys
from pathlib import Path


BMFONT_REPO = Path(r"C:\WebStuff\BMFont-Python")
if str(BMFONT_REPO) not in sys.path:
    sys.path.insert(0, str(BMFONT_REPO))

from bmfont_tool.core.generator import GenerateOptions, generate_bmfont  # noqa: E402
from bmfont_tool.core.models import AdvancedFontSettings, AdvancedExportSettings, OutputFormat, TextureFormat  # noqa: E402


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    work_dir = project_root / "ttf-work"
    output_dir = work_dir / "generated-bmfont"
    output_dir.mkdir(parents=True, exist_ok=True)

    ttf_path = work_dir / "output" / "StardewCyrillicPrototype-Win.ttf"
    metadata = json.loads((work_dir / "glyphs_augmented.json").read_text(encoding="utf-8"))
    characters = "".join(glyph["char"] for glyph in metadata["glyphs"])

    result = generate_bmfont(
        GenerateOptions(
            font_path=ttf_path,
            output_dir=output_dir,
            output_name="Cyrillic",
            characters=characters,
            font_size=34,
            atlas_width=512,
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

    print(f"Generated BMFont: {result.fnt_path}")
    for page in result.page_paths:
        print(f"Page: {page}")
    print(f"Glyphs: {len(result.font_data.glyphs)}")
    print(f"Line height: {result.font_data.line_height}")
    print(f"Base: {result.font_data.base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
