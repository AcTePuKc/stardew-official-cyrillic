from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PANEL_PADDING_X = 28
PANEL_PADDING_Y = 20
LINE_GAP = 16
TITLE_HEIGHT = 34
BG_COLOR = (235, 211, 168, 255)
TITLE_COLOR = (107, 65, 28, 255)
GLYPH_COLOR = (97, 26, 13, 255)
LABEL_COLOR = (107, 65, 28, 255)
LABEL_GAP = 10


SAMPLE_SECTIONS = [
    ("Cyrillic-BG", "Аа Бб Вв Гг Дд Ее Жж Зз Ии Йй Кк Лл Мм Нн Оо Пп Рр Сс Тт Уу Фф Хх Цц Чч Шш Щщ Ъъ Ьь Юю Яя Ѝѝ"),
    ("Russian Extension", "Ёё Ыы Ээ"),
    ("Latin", "Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz"),
    ("SDV Used Glyphs", "0123456789  .,:;!?()[]{}<>+-= @ # №  \" '  «» „“  ★ ◆ ● ▲ ▼  → ← ↑ ↓"),
]


def load_records(metadata_path: Path, glyphs_dir: Path) -> dict[str, dict]:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    records: dict[str, dict] = {}
    for glyph in data["glyphs"]:
        char = glyph.get("char", chr(glyph["char_id"]))
        image_path = glyphs_dir / glyph["image"]
        if not image_path.exists():
            continue
        records[char] = {
            "char_id": glyph["char_id"],
            "char": char,
            "image_path": image_path,
            "xadvance": int(glyph.get("xadvance", 0)),
            "yoffset": int(glyph.get("yoffset", 0)),
        }
    return records


def nine_slice_panel(source: Image.Image, width: int, height: int, corner: int = 12) -> Image.Image:
    panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sw, sh = source.size

    def crop(box):
        return source.crop(box)

    tl = crop((0, 0, corner, corner))
    tr = crop((sw - corner, 0, sw, corner))
    bl = crop((0, sh - corner, corner, sh))
    br = crop((sw - corner, sh - corner, sw, sh))
    top = crop((corner, 0, sw - corner, corner))
    bottom = crop((corner, sh - corner, sw - corner, sh))
    left = crop((0, corner, corner, sh - corner))
    right = crop((sw - corner, corner, sw, sh - corner))
    center = crop((corner, corner, sw - corner, sh - corner))

    panel.alpha_composite(tl, (0, 0))
    panel.alpha_composite(tr, (width - corner, 0))
    panel.alpha_composite(bl, (0, height - corner))
    panel.alpha_composite(br, (width - corner, height - corner))

    for x in range(corner, width - corner, top.width):
        panel.alpha_composite(top, (x, 0))
        panel.alpha_composite(bottom, (x, height - corner))
    for y in range(corner, height - corner, left.height):
        panel.alpha_composite(left, (0, y))
        panel.alpha_composite(right, (width - corner, y))
    for x in range(corner, width - corner, center.width):
        for y in range(corner, height - corner, center.height):
            panel.alpha_composite(center, (x, y))

    return panel


def resolve_ui_panel_path() -> Path | None:
    explicit = os.environ.get("STARDEW_CONTENT_UNPACKED")
    candidates = []
    if explicit:
        candidates.append(Path(explicit) / "LooseSprites" / "textBox.png")
    candidates.append(Path(r"F:\SteamLibrary\steamapps\common\Stardew Valley\Content (unpacked)\LooseSprites\textBox.png"))
    for path in candidates:
        if path.exists():
            return path
    return None


def render_line(draw_target: Image.Image, glyphs: dict[str, dict], line: str, x: int, y: int) -> None:
    cursor = x
    for char in line:
        record = glyphs.get(char)
        if record is None:
            cursor += 10
            continue
        glyph = Image.open(record["image_path"]).convert("RGBA")
        alpha = glyph.getchannel("A")
        tinted = Image.new("RGBA", glyph.size, GLYPH_COLOR)
        tinted.putalpha(alpha)
        glyph = tinted
        draw_target.alpha_composite(glyph, (cursor, y + record["yoffset"]))
        cursor += max(1, record["xadvance"])


