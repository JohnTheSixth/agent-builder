# pdf-fix reference

Details behind `SKILL.md` and `scripts/pdffix.py`, learned on real Internet Archive and
photocopied book scans.

## PdfCraft essentials

- `pdfcraft-cli run --script steps.json --report` runs a list of `{"tool": …, "args": …}` steps in
  one session and prints one JSON report (`ok`, per-step `result` or `error`). `pdfcraft-cli tools`
  prints every tool's JSON Schema — check it when a tool rejects an argument.
- `--root DIR` confines reads/writes to DIR; leave it off when the input lives elsewhere.
- Edits stay in memory until `doc_save`/`doc_optimize`/`page_extract` write a file.
- One big script slows down superlinearly as the document grows (undo history). Use chunks of
  24–40 pages run in parallel, then `doc_combine` (which adds one bookmark per file — drop them with
  `doc_optimize … discard: ["bookmarks"]`). With a single chunk, `doc_open` it instead.
- OCR: `ocr_status` shows engines. The built-in `ocrs` needs model files; the desktop app ships
  them (macOS: `/Applications/PdfCraft.app/Contents/Resources/models`) — export
  `PDFCRAFT_MODELS` to that folder. `engine: "auto", strategy: "rover"` combines ocrs and
  Tesseract and read best in tests. Set `OMP_THREAD_LIMIT=1` when running many chunks at once.

### Tools used and how

| Step | Tool | Notes |
|---|---|---|
| inspect | `doc_info` | per-page width/height/label, metadata |
| inspect | `page_images` | image pixel size, placement `rect`, `visible_rect` (rect past the page = hidden scan area) |
| render | `pdfcraft-cli render IN --page N --dpi D --out x.png` | composites MRC layers correctly; IA JPEG 2000 pages can't be enhanced in place, so render first |
| rebuild | `doc_create {from: images, paths, dpi}` | the dpi you pass sets page size = pixels ÷ dpi |
| whiten | `page_enhance_scan {level}` | evens illumination, removes yellow/sepia, edge shadows, specks; skips JPX/JBIG2/CCITT images |
| 1-bit / gray / crop / straighten | `page_enhance_camera {page, mode: bw|greyscale, level, corners}` | corners = any convex quad in top-left-origin points; it is warped to an upright rectangle of that size at the image's resolution. For bw, `level` is the cutoff (higher keeps fainter strokes black). |
| page size | `page_set_box {pages:[n], box: media, rect}` | rect may extend past the content (negative values) to pad white margins; one page per call when using `rect` |
| full scan | `page_set_box` media + crop to the image `rect` | reveals scan area the original crop hid |
| words | `ocr_words {pages, engine, dpi}` | boxes in points; `confidence` is null for ocrs — filter by word shape then |
| OCR | `ocr_recognize {engine, strategy, force_ocr}` | invisible text over the page; returns words per page |
| labels | `page_number {from, to, style, start}` | e.g. front matter i–viii, body from 1; or `start: 2` when printed page 1 is missing |
| finish | `doc_set_info {key, value}`, `doc_optimize` | `mono: {compression: jbig2}` (lossless, shared symbol dictionaries); gray JPEG q70 at 200 ppi |

## Numbers from real books

| Book (source) | Result |
|---|---|
| IA sepia scan, 484 pp, 100 MB, JPEG 2000 pages, 72 ppi declared | 472 pp, 1-bit 300 ppi, 10.0 MB (poetry, light pages) |
| IA MRC color scan, 411 pp, 26.7 MB, 514 ppi mask | 300 ppi cutoff 50: 15.4 MB, thin strokes · **400 ppi cutoff 65: 19.5 MB, clearly better** |
| Photocopied spreads, 278 spreads, 251 MB, 1-bit 200 ppi, hidden scan area | 554 pp at 6×9, 400 ppi, 28.1 MB, tilt < 0.3° |

Rules of thumb: 1-bit JBIG2 at 400 ppi ≈ 35–50 KB/page for dense prose; OCR text layer ≈ 4–7 KB/page;
grayscale JPEG pages cost 10–20× a 1-bit page (a whole book in grayscale ≈ 100+ MB).

## Spread geometry (what `spreads` computes)

- Coordinates: full-scan page points, top-left origin. Analysis renders at 200 dpi; production at `--ppi`.
- Tilt convention (ImageMagick): `%[deskew:angle]` = clockwise rotation that straightens the page.
  The crop window is defined in straightened space around the text-block centre C, and its corners
  are rotated by −angle about C to get the source quad for `page_enhance_camera`.
