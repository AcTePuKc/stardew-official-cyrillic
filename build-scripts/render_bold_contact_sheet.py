from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PADDING = 8
LABEL_HEIGHT = 16
BACKGROUND = (245, 242, 232, 255)
ROW_BG = (255, 255, 255, 255)
TEXT = (36, 36, 36, 255)
OUTLINE = (210, 204, 190, 255)


def render_contact_sheet(sheet_name: str, source_path: Path, output_path: Path) -> None:
    source = Image.open(source_path).convert("RGBA")
    rows = sorted(output_path.parent.glob(f"{sheet_name}_row_*.png"))
    font = ImageFont.load_default()

    row_width = max((Image.open(row).width for row in rows), default=source.width)
    total_height = PADDING
    row_images: list[tuple[str, Image.Image]] = []
    for row in rows:
        row_image = Image.open(row).convert("RGBA")
        row_images.append((row.stem, row_image))
        total_height += LABEL_HEIGHT + row_image.height + PADDING

    canvas = Image.new("RGBA", (row_width + PADDING * 2, total_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    y = PADDING
    for label, row_image in row_images:
        draw.text((PADDING, y), label, fill=TEXT, font=font)
        y += LABEL_HEIGHT
        draw.rectangle((PADDING - 1, y - 1, PADDING + row_image.width, y + row_image.height), outline=OUTLINE, fill=ROW_BG)
        canvas.alpha_composite(row_image, (PADDING, y))
        y += row_image.height + PADDING

    canvas.save(output_path)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    rows_dir = project_root / "bold-work" / "rows"
    output_dir = project_root / "bold-work"
    render_contact_sheet(
        "font_bold",
        project_root / "source-assets" / "font_bold.png",
        output_dir / "font_bold_contact_sheet.png",
    )
    render_contact_sheet(
        "font_colored",
        project_root / "source-assets" / "font_colored.png",
        output_dir / "font_colored_contact_sheet.png",
    )
    print(f"Wrote contact sheets to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
