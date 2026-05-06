from __future__ import annotations

import json
from pathlib import Path


def unique_preserve_order(text: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for char in text:
        if char not in seen:
            seen.add(char)
            out.append(char)
    return "".join(out)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    mapping_path = project_root / "bold-work" / "row_mapping_template.json"
    data = json.loads(mapping_path.read_text(encoding="utf-8"))

    rows = data["font_colored"]
    ordered_chunks: list[str] = []
    included_rows: list[int] = []
    skipped_rows: list[int] = []

    for row in rows:
        chars = row["confirmed_characters"]
        if chars:
            ordered_chunks.append(chars)
            included_rows.append(int(row["row_index"]))
        else:
            skipped_rows.append(int(row["row_index"]))

    merged = "".join(ordered_chunks)
    charset = unique_preserve_order(merged)

    output_dir = project_root / "gameplay-work"
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "gameplay_charset_seed.txt").write_text(charset, encoding="utf-8")
    report = {
        "status": "seed",
        "source_family": "font_colored",
        "source_mapping": str(mapping_path),
        "included_rows": included_rows,
        "skipped_rows": skipped_rows,
        "character_count": len(charset),
        "characters": charset,
    }
    (output_dir / "gameplay_charset_seed.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
