Personal project designed to streamline agent skill development.

## Contents

| Name | Skill | Agent | What it does |
|---|---|---|---|
| obsidian-plugin-finder | `skills/obsidian-plugin-finder/` | `agents/obsidian-plugin-finder.md` | Finds Obsidian plugins (or workarounds) for a described workflow. |
| pdf-fix | `skills/pdf-fix/` (`/pdf-fix`) | `agents/pdf-fix.md` | Turns scanned book PDFs into clean, straight, OCR'd, compact PDFs with PdfCraft: removes covers/duplicates, whitens sepia, splits two-page spreads, deskews, uniform page size, page labels, JBIG2. |

Skills are interactive (they ask before removing pages or choosing numbering); agents are the
same capability packaged for delegation, returning one report.

## Install into Claude Code

```bash
npm run link            # symlink agents/*.md and skills/* into ~/.claude
npm run link -- --force # replace existing entries
```

## pdf-fix requirements

- [PdfCraft](https://github.com/storytold/pdfcraft) `pdfcraft-cli` ≥ 0.21 (`brew install pdfcraft-cli`,
  Linux packages, or the release zips). The desktop app provides the built-in OCR models.
- Python 3.8+ (standard library only) for `skills/pdf-fix/scripts/pdffix.py`.
- ImageMagick 7 (`magick`) or 6 (`convert`) — required for two-page spreads, verification and contact sheets.
- Optional: Tesseract (second OCR engine used by PdfCraft), poppler `pdfimages` (shows image encodings).

Quick check: `python3 skills/pdf-fix/scripts/pdffix.py doctor`
