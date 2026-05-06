from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bmfont_tool.stardew import (  # noqa: E402
    convert_bmfont_to_spritefont_source,
    write_spritefont_source_json,
    write_xnbnode_yaml,
)


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(
            "Usage: python tools/build_stardew_spritefont_assets.py "
            "<input.fnt> <template.json> <texture_export.png> <output.json> <output.yaml>"
        )
        return 1

    fnt_path = Path(argv[1])
    template_path = Path(argv[2])
    texture_export = argv[3]
    output_json = Path(argv[4])
    output_yaml = Path(argv[5])

    source = convert_bmfont_to_spritefont_source(
        fnt_path=fnt_path,
        template_path=template_path,
        texture_export=texture_export,
    )
    write_spritefont_source_json(source, output_json)
    write_xnbnode_yaml(source, output_yaml)

    print(f"Wrote source JSON: {output_json}")
    print(f"Wrote XNBNode YAML: {output_yaml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