def measure_line(glyphs: dict[str, dict], line: str) -> int:
    width = 0
    for char in line:
        record = glyphs.get(char)
        if record is None:
            width += 10
            continue
        width += max(1, record["xadvance"])
    return width


def render_sheet(glyphs: dict[str, dict], output_path: Path, title: str, ui_panel_path: Path | None) -> None:
    label_font = ImageFont.load_default()
    line_height = max((Image.open(record["image_path"]).height + record["yoffset"] for record in glyphs.values()), default=24)
    label_width = max((ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), label, font=label_font)[2] for label, _ in SAMPLE_SECTIONS), default=120)
    widest_line = max((measure_line(glyphs, line) for _, line in SAMPLE_SECTIONS), default=900)
    total_text = f"And more ... total {len(glyphs)} glyphs"
    total_width = measure_line(glyphs, total_text)
    content_width = max(widest_line, total_width)
    width = max(1180, PANEL_PADDING_X * 2 + label_width + LABEL_GAP + content_width + 24)
    section_count = len(SAMPLE_SECTIONS) + 1
    height = TITLE_HEIGHT + PANEL_PADDING_Y * 2 + section_count * line_height + (section_count - 1) * LINE_GAP + 24

    image = Image.new("RGBA", (width, height), BG_COLOR)
    if ui_panel_path is not None:
        panel_source = Image.open(ui_panel_path).convert("RGBA")
        panel = nine_slice_panel(panel_source, width, height)
        image.alpha_composite(panel, (0, 0))
    else:
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=14, fill=(244, 224, 181, 255), outline=(123, 83, 39, 255), width=4)

    draw = ImageDraw.Draw(image)
    draw.text((PANEL_PADDING_X, 8), title, fill=TITLE_COLOR)

    baseline_y = TITLE_HEIGHT + PANEL_PADDING_Y
    sample_x = PANEL_PADDING_X + label_width + LABEL_GAP
    for idx, (label, line) in enumerate(SAMPLE_SECTIONS):
        y = baseline_y + idx * (line_height + LINE_GAP)
        draw.text((PANEL_PADDING_X, y + 2), f"{label}:", fill=LABEL_COLOR, font=label_font)
        render_line(image, glyphs, line, sample_x, y)

    footer_y = baseline_y + len(SAMPLE_SECTIONS) * (line_height + LINE_GAP)
    draw.text((PANEL_PADDING_X, footer_y + 2), "And more:", fill=LABEL_COLOR, font=label_font)
    render_line(image, glyphs, total_text, sample_x, footer_y)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    preview_root = project_root / "final-build" / "glyph-previews"
    preview_root.mkdir(parents=True, exist_ok=True)
    ui_panel_path = resolve_ui_panel_path()

    targets = [
        (
            "regular",
            project_root / "russian-bg-work" / "glyphs_augmented.json",
            project_root / "russian-bg-work" / "glyphs",
            "Regular Preview",
        ),
        (
            "bold",
            project_root / "russian-bg-bold-work" / "glyphs_augmented.json",
            project_root / "russian-bg-bold-work" / "glyphs",
            "Bold Preview",
        ),
        (
            "italic",
            project_root / "russian-bg-italic-work" / "glyphs_augmented.json",
            project_root / "russian-bg-italic-work" / "glyphs",
            "Italic Preview",
        ),
    ]

    outputs = []
    for key, metadata_path, glyphs_dir, title in targets:
        glyphs = load_records(metadata_path, glyphs_dir)
        output_path = preview_root / f"{key}_glyph_preview.png"
        render_sheet(glyphs, output_path, title, ui_panel_path)
        outputs.append(str(output_path))

    report = {"outputs": outputs}
    (preview_root / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
