# Build Guide

This repository is intended to support three practical workflows:

1. edit glyph PNGs and rebuild `Regular`, `Bold`, or `Italic`
2. generate a large `Cyrillic.fnt` / `Cyrillic_0.png` from the family `Bold`
3. generate `SmallFont.xnb` / `SpriteFont1.xnb` from the family `Regular`

## Requirements

- Python 3.11+
- [`bmfont_studio` / `BMFont-Python`](https://github.com/AcTePuKc/bmfont_studio)
- `XNBNode` for `SmallFont` / `SpriteFont1` packing
- locally extracted vanilla Stardew template references if you want to regenerate `SmallFont` / `SpriteFont1`

The public scripts auto-detect `BMFont-Python` in these ways:

1. `BMFONT_PYTHON_ROOT` environment variable
2. `C:\WebStuff\BMFont-Python`
3. a sibling `BMFont-Python` folder next to this repo

## Rebuild a family member from edited glyphs

Edit glyph PNG files inside one of these folders:

- `russian-bg-work/glyphs/`
- `russian-bg-bold-work/glyphs/`
- `russian-bg-italic-work/glyphs/`

Then rebuild:

```powershell
python build-scripts/rebuild_family_member_from_existing_glyphs.py --member regular
python build-scripts/rebuild_family_member_from_existing_glyphs.py --member bold
python build-scripts/rebuild_family_member_from_existing_glyphs.py --member italic
```

## Assemble the installable family

```powershell
python build-scripts/assemble_official_russian_bg_family.py
```

This produces:

- `font-family-work/StardewValleyOfficialCyrillicBG-Regular.ttf`
- `font-family-work/StardewValleyOfficialCyrillicBG-Bold.ttf`
- `font-family-work/StardewValleyOfficialCyrillicBG-Italic.ttf`

## Generate large Cyrillic BMFont assets

```powershell
python build-scripts/generate_cyrillic_from_family_bold.py
```

This generates a large `Cyrillic.fnt` / `Cyrillic_0.png` test build from the `Bold` family member.

## Generate `SmallFont` and `SpriteFont1`

```powershell
python build-scripts/generate_smallfont_spritefont_from_family_regular.py
```

This generates:

- `SmallFont.xnb`
- `SpriteFont1.xnb`

from the `Regular` family member, using the vanilla `ru-RU` SpriteFont templates as structural references.

Before running that step, place your own locally extracted reference files here:

- `source-assets/SmallFont.ru-RU.json`
- `source-assets/SpriteFont1.ru-RU.json`

## Generate glyph preview sheets

```powershell
python build-scripts/render_glyph_contact_sheets.py
```

This updates:

- `final-build/glyph-previews/regular_glyph_contact_sheet.png`
- `final-build/glyph-previews/bold_glyph_contact_sheet.png`
- `final-build/glyph-previews/italic_glyph_contact_sheet.png`

## Package a public archive

```powershell
python build-scripts/package_release_bundle.py
```

This creates a release-oriented `.zip` bundle in:

- `final-build/release-bundles/`

## Current recommendation

For public collaboration:

- keep glyph editing centered around the `russian-bg-*` folders
- treat `font-family-work/` as assembled deliverables
- treat generated game assets as test outputs, not as the only source of truth
