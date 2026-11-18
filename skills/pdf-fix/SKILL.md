---
name: pdf-fix
description: >
  Turn a scanned book PDF (Internet Archive, photocopies, flatbed scans, two-page spreads)
  into a clean, readable, searchable, much smaller PDF using PdfCraft's pdfcraft-cli:
  remove covers/endpapers/scanner targets and duplicate scans, whiten sepia or color paper
  to black text on white, keep photos in grayscale, split two-page spreads into single
  pages, straighten tilted pages, put every page on a uniform size (default 6x9 in), OCR
  the text, make PDF page numbers match printed page numbers, and compress with JBIG2.
  Use when the user asks to fix, clean up, optimize, shrink, deskew, split, OCR or
  "make readable" a scanned PDF or book, or invokes /pdf-fix.
argument-hint: "<input.pdf> [output folder]"
---

# /pdf-fix — scanned book → clean PDF with PdfCraft

Everything that changes the PDF is done by **PdfCraft** (`pdfcraft-cli`). The helper script
`scripts/pdffix.py` (next to this file) drives it: it writes PdfCraft automation scripts, runs
them in parallel chunks, and checks the result. ImageMagick and OCR are only used to *measure*.

Read `reference.md` (same folder) when you need the PdfCraft tool details, the geometry, the
reasons behind the defaults, or a manual fallback without Python.

## Requirements (check first)

| Tool | Needed for | Install |
|---|---|---|
| `pdfcraft-cli` (PdfCraft ≥ 0.21) | everything | macOS: `brew install pdfcraft-cli` or the release zip · Linux: `.deb`/`.rpm`/tarball · Windows: the release zip; or `cargo install --path apps/pdfcraft-cli` from github.com/storytold/pdfcraft. Set `PDFCRAFT_CLI` if it is not on PATH. |
| Python 3.8+ | `scripts/pdffix.py` (standard library only) | macOS/Linux: `python3`; Windows: `py -3` |
| ImageMagick 7 (`magick`) or 6 (`convert`) | **required** for spreads (tilt), verify checks, contact sheets | `brew install imagemagick` · `sudo apt install imagemagick` · `winget install ImageMagick.ImageMagick` |
| OCR engine | text layer | PdfCraft's built-in `ocrs` needs its models: the desktop app ships them (the script finds them and sets `PDFCRAFT_MODELS`). Tesseract, if installed, is used as a second engine. |

Run the preflight and fix anything missing before going on:

```bash
python3 <skill-dir>/scripts/pdffix.py doctor
```

`<skill-dir>` is the folder containing this SKILL.md (e.g. `~/.claude/skills/pdf-fix`). On
Windows use `py -3` instead of `python3`. Work files go in a scratch folder (`--workdir`), never
next to the user's documents; reuse the same workdir to resume an interrupted run.

## Default preferences (from the user's past decisions)

Use these unless the user says otherwise — and still confirm the ones marked *ask*:

- **Readability beats file size.** Aim small (often < 10 MB is impossible losslessly), never by blurring text.
- **1-bit text at 400 ppi, black/white cutoff 65** (`--ppi 400 --level 65`). 300 ppi / cutoff 50 looked thin.
  **Exception — scans that already store text as a 1-bit mask** (Internet Archive "MRC", `inspect`
  shows a JBIG2 layer at a fixed ppi, often 360): render on that grid with `--render-dpi <mask ppi>`
  so the mask comes through pixel for pixel. Resampling it to another ppi blurs and thickens fine
  strokes (diacritics, Hebrew/Arabic/Syriac letters), and going above the mask ppi adds bytes, not detail.
- **Tables, script charts and other fine detail the user cares about** (e.g. Semitic-language
  tables) may go grayscale too (`--gray`), but each grayscale page costs ~300–350 KB at 300 ppi
  versus ~30–40 KB in 1-bit — never gray whole prose sections, and *ask* when the total would
  exceed the source's size.
