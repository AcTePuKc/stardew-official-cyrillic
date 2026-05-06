from __future__ import annotations

import json
import zipfile
from pathlib import Path


RELEASE_INCLUDE = [
    "README.md",
    "BUILD.md",
    "LICENSE-CODE",
    "ASSET-NOTICE.md",
    "font-family-work/StardewValleyOfficialCyrillicBG-Regular.ttf",
    "font-family-work/StardewValleyOfficialCyrillicBG-Bold.ttf",
    "font-family-work/StardewValleyOfficialCyrillicBG-Italic.ttf",
    "font-family-work/generated-cyrillic-bold/Cyrillic.fnt",
    "font-family-work/generated-cyrillic-bold/Cyrillic_0.png",
    "final-build/glyph-previews",
]

SOURCE_INCLUDE = [
    "README.md",
    "BUILD.md",
    ".gitignore",
    "LICENSE-CODE",
    "ASSET-NOTICE.md",
    ".github/workflows/package-font-release.yml",
    "build-scripts",
    "source-assets/README.md",
    "russian-bg-work",
    "russian-bg-bold-work",
    "russian-bg-italic-work",
    "font-family-work/StardewValleyOfficialCyrillicBG-Regular.ttf",
    "font-family-work/StardewValleyOfficialCyrillicBG-Bold.ttf",
    "font-family-work/StardewValleyOfficialCyrillicBG-Italic.ttf",
    "final-build/glyph-previews",
]

EXCLUDE_SUFFIXES = {
    ".pyc",
}

EXCLUDE_PARTS = {
    "__pycache__",
}


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if ".bak_before_" in path.name:
        return True
    return False


def iter_files(root: Path, rel: Path):
    path = root / rel
    if not path.exists():
        return
    if path.is_file():
        if not should_skip(rel):
            yield path, rel
        return
    for child in sorted(path.rglob("*")):
        if child.is_dir():
            continue
        rel_child = child.relative_to(root)
        if should_skip(rel_child):
            continue
        yield child, rel_child


def build_zip(project_root: Path, output_path: Path, include_paths: list[str]) -> dict[str, object]:
    files_added: list[str] = []
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel_text in include_paths:
            rel = Path(rel_text)
            for src, rel_src in iter_files(project_root, rel):
                arc = str(rel_src).replace("\\", "/")
                zf.write(src, arcname=arc)
                files_added.append(arc)
    return {
        "bundle_path": str(output_path),
        "file_count": len(files_added),
        "files": files_added,
    }


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    dist_dir = project_root / "final-build" / "release-bundles"
    dist_dir.mkdir(parents=True, exist_ok=True)

    release_report = build_zip(
        project_root,
        dist_dir / "Stardew-Official-Cyrillic-Release.zip",
        RELEASE_INCLUDE,
    )
    source_report = build_zip(
        project_root,
        dist_dir / "Stardew-Official-Cyrillic-Source.zip",
        SOURCE_INCLUDE,
    )

    report = {
        "release": release_report,
        "source": source_report,
    }
    (dist_dir / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