- Window: text-block width + `--side-margin` each side (2.4 in half-width for a 4.4 in block),
  from `--head-margin` (0.75 in) above the running head to 0.25 in below the deepest text. The
  running head (top of a full-height page's text) is the vertical anchor; pages without one use
  the facing page's. Facing text centres are a near-constant distance apart (5.46 ± 0.10 in in
  testing), which places blank/sparse pages reliably.
- If the window pokes above the scan, it starts lower and the top margin grows by the same amount.
- Noise control: words must be text-sized (4.3–32 pt boxes); lines need ≥ 2 words; the text block
  keeps lines inside the body's left/right edges and the largest vertically contiguous group.
  A gutter more than 1 in from its 6 nearest reliable spreads is re-searched near theirs.
- Pictures (maps, sideways charts) have too few text-sized words: mark them `--gutter-only` and,
  if they still sit off-centre, give `--gutter-at SPREAD:POINTS`.

## Pitfalls seen

- **Hidden scan area**: a 251 MB file stored A3 flatbed scans but showed only part of each; some
  pages lost first letters and bottom lines. Always compare `rect` with the page size.
- **Duplicate scans**: two consecutive spreads with the same page numbers (found by OCR-ing the
  headers: printed − expected offset jumps by 2). Drop one with `--skip`.
- **Missing first page**: the half-title wasn't scanned, so the book starts at printed page 2 →
  labels `1-:decimal:2` (or insert a blank page, if the user prefers real indexes to match).
- **Implausible page size**: IA files declaring 72 ppi make 34 × 54 in pages; set `--book-height-in`.
- **Pen underlining** turns solid black in 1-bit and competes with the text; only grayscale softens
  it (very expensive). Keep it unless the user wants otherwise.
- **Scanner-bed edges**: trim ~7 pt per edge (`--trim`) or the dark sliver becomes a black bar.
  Tables can sit closer to the edge than that — trim those pages less with `--trim-at`.
- **IA MRC scans** (mupdf producer): a low-ppi color JPX background, a color JPX foreground and a
  JBIG2 mask that carries all the text detail (360 ppi on recent IA books). Rendering at exactly
  the mask ppi (`--render-dpi 360`) reproduces it; rendering at 300 merged small dots and thickened
  Hebrew/Arabic/Syriac strokes. 1-bit at the mask ppi cost ~17% more than 300 ppi.
- **Grayscale cost**: ~300 KB/page for plates, tables and script charts and ~340 KB/page for
  prose at 300 ppi, quality 80 (quality 70 ≈ −15%, 250 ppi ≈ −30%). Gray only the pages that need it.
- `doc_optimize` downsamples gray/color only above `above_ppi` (the script sets 1.1 × `--gray-ppi`).
- **Tilt**: `--deskew` measures with ImageMagick `-deskew` on the text block, refines by row-profile
  sharpness, and applies only corrections between 0.15° and 3° that sharpen the rows. It is
  optional: a slight, uniform tilt with no overscan lines reads fine and costs nothing to keep;
  straightening matters when tilt varies a lot between pages (two-page scans) or brings overscan
  into view.
- `doc_optimize` reports `images_refused`/no change when asked to downsample 1-bit images — it
  only replaces an image when the result is smaller, which resampled bilevel images rarely are.
- The scanner bed can be black on some spreads and light gray on others — never detect the book
  by brightness alone; use the words.

## Manual fallback (no Python)

The same steps work by hand with `pdfcraft-cli`:

1. `pdfcraft-cli render IN.pdf --page N --dpi D --out pN.png` for each kept page (D = target ppi × scale;
   for a 1-bit-mask source use D = the mask ppi and target ppi = D ÷ scale).
2. Write a JSON script per chunk: `doc_create` (images, dpi = target ppi) → `page_enhance_scan`
   (level 60) → per page `page_enhance_camera` (bw, level 65, corners inset 7 pt) → `page_set_box`
   (media, centered rect on 432 × 648) → `ocr_recognize` (auto, rover) → `doc_save`.
3. Run chunks in parallel: `pdfcraft-cli run --script cNN.json --report`.
4. Final script: `doc_combine` → `page_number` → `doc_set_info` → `doc_optimize` (jbig2, discard bookmarks).