- **Uniform 6 × 9 in pages** (`--page-size 6x9`), content at its real size, centered.
- **Remove** exterior covers, endpapers (patterned and their blank backs), scanner color charts / blank scanner sheets, and exact duplicate scans. **Keep** blank leaves inside the book (they keep the numbering right). *ask* when unsure.
- **Photos / halftone plates stay grayscale** (`--gray`); line art and stamps go 1-bit.
- **Reader's pen marks are kept** (they become black in 1-bit) unless the user asks otherwise.
- **PDF page numbers should match printed numbers** — via page labels (`--labels`) or by keeping pages so the offset is 0. *ask* which.
- **Title/Author** metadata set from the original or the title page.
- Output file: `<input name>_clean.pdf` in the folder the user names (*ask* if not given).

## Workflow

Keep a task list. Long runs (minutes) go in the background; report progress when they finish.

### 1. Evaluate (no changes yet)

```bash
python3 <skill-dir>/scripts/pdffix.py inspect IN.pdf --workdir WORK/inspect
python3 <skill-dir>/scripts/pdffix.py thumbs IN.pdf WORK/thumbs --dpi 14 --sheet --per-sheet 60 --cols 10
python3 <skill-dir>/scripts/pdffix.py thumbs IN.pdf WORK/ends --pages 1-14 --dpi 30 --sheet --per-sheet 14 --cols 7
```

Also render the last ~12 pages the same way. Look at the contact sheets (Read the PNGs) and
report to the user, as a short table:

- file size, pages, page size (and whether it varies), bytes/page;
- how the scan is stored: from `scan_images_sample` — pixel size, ppi, layers (Internet Archive
  "MRC" = a ~170 ppi color background + ~500 ppi color text layer + JBIG2 mask), already 1-bit?;
  `poppler`'s `pdfimages -list` gives encodings (jpx/jbig2/ccitt) if it is installed;
- **`extends_past_page: true`** → the visible page hides part of the scan and may cut text off;
- color vs sepia vs black-and-white; existing text layer (words) and its quality;
- printed-number offset (`printed_minus_pdf_page`), missing front pages, blank pages;
- covers, endpapers, scanner targets, duplicates (same headers on consecutive pages — compare
  thumbnails, or OCR the headers), photos/halftones, pen marks, sideways charts, maps;
- **two-page spreads** (`looks_like_spreads`), tilt, gutter shadows;
- implausible physical size (`suspicious_physical_size`, e.g. IA scans declaring 72 ppi → 34 × 54 in pages).

### 2. Ask before working

Use AskUserQuestion (self-contained questions, recommended option first) for whatever the
evaluation left open: pages to drop, numbering method, page size, resolution (400 ppi ≈ 35–50 KB
per page vs 300 ppi ≈ 25–35 KB), pen marks, grayscale pages, and for spreads the framing
(crop to the text block with even margins — recommended — or keep the full scanned page).

### 3a. Single book pages per PDF page → `build`

Test on a handful of pages first, look at them, then run everything:

```bash
python3 <skill-dir>/scripts/pdffix.py build IN.pdf WORK/test.pdf --workdir WORK/b --keep 5-14 --gray 8
python3 <skill-dir>/scripts/pdffix.py build IN.pdf OUT/name_clean.pdf --workdir WORK/b \
  --keep 5-476 --gray 8 --labels "1-8:lower-roman,9-:decimal:1" \
  --title "…" --author "…"
```

- `--keep`/`--skip` are **source** page numbers; `--labels` ranges are **output** page numbers.
- If the PDF's page size is wrong (IA 72 ppi), pass `--book-height-in 8` (the real page height).
- `--scale auto` fits the largest page into `--page-size`; `--trim 7` (points) removes dark
  scanner-bed slivers at the edges; `--clean 60` evens out yellowed/uneven paper first.
- `--trim-at 772-775:3` overrides the trim for some source pages — use it when a table or
  figure sits closer to the scan edge than `--trim` (a 7 pt trim clipped a table border 6 pt
  from the edge). Look for it with `verify`'s edge check and by eye on table pages.
- `--deskew` straightens tilted text pages (ImageMagick measures, PdfCraft rotates; a tilt is
  only applied when it makes the text rows sharper). Use it for flatbed or IA scans with
  visibly tilted pages.
