# Stardew Official Cyrillic Project

Goal: build a public, documented, Bulgarian-complete Stardew Valley font family and asset pipeline based on the game's official-style font assets.

## Licensing

This repository uses a split approach:

- `LICENSE-CODE` applies to the original scripts and documentation in this project.
- `ASSET-NOTICE.md` applies to game-derived assets and derivative bitmap/font materials.

Do not treat the whole repository as if it were fully MIT-licensed.

## Current state

- A reusable public font family now exists in three styles:
  - `Regular`
  - `Bold`
  - `Italic`
- The family is assembled under `font-family-work/` and can be installed for typing tests.
- A generated bold `Cyrillic.fnt` / `Cyrillic_0.png` test build now exists and is suitable for in-game comparison.
- `SmallFont.xnb` and `SpriteFont1.xnb` are now being regenerated from the same `Regular` family source, using the vanilla `ru-RU` SpriteFont templates as structural references.
- Glyph preview sheets are generated so other contributors can inspect and extend the glyph set more easily.

## Tooling

This project uses `bmfont_studio` / `BMFont-Python` as the main bitmap font generation toolchain:

- [bmfont_studio](https://github.com/AcTePuKc/bmfont_studio)

Some scripts in this repository expect that toolchain to be available locally, either via:

- `BMFONT_PYTHON_ROOT`
- a local `BMFont-Python` checkout
- a sibling `BMFont-Python` folder next to this repository

## Public metadata policy

Generated family fonts use:

- `Manufacturer`: `Stardew Official Cyrillic Project`
- `Designer/Foundry`: `Bitmap reconstruction and Bulgarian Cyrillic extension for Stardew Valley (Latin, Cyrillic, UI symbols)`

The goal is to describe the work as a community font reconstruction project rather than as a tool-generated prototype.

## Main outputs

### Installable font family

Located in `font-family-work/`:

- `StardewValleyOfficialCyrillicBG-Regular.ttf`
- `StardewValleyOfficialCyrillicBG-Bold.ttf`
- `StardewValleyOfficialCyrillicBG-Italic.ttf`

These are separate files, but they are also assembled as a single font family for operating system and design-tool use.

### Game font assets

Current generated test outputs include:

- large `Cyrillic.fnt` / `Cyrillic_0.png`
- `SmallFont.xnb`
- `SpriteFont1.xnb`

These are all derived from the same reconstructed source family, but each game layer still needs its own size and atlas tuning.

## Source references

### Large BMFont layer

- `source-assets/Russian.fnt`
- `source-assets/Russian_0.png`
- `source-assets/font_bold.png`
- `source-assets/font_colored.png`

### SpriteFont / XNB layer

- `source-assets/SmallFont.ru-RU.json`
- `source-assets/SmallFont.ru-RU.png`
- `source-assets/SpriteFont1.ru-RU.json`
- `source-assets/SpriteFont1.ru-RU.png`

Important finding:

- `SmallFont.ru-RU.json` and `SpriteFont1.ru-RU.json` are identical in the inspected vanilla assets
- `SmallFont.ru-RU.png` and `SpriteFont1.ru-RU.png` are also identical

## Folder guide

- `source-assets/`
  Local-only reference area for vanilla extracted font assets, if you want to regenerate some game-facing outputs yourself.
- `build-scripts/`
  Reproducible build, packaging, assembly, and preview scripts.
- `russian-bg-work/`
  Regular-font glyph source, metadata, and prototype outputs.
- `russian-bg-bold-work/`
  Bold-font glyph source, metadata, and prototype outputs.
- `russian-bg-italic-work/`
  Italic-font glyph source, metadata, and prototype outputs.
- `font-family-work/`
  Assembled `Regular/Bold/Italic` family files and current game-asset generation outputs.
- `final-build/`
  Final-ish public-facing artifacts such as glyph previews.
- `notes/`
  Coverage notes, forensic findings, limitations, and roadmap.

## Glyph preview assets

To make future extension easier, the project generates contact sheets for the current glyph sets:

- `final-build/glyph-previews/regular_glyph_contact_sheet.png`
- `final-build/glyph-previews/bold_glyph_contact_sheet.png`
- `final-build/glyph-previews/italic_glyph_contact_sheet.png`

These are intended as a contributor aid, so people can quickly inspect what exists and what still needs cleanup or extension.
