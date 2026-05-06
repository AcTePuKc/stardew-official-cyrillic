from __future__ import annotations

import json
from pathlib import Path


def build_entries(sheet: dict[str, object]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for row in sheet["rows"]:
        entries.append(
            {
                "row_index": row["row_index"],
                "y0": row["y0"],
                "y1": row["y1"],
                "height": row["height"],
                "component_count": row["component_count"],
                "proposed_role": None,
                "confirmed_characters": "",
                "notes": "",
            }
        )
    return entries


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    report_path = project_root / "bold-work" / "component_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    mapping = {
        "status": "template",
        "instructions": [
            "Use this file to map bold-sheet rows to character groups or UI symbols.",
            "Treat font_bold as the canonical geometry reference unless a row only exists in font_colored.",
            "Keep confirmed_characters ordered exactly as they appear left-to-right in the sheet.",
        ],
        "font_bold": build_entries(report["font_bold"]),
        "font_colored": build_entries(report["font_colored"]),
    }

    mapping_path = project_root / "bold-work" / "row_mapping_template.json"
    mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote mapping template to {mapping_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