- `--render-dpi N` renders at exactly N dpi and derives `--ppi` from the scale (see the
  1-bit-mask exception above). `--gray-ppi`/`--gray-quality` set grayscale pages (default 200 / 70).
- Defaults already match the preferences: `--ppi 400 --level 65 --page-size 6x9`.

### 3b. Two-page spreads → `spreads`

```bash
python3 <skill-dir>/scripts/pdffix.py spreads IN.pdf WORK/test.pdf --workdir WORK/s --only 2,15,50,140 --labels "1-:decimal:2"
python3 <skill-dir>/scripts/pdffix.py spreads IN.pdf OUT/name_clean.pdf --workdir WORK/s --skip 98 \
  --labels "1-:decimal:2" --gutter-only 274 --title "…" --author "…"
```

What it does, all with PdfCraft except measuring:
1. If the scan image is bigger than the visible page, expands each page to the **full scan**
   (the original crop can cut off letters and lines).
2. Finds words with PdfCraft `ocr_words`, the **gutter** (widest empty column between the two
   pages, with outliers re-searched near neighbouring spreads), and each page's **text block**.
3. Measures each page's **tilt** with ImageMagick `-deskew`, cross-checked against text-line
   slopes and settled by projection-profile sharpness (left pages often tilt 1–2°, right ones less).
4. Plans a crop window per page: text block centered, running head at the same height on every
   page, even margins on the 6 × 9 page. Pages without their own text block (blank, chapter
   openings, title pages) are placed from the facing page.
5. PdfCraft `page_enhance_camera` warps each rotated window upright (split + straighten + crop in
   one step), converts to 1-bit; `page_set_box` centers it; OCR; combine; labels; JBIG2.

It prints the output pages placed without their own text block — **look at each of them**.
Maps, sideways charts and plates often need `--gutter-only SPREAD` plus `--gutter-at
SPREAD:POINTS` (x of the gutter in full-scan points, read it off a thumbnail: pixels ÷ dpi × 72),
or `--extra-bottom SPREAD:L|R:INCHES` when something (e.g. a sticker, a caption) sits below the
text. Rerunning with the same `--workdir` redoes only what changed.

### 4. Verify, then deliver

```bash
python3 <skill-dir>/scripts/pdffix.py verify OUT/name_clean.pdf --workdir WORK/v
python3 <skill-dir>/scripts/pdffix.py thumbs OUT/name_clean.pdf WORK/out --dpi 14 --sheet
```

Check: one page size throughout; labels match printed numbers on most pages (misses are OCR
noise — spot-check them visually); `blank_pages` are exactly the expected blank leaves;
`tilt_over_0.3deg` near empty; `ink_at_page_edge` pages inspected (clipped content → fix with
`--extra-bottom`/`--gutter-at`/wider margins and rerun). Zoom into a dense paragraph at ~200 dpi
next to the original to confirm readability. Then report: before/after table (size, pages, page
size, resolution, tilt, OCR words, numbering), what was removed and why, anything not fixable
(e.g. a 200 ppi source stays soft; curved lines near the spine are not flattened).

## If the result is too big or too soft

- PdfCraft compresses 1-bit images **losslessly only** (JBIG2/CCITT), and `doc_optimize` will
  not usefully downsample 1-bit pages. Size per page tracks text density and resolution.
- Thin or broken letters → raise `--level` (65 → 75). Fuzzy edges → raise `--ppi` (300 → 400;
  the source's own resolution is the ceiling for detail). For a 1-bit-mask source use
  `--render-dpi` at the mask ppi instead.
- A well-made IA scan is often already compact (its JBIG2 mask is about what a lossless 1-bit
  rebuild costs). Then the gain is legibility — white paper, straight pages, a uniform page
  size, a better text layer — not size; tell the user so and don't promise a big reduction.
- Lossy JBIG2 (symbol matching) is not available: PdfCraft is lossless-only and ocrmypdf 17
  ignores `--jbig2-lossy`. Don't offer it.
