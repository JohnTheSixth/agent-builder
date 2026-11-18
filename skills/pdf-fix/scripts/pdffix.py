#!/usr/bin/env python3
"""pdffix — clean up scanned-book PDFs with PdfCraft (pdfcraft-cli).

Standard library only; runs on macOS, Linux and Windows (Python 3.8+).
Requires: pdfcraft-cli. Requires ImageMagick 7 (`magick`) or 6 (`convert`) for
`spreads`, `verify` tilt/edge checks and contact sheets. PdfCraft does every
edit to the PDF; ImageMagick only measures.

Subcommands
  doctor                       tools, OCR engines, model folder
  inspect IN                   structure: pages, sizes, scan images, text layer, numbering
  thumbs IN OUTDIR             low-res page renders (+ contact sheets with ImageMagick)
  build IN OUT                 one book page per PDF page: clean, 1-bit, resize, OCR, optimize
  spreads IN OUT               two-page spreads: split, straighten, crop, clean, OCR, optimize
  verify OUT                   page sizes, labels vs printed numbers, tilt, clipped ink

Run `pdffix.py <cmd> -h` for options. Every long step is resumable inside --workdir.
"""
import argparse, concurrent.futures as cf, glob, json, math, os, re, shutil, statistics as st, subprocess, sys, tempfile
from collections import Counter

# ---------------------------------------------------------------- tools

def which_pdfcraft():
    p = os.environ.get("PDFCRAFT_CLI") or shutil.which("pdfcraft-cli")
    if not p:
        sys.exit("pdfcraft-cli not found. Install PdfCraft's CLI (https://github.com/storytold/pdfcraft/releases, "
                 "Homebrew, or the Linux packages) or set PDFCRAFT_CLI to its full path.")
    return p


def which_magick():
    """ImageMagick 7 (`magick`) or 6 (`convert`); None if absent."""
    if shutil.which("magick"):
        return ["magick"]
    c = shutil.which("convert")
    if c and "imagemagick" in subprocess.run([c, "-version"], capture_output=True, text=True).stdout.lower():
        return [c]
    return None


CLI = None
MAGICK = None


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def run_steps(steps, workdir, name, root=None):
    """Run a PdfCraft automation script; return the parsed --report JSON. Raises on failure."""
    os.makedirs(workdir, exist_ok=True)
    path = os.path.join(workdir, name + ".json")
    with open(path, "w") as f:
        json.dump(steps, f)
    args = [CLI, "run", "--script", path, "--report"] + (["--root", root] if root else [])
    p = sh(args)
    try:
        rep = json.loads(p.stdout)
    except ValueError:
        raise RuntimeError(f"{name}: could not read PdfCraft report\n{p.stdout[-800:]}\n{p.stderr[-800:]}")
    with open(os.path.join(workdir, name + ".out.json"), "w") as f:
        json.dump(rep, f, indent=1)
    if not rep.get("ok"):
        bad = [s for s in rep.get("steps", []) if s.get("status") == "error"]
        raise RuntimeError(f"{name}: {bad[0].get('error') if bad else 'failed'}")
    return rep


def result(rep, i):
    r = rep["steps"][i].get("result")
    return r[0] if isinstance(r, list) and r else r


def model_dirs():
    """Likely places the PdfCraft desktop app keeps its ocrs models."""
    home = os.path.expanduser("~")
    c = [
        "/Applications/PdfCraft.app/Contents/Resources/models",
        os.path.join(home, "Applications/PdfCraft.app/Contents/Resources/models"),
        "/usr/share/pdfcraft/models", "/usr/lib/pdfcraft/models", "/opt/pdfcraft/models",
        os.path.join(os.path.dirname(os.path.realpath(CLI)), "models"),
        os.path.join(os.path.dirname(os.path.realpath(CLI)), "..", "share", "pdfcraft", "models"),
    ]
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            c += [os.path.join(base, "PdfCraft", "models"), os.path.join(base, "Programs", "PdfCraft", "models")]
    return [d for d in c if os.path.isdir(d)]


def ocr_status():
    tmp = tempfile.mkdtemp(prefix="pdffix-")
    rep = run_steps([{"tool": "ocr_status", "args": {}}], tmp, "ocr_status")
    return result(rep, 0)


def ensure_models():
    """Make the built-in ocrs engine usable: point PDFCRAFT_MODELS at the desktop app's models if needed."""
    s = ocr_status()
    eng = {e["id"]: e for e in s.get("engines", [])}
    if eng.get("ocrs", {}).get("available"):
        return s
    for d in model_dirs():
        os.environ["PDFCRAFT_MODELS"] = d
        s = ocr_status()
        if {e["id"]: e for e in s["engines"]}.get("ocrs", {}).get("available"):
            return s
    os.environ.pop("PDFCRAFT_MODELS", None)
    return ocr_status()


def ocr_engine(choice):
    """'auto' when both engines run, otherwise whichever one does; None if no OCR is possible."""
    if choice == "none":
        return None
    s = ensure_models()
    ok = {e["id"] for e in s.get("engines", []) if e.get("available")}
    if choice in ("ocrs", "tesseract"):
        if choice not in ok:
            sys.exit(f"OCR engine {choice} is not available: {s}")
        return choice
    if {"ocrs", "tesseract"} <= ok:
        return "auto"
    if ok:
        return ok.pop()
    print("warning: no OCR engine available; continuing without OCR", file=sys.stderr)
    return None


def magick(args):
    return sh(MAGICK + args)


def jobs_default():
    return max(1, min(8, (os.cpu_count() or 2)))


# ---------------------------------------------------------------- helpers

def parse_pages(spec, n):
    """'1-4,7,10-' -> sorted list of 1-based pages (open ranges run to n)."""
    if not spec:
        return []
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a) if a else 1
            b = int(b) if b else n
            out.update(range(a, b + 1))
        else:
            out.add(int(part))
    return sorted(p for p in out if 1 <= p <= n)


def parse_size(s):
    """'6x9' inches -> (432, 648) points; 'native' -> None."""
    if not s or s == "native":
        return None
    m = re.fullmatch(r"([\d.]+)x([\d.]+)", s.strip().lower())
    if not m:
        sys.exit(f"bad --page-size {s!r}: use e.g. 6x9 (inches) or native")
    return float(m.group(1)) * 72, float(m.group(2)) * 72


def parse_labels(spec, n):
    """'1-8:lower-roman,9-:decimal:1' or '1-:decimal:2' -> page_number steps args."""
    out = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        f = part.split(":")
        rng = f[0]; style = f[1] if len(f) > 1 else "decimal"; start = int(f[2]) if len(f) > 2 else 1
        a, _, b = rng.partition("-")
        a = int(a) if a else 1
        b = (int(b) if b else n) if "-" in rng else a
        out.append({"from": a, "to": min(b, n), "style": style, "start": start})
    return out


def doc_info(path, workdir):
    rep = run_steps([{"tool": "doc_open", "args": {"path": os.path.abspath(path)}},
                     {"tool": "doc_info", "args": {"doc": 1}}], workdir, "doc_info")
    return result(rep, 1)


def text_pages(path):
    p = sh([CLI, "text", os.path.abspath(path)])
    return p.stdout.split("\f")


NUM_RE = [re.compile(r"^(\d{1,4})\b"), re.compile(r"\b(\d{1,4})$")]


def printed_numbers(pages):
    """Best guess at the printed page number on each page (first/last 2 non-empty lines)."""
    out = []
    for p in pages:
        lines = [l.strip() for l in p.splitlines() if l.strip()]
        num = None
        for l in lines[:2] + lines[-2:]:
            for r in NUM_RE:
                m = r.search(l)
                if m:
                    num = int(m.group(1)); break
            if num is not None:
                break
        out.append(num)
    return out


def offsets(nums, labels=None):
    """Counter of printed-minus-expected; expected is the page's numeric label or its 1-based index."""
    c = Counter()
    for i, n in enumerate(nums, 1):
        if n is None:
            continue
        exp = i
        if labels and i - 1 < len(labels) and str(labels[i - 1]).isdigit():
            exp = int(labels[i - 1])
        c[n - exp] += 1
    return c


def pmap(fn, items, jobs):
    with cf.ThreadPoolExecutor(jobs) as ex:
        return list(ex.map(fn, items))


def render(path, page, dpi, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    p = sh([CLI, "render", os.path.abspath(path), "--page", str(page), "--dpi", f"{dpi:g}", "--out", out])
    if p.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"render page {page} failed: {p.stderr.strip()}")
    return out


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


# ---------------------------------------------------------------- doctor / inspect / thumbs

def cmd_doctor(a):
    print("pdfcraft-cli:", CLI, sh([CLI, "--version"]).stdout.splitlines()[0])
    s = ensure_models()
    for e in s.get("engines", []):
        print(f"  OCR {e['id']:9s}", "available" if e.get("available") else f"unavailable ({e.get('unavailable')})")
    if os.environ.get("PDFCRAFT_MODELS"):
        print("  PDFCRAFT_MODELS =", os.environ["PDFCRAFT_MODELS"], "(export this for manual pdfcraft-cli runs)")
    print("ImageMagick:", " ".join(MAGICK) if MAGICK else
          "NOT FOUND — required for spreads, tilt/edge checks and contact sheets "
          "(brew install imagemagick | sudo apt install imagemagick | winget install ImageMagick.ImageMagick)")
    print("Python:", sys.version.split()[0], "| CPUs:", os.cpu_count())


def cmd_inspect(a):
    wd = a.workdir or tempfile.mkdtemp(prefix="pdffix-inspect-")
    info = doc_info(a.input, wd)
    pages = info["pages"]; n = len(pages)
    sizes = Counter((round(p["width"]), round(p["height"])) for p in pages)
    sample = sorted({1, 2, n // 4 or 1, n // 2 or 1, (3 * n) // 4 or 1, n - 1 or 1, n})
    steps = [{"tool": "doc_open", "args": {"path": os.path.abspath(a.input)}}] + \
            [{"tool": "page_images", "args": {"doc": 1, "page": p}} for p in sample]
    rep = run_steps(steps, wd, "page_images")
    imgs = []
    for i, p in enumerate(sample, 1):
        r = result(rep, i)
        pg = pages[p - 1]
        for im in r.get("images", []):
            x0, y0, x1, y1 = im["rect"]
            w_in = (x1 - x0) / 72
            hidden = (x0 < -2 or y0 < -2 or x1 > pg["width"] + 2 or y1 > pg["height"] + 2)
            imgs.append({"page": p, "pixels": im["pixels"], "ppi": round(im["pixels"][0] / w_in) if w_in else None,
                         "rect": [round(v, 1) for v in im["rect"]], "extends_past_page": hidden})
    tp = text_pages(a.input)[:n]
    words = [len(t.split()) for t in tp]
    nums = printed_numbers(tp)
    off = offsets(nums)
    w_in = st.median(p["width"] for p in pages) / 72; h_in = st.median(p["height"] for p in pages) / 72
    report = {
        "file": a.input, "bytes": info.get("file_size"), "pages": n,
        "title": info.get("title"), "author": info.get("author"), "producer": info.get("producer"),
        "page_sizes_pt": [{"size": list(k), "count": v} for k, v in sizes.most_common(6)],
        "median_page_in": [round(w_in, 2), round(h_in, 2)],
        "looks_like_spreads": w_in > h_in * 1.15,
        "suspicious_physical_size": w_in > 12 or h_in > 16,
        "labels_first": [p.get("label") for p in pages[:8]],
        "scan_images_sample": imgs,
        "text_layer_words": sum(words),
        "pages_with_under_5_words": ([i for i, w in enumerate(words, 1) if w < 5][:80]
                                     if sum(w < 5 for w in words) < 0.5 * n else "most pages — no usable text layer"),
        "printed_minus_pdf_page": off.most_common(5),
    }
    print(json.dumps(report, indent=1))
    if report["suspicious_physical_size"]:
        print("\nNOTE: page size is implausible for a book (Internet Archive scans often declare 72 ppi). "
              "Use --book-height-in with `build` to set the real size.", file=sys.stderr)
    if any(i["extends_past_page"] for i in imgs):
        print("\nNOTE: scan images extend past the visible page; the page crop may hide text. "
              "`spreads` expands to the full scan automatically; for `build`, check renders of the full image.", file=sys.stderr)


def cmd_thumbs(a):
    info = doc_info(a.input, os.path.join(a.outdir, ".w"))
    n = len(info["pages"])
    pages = parse_pages(a.pages, n) if a.pages else list(range(1, n + 1))
    os.makedirs(a.outdir, exist_ok=True)
    outs = pmap(lambda p: render(a.input, p, a.dpi, os.path.join(a.outdir, f"p{p:04d}.png")), pages, a.jobs)
    print(f"{len(outs)} thumbnails in {a.outdir}")
    if MAGICK and a.sheet:
        per = a.per_sheet
        for k in range(0, len(outs), per):
            sheet = os.path.join(a.outdir, f"sheet_{pages[k]:04d}-{pages[min(k+per, len(pages))-1]:04d}.png")
            mont = (MAGICK + ["montage"]) if MAGICK[0].endswith("magick") else [shutil.which("montage") or "montage"]
            sh(mont + outs[k:k + per] + ["-tile", f"{a.cols}x", "-geometry", "+3+3", "-background", "#999999", sheet])
            if os.path.exists(sheet):   # montage may exit 1 over a missing label font yet write the sheet
                print("sheet:", sheet, f"(pages {pages[k]}-{pages[min(k+per, len(pages))-1]}, {a.cols} per row)")


# ---------------------------------------------------------------- shared finishing

def run_chunks(chunks, jobs, label):
    """chunks: list of (name, steps, workdir, out). Skips a chunk whose output exists and was made by identical steps."""
    import hashlib

    def sig(c):
        return hashlib.sha256(json.dumps(c[1], sort_keys=True).encode()).hexdigest()

    def done(c):
        s = c[3] + ".sig"
        return os.path.exists(c[3]) and os.path.exists(s) and open(s).read() == sig(c)
    todo = [c for c in chunks if not done(c)]
    print(f"{label}: {len(chunks) - len(todo)} chunk(s) already done, running {len(todo)} with {jobs} jobs", flush=True)

    def go(c):
        name, steps, wd, out = c
        rep = run_steps(steps, wd, name)
        with open(out + ".sig", "w") as f:
            f.write(sig(c))
        words = 0
        for s in rep["steps"]:
            if s["tool"] == "ocr_recognize":
                r = s["result"][0] if isinstance(s["result"], list) else s["result"]
                words = sum(p.get("words", 0) for p in r.get("pages", []))
        print(f"  {name} done ({words} OCR words)", flush=True)
        return words
    return sum(pmap(go, todo, jobs))


def finish(chunk_pdfs, out, wd, a, n_pages):
    steps = ([{"tool": "doc_combine", "args": {"paths": chunk_pdfs}}] if len(chunk_pdfs) > 1
             else [{"tool": "doc_open", "args": {"path": chunk_pdfs[0]}}])
    for lab in parse_labels(a.labels, n_pages):
        steps.append({"tool": "page_number", "args": {"doc": 1, **lab}})
    if a.title:
        steps.append({"tool": "doc_set_info", "args": {"doc": 1, "key": "Title", "value": a.title}})
    if a.author:
        steps.append({"tool": "doc_set_info", "args": {"doc": 1, "key": "Author", "value": a.author}})
    steps.append({"tool": "doc_optimize", "args": {
        "doc": 1, "path": os.path.abspath(out), "discard": ["bookmarks"],
        "mono": {"compression": "jbig2", "downsample": False},
        "gray": {"downsample": True, "ppi": a.gray_ppi, "above_ppi": round(a.gray_ppi * 1.1), "compression": "jpeg", "quality": a.gray_quality},
        "color": {"downsample": True, "ppi": a.gray_ppi, "above_ppi": round(a.gray_ppi * 1.1), "compression": "jpeg", "quality": a.gray_quality}}})
    rep = run_steps(steps, wd, "finish")
    r = result(rep, len(steps) - 1)
    print(f"wrote {out}: {r['bytes_after']:,} bytes ({r['bytes_before']:,} before optimizing)")


def ocr_step(engine, doc=1):
    return [{"tool": "ocr_recognize", "args": {"doc": doc, "engine": engine, "strategy": "rover", "force_ocr": True}}] if engine else []


# ---------------------------------------------------------------- build (one book page per PDF page)

def cmd_build(a):
    wd = os.path.abspath(a.workdir); os.makedirs(wd, exist_ok=True)
    info = doc_info(a.input, wd)
    pages = info["pages"]; n = len(pages)
    keep = parse_pages(a.keep, n) if a.keep else list(range(1, n + 1))
    keep = [p for p in keep if p not in set(parse_pages(a.skip, n))]
    gray = set(parse_pages(a.gray, n))
    target = parse_size(a.page_size)
    trim_pt = a.trim
    med_w = st.median(pages[p - 1]["width"] for p in keep); med_h = st.median(pages[p - 1]["height"] for p in keep)
    max_w = max(pages[p - 1]["width"] for p in keep); max_h = max(pages[p - 1]["height"] for p in keep)
    # scale: source points -> output points
    if a.book_height_in:
        scale = a.book_height_in * 72 / med_h
    elif a.scale not in (None, "auto"):
        scale = float(a.scale)
    elif target:
        scale = min(target[0] / max_w, target[1] / max_h)  # largest page fits, trim gives the margin
    else:
        scale = 1.0
    if med_w * scale / 72 > 12:
        sys.exit(f"pages would be {med_w*scale/72:.1f} in wide — the source size looks wrong; pass --book-height-in")
    if a.render_dpi:   # land the render on the source's own pixel grid (e.g. an IA text mask at 360 ppi)
        a.ppi = round(a.render_dpi / scale, 3)
    rdpi = a.ppi * scale
    trim_at = {}
    for spec in a.trim_at or []:
        pg, _, pt = spec.rpartition(":")
        if not pg:
            sys.exit(f"--trim-at {spec!r}: expected PAGES:POINTS, e.g. 772-775:3")
        for p in parse_pages(pg, n):
            trim_at[p] = float(pt)
    print(f"{len(keep)} pages | scale {scale:.4f} | render {rdpi:.1f} dpi -> {a.ppi} ppi | "
          f"output {'native size' if not target else f'{target[0]/72:g}x{target[1]/72:g} in'}")
    engine = ocr_engine(a.ocr)

    pdir = os.path.join(wd, "pages"); os.makedirs(pdir, exist_ok=True)
    pngs = pmap(lambda p: render(a.input, p, rdpi, os.path.join(pdir, f"p{p:04d}.png")), keep, a.jobs)
    print(f"rendered {len(pngs)} pages", flush=True)

    tilts = {}
    if a.deskew:
        if not MAGICK:
            sys.exit("--deskew needs ImageMagick (brew install imagemagick | sudo apt install imagemagick | winget install ImageMagick.ImageMagick)")
        tpath = os.path.join(wd, f"tilts_{a.ppi}_{rdpi:.2f}.json")
        tilts = {int(k): v for k, v in json.load(open(tpath)).items()} if os.path.exists(tpath) else {}
        todo = [p for p in keep if p not in tilts]
        for p, t in pmap(lambda p: (p, measure_tilt(os.path.join(pdir, f"p{p:04d}.png"))), todo, a.jobs):
            tilts[p] = t
        json.dump(tilts, open(tpath, "w"))
        moved = sorted((abs(t), p, t) for p, t in tilts.items() if t)
        print(f"straightening {len(moved)} page(s); largest: " +
              ", ".join(f"p{p} {t:+.2f}°" for _, p, t in moved[::-1][:8]), flush=True)

    chunks = []; cdir = os.path.join(wd, "chunks"); os.makedirs(cdir, exist_ok=True)
    for k in range(0, len(keep), a.chunk):
        part = keep[k:k + a.chunk]; files = [os.path.join(pdir, f"p{p:04d}.png") for p in part]
        steps = [{"tool": "doc_create", "args": {"from": "images", "paths": files, "dpi": a.ppi}}]
        if a.clean:
            steps.append({"tool": "page_enhance_scan", "args": {"doc": 1, "level": a.clean}})
        for i, (p, f) in enumerate(zip(part, files), 1):
            w, h = png_size(f); pw, ph = w / a.ppi * 72, h / a.ppi * 72; t = trim_at.get(p, trim_pt)
            is_gray = p in gray
            ang = tilts.get(p, 0.0)
            if ang:
                # trim enough that the rotated crop stays inside the scan
                s_, c_ = abs(math.sin(math.radians(ang))), math.cos(math.radians(ang))
                t = max(t, ph / 2 * s_ + pw / 2 * (1 - c_) + 1, pw / 2 * s_ + ph / 2 * (1 - c_) + 1)
                quad = [rot(x, y, pw / 2, ph / 2, -ang) for x, y in ((t, t), (pw - t, t), (pw - t, ph - t), (t, ph - t))]
                corners = [round(v, 2) for xy in quad for v in xy]
            else:
                corners = [t, t, pw - t, t, pw - t, ph - t, t, ph - t]
            steps.append({"tool": "page_enhance_camera", "args": {
                "doc": 1, "page": i, "mode": "greyscale" if is_gray else "bw",
                "level": a.gray_level if is_gray else a.level, "corners": corners}})
            if target:
                cw, ch = pw - 2 * t, ph - 2 * t
                if cw > target[0] + 0.5 or ch > target[1] + 0.5:
                    sys.exit(f"page {p} ({cw/72:.2f}x{ch/72:.2f} in) is bigger than the target page; lower --scale")
                ox, oy = (target[0] - cw) / 2, (target[1] - ch) / 2
                steps.append({"tool": "page_set_box", "args": {"doc": 1, "pages": [i], "box": "media", "rect": [-ox, -oy, cw + ox, ch + oy]}})
        steps += ocr_step(engine)
        out = os.path.join(cdir, f"c{k // a.chunk:03d}.pdf")
        steps.append({"tool": "doc_save", "args": {"doc": 1, "path": out}})
        chunks.append((f"c{k // a.chunk:03d}", steps, cdir, out))
    words = run_chunks(chunks, a.jobs, "build")
    finish([c[3] for c in chunks], a.output, wd, a, len(keep))
    if words:
        print(f"OCR words this run: {words:,}")


# ---------------------------------------------------------------- spreads (two book pages per PDF page)

def expand_full_scan(src, wd, n):
    """If the scan image is larger than the visible page, expand media+crop boxes to the whole image."""
    out = os.path.join(wd, "fullscan.pdf")
    if os.path.exists(out):
        return out, True
    steps = [{"tool": "doc_open", "args": {"path": os.path.abspath(src)}}] + \
            [{"tool": "page_images", "args": {"doc": 1, "page": p}} for p in range(1, n + 1)]
    rep = run_steps(steps, wd, "page_images_all")
    boxes = []
    for p in range(1, n + 1):
        ims = result(rep, p).get("images", [])
        if not ims:
            boxes.append(None); continue
        big = max(ims, key=lambda im: im["pixels"][0] * im["pixels"][1])
        x0, y0, x1, y1 = big["rect"]; vx0, vy0, vx1, vy1 = big["visible_rect"] or big["rect"]
        hidden = (vx0 - x0) + (vy0 - y0) + (x1 - vx1) + (y1 - vy1)
        boxes.append([x0, y0, x1, y1] if hidden > 0.02 * (x1 - x0) else None)
    if not any(boxes):
        return os.path.abspath(src), False
    steps = [{"tool": "doc_open", "args": {"path": os.path.abspath(src)}}]
    for p, b in enumerate(boxes, 1):
        if b:
            steps += [{"tool": "page_set_box", "args": {"doc": 1, "pages": [p], "box": bx, "rect": b}} for bx in ("media", "crop")]
    steps.append({"tool": "doc_save", "args": {"doc": 1, "path": out, "full": True}})
    run_steps(steps, wd, "expand")
    print(f"expanded {sum(1 for b in boxes if b)} page(s) to their full scan image", flush=True)
    return out, True


WORD_RE = re.compile(r"^[\"'(\[]?[A-Za-z][a-z]{2,}[,.;:!?)'\"\]]*$")


def good_word(w):
    t = (w.get("text") or "").strip()
    c = w.get("confidence")
    if c is not None:
        return c >= 70 and len(t) >= 2
    return bool(WORD_RE.match(t))


def ocr_words_pages(pdf, pages, engine, wd, jobs, dpi=200):
    """{page: [ {x0,y0,x1,y1} in points ]} via PdfCraft ocr_words, cached in wd."""
    cache = os.path.join(wd, "words.json")
    have = json.load(open(cache)) if os.path.exists(cache) else {}
    todo = [p for p in pages if str(p) not in have]
    batches = [todo[i:i + 12] for i in range(0, len(todo), 12)]

    def go(b):
        steps = [{"tool": "doc_open", "args": {"path": pdf}},
                 {"tool": "ocr_words", "args": {"doc": 1, "pages": b, "engine": engine, "dpi": dpi, "force_ocr": True}}]
        rep = run_steps(steps, os.path.join(wd, "ocrw"), f"w{b[0]:04d}")
        out = {}
        for pg in result(rep, 1)["pages"]:
            out[str(pg["page"])] = [{"x0": w["box"][0], "y0": w["box"][1], "x1": w["box"][0] + w["box"][2],
                                     "y1": w["box"][1] + w["box"][3]} for w in pg["words"] if good_word(w)]
        return out
    for i, res in enumerate(pmap(go, batches, max(1, jobs // 2))):
        have.update(res)
    json.dump(have, open(cache, "w"))
    return {int(k): v for k, v in have.items()}


def lines_from(words):
    """Group word boxes into text lines by vertical overlap; keep lines with 2+ words."""
    ws = sorted(words, key=lambda w: (w["y0"] + w["y1"]) / 2)
    lines, cur = [], []
    for w in ws:
        cy = (w["y0"] + w["y1"]) / 2; h = w["y1"] - w["y0"]
        if cur and abs(cy - st.mean((c["y0"] + c["y1"]) / 2 for c in cur)) > 0.5 * h:
            lines.append(cur); cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return [l for l in lines if len(l) >= 2]


def main_block(lines):
    """Drop OCR noise (scanner bed, gutter shadow): keep lines inside the body's left/right edges,
    then the largest vertically contiguous group of them."""
    if not lines:
        return []
    ext = [(min(w["x0"] for w in l), max(w["x1"] for w in l), min(w["y0"] for w in l), max(w["y1"] for w in l), l) for l in lines]
    body = [e for e in ext if len(e[4]) >= 4] or ext
    mx0 = st.median(e[0] for e in body); mx1 = st.median(e[1] for e in body)
    tol = 0.6 * 72
    keep = sorted((e for e in ext if e[0] >= mx0 - tol and e[1] <= mx1 + tol), key=lambda e: e[2])
    groups, cur = [], []
    for e in keep:
        if cur and e[2] - max(c[3] for c in cur) > 0.8 * 72:
            groups.append(cur); cur = []
        cur.append(e)
    if cur:
        groups.append(cur)
    best = max(groups, key=lambda g: sum(len(e[4]) for e in g)) if groups else []
    return [e[4] for e in best]


def gutter_of(words, page_w, expect=None):
    """x (points) halfway across the widest empty column between the two pages' words
    (only gaps centred within 1.5 in of `expect`, when given)."""
    if not words:
        return None
    step = 3.6  # 0.05 in
    nb = int(page_w / step) + 1; bins = [0] * nb
    for w in words:
        for b in range(max(0, int(w["x0"] / step)), min(nb - 1, int(w["x1"] / step)) + 1):
            bins[b] += 1
    noise = max(1, int(0.004 * len(words)))           # a stray word or two in the gutter shadow is not text
    bins = [0 if v <= noise else v for v in bins]
    occ = [i for i, v in enumerate(bins) if v]
    if not occ:
        return None
    best = None; i = occ[0]
    while i <= occ[-1]:
        if bins[i] == 0:
            j = i
            while bins[j] == 0:
                j += 1
            left = sum(1 for w in words if w["x1"] <= i * step)
            near = expect is None or abs((i + j) * step / 2 - expect) <= 1.5 * 72
            if near and 0.03 * len(words) <= left <= 0.97 * len(words) and (best is None or j - i > best[1] - best[0]):
                best = (i, j)
            i = j
        else:
            i += 1
    if best and (best[1] - best[0]) * step >= 0.4 * 72:
        return (best[0] + best[1]) * step / 2
    return None


def rot(px, py, cx, cy, deg):
    t = math.radians(deg); dx, dy = px - cx, py - cy
    return cx + dx * math.cos(t) - dy * math.sin(t), cy + dx * math.sin(t) + dy * math.cos(t)


def row_variance(png, box, ang):
    """Projection-profile sharpness of a crop after rotating by ang (ImageMagick)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    r = magick([png, "-crop", f"{w}x{h}+{x0}+{y0}", "+repage", "-background", "white", "-virtual-pixel", "white",
                "-distort", "SRT", f"{ang}", "-colorspace", "gray", "-threshold", "55%", "-negate",
                "-filter", "box", "-resize", f"1x{h}!", "-depth", "16", "txt:-"])
    v = [float(l.split("(")[1].split(")")[0].split(",")[0]) for l in r.stdout.splitlines()[1:] if "(" in l]
    return st.pvariance(v) if len(v) > 2 else 0.0


def page_tilt(png, scale, lines):
    """Tilt (deg, ImageMagick convention: rotate clockwise by this to straighten) for one page's text."""
    xs0 = min(w["x0"] for l in lines for w in l); xs1 = max(w["x1"] for l in lines for w in l)
    ys0 = min(w["y0"] for l in lines for w in l); ys1 = max(w["y1"] for l in lines for w in l)
    pad = 7.2
    box = [max(0, (xs0 - pad) * scale), max(0, (ys0 - pad) * scale), (xs1 + pad) * scale, (ys1 + pad) * scale]
    # slope of text lines from word bottoms
    slopes = []
    for l in lines:
        if len(l) < 4:
            continue
        l = sorted(l, key=lambda w: w["x0"]); xs = [(w["x0"] + w["x1"]) / 2 for w in l]; ys = [w["y1"] for w in l]
        if xs[-1] - xs[0] < 108:
            continue
        mx, my = st.mean(xs), st.mean(ys); den = sum((x - mx) ** 2 for x in xs)
        if den:
            slopes.append(math.degrees(math.atan(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den)))
    line_ang = -st.median(slopes) if len(slopes) >= 5 else None
    if not MAGICK:
        return line_ang or 0.0, "lines"
    r = magick([png, "-crop", f"{int(box[2]-box[0])}x{int(box[3]-box[1])}+{int(box[0])}+{int(box[1])}", "+repage",
                "-colorspace", "gray", "-deskew", "40%", "-format", "%[deskew:angle]", "info:"])
    try:
        im_ang = float(r.stdout.strip())
    except ValueError:
        im_ang = 0.0
    if abs(im_ang) > 3:
        im_ang = line_ang or 0.0
    if len(lines) < 5:
        return im_ang, "magick"
    cands = {round(im_ang, 2)}
    if line_ang is not None:
        cands.add(round(line_ang, 2))
    sc = {c: row_variance(png, box, c) for c in cands}
    b = max(sc, key=sc.get)
    for d in (-0.3, -0.2, -0.1, 0.1, 0.2, 0.3):
        c = round(b + d, 2)
        if c not in sc:
            sc[c] = row_variance(png, box, c)
    return max(sc, key=sc.get), "sharpest"


def measure_tilt(png):
    """Tilt to correct on one rendered page (ImageMagick convention), or 0.0 when it isn't clearly tilted.
    Only pages with a real block of text are measured, and the correction must sharpen the text rows."""
    W, H = png_size(png)
    r = magick([png, "-colorspace", "gray", "-threshold", "50%", "-format", "%@", "info:"]).stdout.strip()
    m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", r)
    if not m:
        return 0.0
    bw, bh, bx, by = map(int, m.groups())
    if bw < 0.5 * W or bh < 0.4 * H:
        return 0.0
    box = [bx, by, bx + bw, by + bh]
    try:
        ang = float(magick([png, "-crop", f"{bw}x{bh}+{bx}+{by}", "+repage", "-colorspace", "gray", "-resize", "50%",
                            "-deskew", "40%", "-format", "%[deskew:angle]", "info:"]).stdout.strip())
    except ValueError:
        return 0.0
    if abs(ang) < 0.15 or abs(ang) > 3:
        return 0.0
    s0 = row_variance(png, box, 0.0)
    sc = {round(ang + d, 2): 0.0 for d in (-0.1, 0.0, 0.1)}
    for k in sc:
        sc[k] = row_variance(png, box, k)
    best = max(sc, key=sc.get)
    return best if sc[best] > 1.03 * s0 and abs(best) >= 0.15 else 0.0


def cmd_spreads(a):
    wd = os.path.abspath(a.workdir); os.makedirs(wd, exist_ok=True)
    info = doc_info(a.input, wd); n = len(info["pages"])
    skip = set(parse_pages(a.skip, n))
    only = set(parse_pages(a.only, n)) if a.only else None
    spreads = [s for s in range(1, n + 1) if s not in skip and (only is None or s in only)]
    target = parse_size(a.page_size) or (432.0, 648.0)
    engine = ocr_engine(a.ocr) or "auto"
    src, expanded = expand_full_scan(a.input, wd, n)
    info2 = doc_info(src, os.path.join(wd, "info2"))
    PW = {i: p["width"] for i, p in enumerate(info2["pages"], 1)}
    if not MAGICK:
        sys.exit("spreads needs ImageMagick to measure page tilt. Install it (macOS: brew install imagemagick; "
                 "Debian/Ubuntu: sudo apt install imagemagick; Windows: winget install ImageMagick.ImageMagick) and rerun.")

    # 1. analysis renders + word boxes
    adpi = 200.0; sc = adpi / 72
    adir = os.path.join(wd, "a200"); os.makedirs(adir, exist_ok=True)
    pmap(lambda s: render(src, s, adpi, os.path.join(adir, f"s{s:04d}.png")), spreads, a.jobs)
    words = ocr_words_pages(src, spreads, engine, wd, a.jobs)
    print(f"word boxes for {len(words)} spreads", flush=True)

    # 2. per-spread geometry
    geom_path = os.path.join(wd, "geom.json")
    geom = json.load(open(geom_path)) if os.path.exists(geom_path) else {}

    def text_words(s):
        return [w for w in words.get(s, []) if 4.3 <= w["y1"] - w["y0"] <= 32]   # text-sized words only (~6-24 pt type)

    # pass 1: gutters; pass 2: re-search outliers near their neighbours' gutter
    forced = {int(e.split(":")[0]): float(e.split(":")[1]) for e in (a.gutter_at or [])}
    gut = {s: gutter_of(text_words(s), PW[s]) for s in spreads}

    def both_full(s):
        g = gut[s]; ws = text_words(s)
        return g is not None and sum(w["x1"] < g for w in ws) >= 80 and sum(w["x0"] > g for w in ws) >= 80
    reliable = {s: gut[s] for s in spreads if both_full(s)}
    for s in spreads:
        near = sorted((k for k in reliable if k != s), key=lambda k: abs(k - s))[:6]
        if near:
            m = st.median(reliable[k] for k in near)
            if s not in reliable or abs(gut[s] - m) > 1.0 * 72:
                g2 = gutter_of(text_words(s), PW[s], expect=m)
                print(f"  spread {s}: gutter {'not found' if gut[s] is None else f'{gut[s]/72:.2f} in'} "
                      f"-> {'%.2f in (gap near neighbours)' % (g2/72) if g2 else '%.2f in (neighbours)' % (m/72)}", file=sys.stderr)
                gut[s] = g2 or m
    gut.update(forced)

    def analyse(s):
        if str(s) in geom and geom[str(s)].get("gutter") == gut[s]:
            return s, geom[str(s)]
        ws = text_words(s)
        g = gut[s]
        pages = []
        for side in ("L", "R"):
            sw = [w for w in ws if g is not None and (((w["x0"] + w["x1"]) / 2 < g) == (side == "L"))]
            ls = main_block(lines_from(sw))
            if not ls:
                pages.append({"side": side, "desk": None, "angle": 0.0}); continue
            ang, how = page_tilt(os.path.join(adir, f"s{s:04d}.png"), sc, ls)
            x0 = min(w["x0"] for l in ls for w in l); x1 = max(w["x1"] for l in ls for w in l)
            y0 = min(w["y0"] for l in ls for w in l); y1 = max(w["y1"] for l in ls for w in l)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            pts = [rot(px, py, cx, cy, ang) for l in ls for w in l for px, py in
                   ((w["x0"], w["y0"]), (w["x1"], w["y0"]), (w["x0"], w["y1"]), (w["x1"], w["y1"]))]
            pages.append({"side": side, "angle": ang, "how": how, "center": [cx, cy], "n_lines": len(ls),
                          "desk": [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]})
        return s, {"gutter": g, "pages": pages}
    for s, gg in pmap(analyse, spreads, a.jobs):
        geom[str(s)] = gg
    json.dump(geom, open(geom_path, "w"), indent=1)

    # 3. layout plan
    plan = make_plan(geom, spreads, a, target)
    json.dump(plan, open(os.path.join(wd, "plan.json"), "w"), indent=1)
    kinds = Counter(p["kind"] for p in plan)
    print(f"plan: {len(plan)} pages {dict(kinds)}", flush=True)
    review = [f"{p['pdf_page']}(spread {p['spread']}{p['side']}, {p['kind']})" for p in plan if p["kind"] != "text"]
    if review:
        print("review these output pages (placed without their own text block):", ", ".join(review), flush=True)
    if a.plan_only:
        print("plan written; stopping (--plan-only)"); return

    # 4. full-resolution renders + PdfCraft split/straighten/clean/OCR
    rdir = os.path.join(wd, f"r{a.ppi}"); os.makedirs(rdir, exist_ok=True)
    pmap(lambda s: render(src, s, a.ppi, os.path.join(rdir, f"s{s:04d}.png")), sorted({p["spread"] for p in plan}), a.jobs)
    ocr = ocr_engine(a.ocr)
    cdir = os.path.join(wd, "chunks"); os.makedirs(cdir, exist_ok=True); chunks = []
    for k in range(0, len(plan), a.chunk):
        part = plan[k:k + a.chunk]
        steps = [{"tool": "doc_create", "args": {"from": "images", "dpi": a.ppi,
                                                 "paths": [os.path.join(rdir, f"s{p['spread']:04d}.png") for p in part]}}]
        for i, p in enumerate(part, 1):
            steps.append({"tool": "page_enhance_camera", "args": {"doc": 1, "page": i, "mode": "greyscale" if p["gray"] else "bw",
                                                                  "level": a.gray_level if p["gray"] else a.level, "corners": p["corners"]}})
            steps.append({"tool": "page_set_box", "args": {"doc": 1, "pages": [i], "box": "media", "rect": p["media"]}})
        steps += ocr_step(ocr)
        out = os.path.join(cdir, f"c{k // a.chunk:03d}.pdf")
        steps.append({"tool": "doc_save", "args": {"doc": 1, "path": out}})
        chunks.append((f"c{k // a.chunk:03d}", steps, cdir, out))
    run_chunks(chunks, a.jobs, "spreads")
    finish([c[3] for c in chunks], a.output, wd, a, len(plan))


def make_plan(geom, spreads, a, target):
    IN = 72.0
    def width(p): return (p["desk"][2] - p["desk"][0]) / IN if p.get("desk") else 0
    def height(p): return (p["desk"][3] - p["desk"][1]) / IN if p.get("desk") else 0
    allw = [width(p) for s in spreads for p in geom[str(s)]["pages"] if p.get("desk") and height(p) > 3]
    TW = st.median(allw) if allw else 4.4                       # typical text width
    def normal(p): return bool(p.get("desk")) and abs(width(p) - TW) <= 0.25 and height(p) > 1.5
    tallest = max([height(q) for s in spreads for q in geom[str(s)]["pages"]] or [1])
    def full(p): return normal(p) and height(p) > 0.8 * tallest
    dists = []
    for s in spreads:
        L, R = geom[str(s)]["pages"]
        if normal(L) and normal(R):
            dists.append((R["center"][0] - L["center"][0]) / IN)
    DIST = st.median(dists) if dists else 5.5
    below = [height(p) for s in spreads for p in geom[str(s)]["pages"] if full(p)] or [7.0]
    ABOVE = a.head_margin
    WIN_H = ABOVE + max(below) + 0.25
    TOP_PAD = max(0.1, (target[1] / IN - WIN_H) / 3)
    if TOP_PAD + WIN_H > target[1] / IN:
        sys.exit(f"text column ({WIN_H:.2f} in) is taller than the {target[1]/IN:g} in page; use a taller --page-size")
    HW = TW / 2 + a.side_margin
    tops = {s: [p["desk"][1] for p in geom[str(s)]["pages"] if full(p)] for s in spreads}
    gutters_found = {s: geom[str(s)]["gutter"] for s in spreads if geom[str(s)]["gutter"] is not None}
    gutter_only = set(parse_pages(a.gutter_only, max(spreads)))
    gray = set(a.gray_pages or [])
    extra = {}
    for e in a.extra_bottom or []:
        s, side, inch = e.split(":"); extra[(int(s), side.upper())] = float(inch)
    plan = []; idx = 0
    for s in spreads:
        g = geom[str(s)]
        gut = g["gutter"]
        if gut is None:
            near = [v for k, v in gutters_found.items() if abs(k - s) <= 6] or list(gutters_found.values()) or [0]
            gut = st.median(near)
        for i, p in enumerate(g["pages"]):
            idx += 1
            q = g["pages"][1 - i]; side = p["side"]; sign = -1 if side == "L" else 1
            ang = p.get("angle", 0.0) if p.get("desk") else 0.0
            if s in gutter_only:
                cx, cy, kind = gut + sign * DIST / 2 * IN, (q["center"][1] if q.get("desk") else 4.5 * IN), "gutter"
            elif normal(p):
                cx, cy = p["center"]; kind = "text"
            elif normal(q):
                cx, cy = q["center"][0] + sign * DIST * IN, q["center"][1]; kind = "from-facing"
            elif p.get("desk") and width(p) >= 1.0 and abs(p["center"][0] - (gut + sign * DIST / 2 * IN)) <= 1.0 * IN:
                cx, cy = p["center"]; kind = "own-partial"      # title pages etc.; noise elsewhere on the scan is ignored
            else:
                cx, cy = gut + sign * DIST / 2 * IN, 4.5 * IN; kind = "blank" if not p.get("desk") else "gutter"
            if full(p):
                yref = p["desk"][1]
            elif full(q):
                yref = q["desk"][1]
            else:
                k, near = 3, []
                while not near and k < 400:
                    near = [t for s2 in range(s - k, s + k + 1) for t in tops.get(s2, [])]; k += 2
                yref = st.median(near) if near else 1.1 * IN
            hw = HW if s not in gutter_only else min(target[0] / IN / 2 - 0.1, HW + 0.35)
            if normal(p):
                hw = max(hw, min(target[0] / IN / 2 - 0.1, width(p) / 2 + 0.12))
            wx0, wx1 = cx - hw * IN, cx + hw * IN
            wy0 = yref - ABOVE * IN
            wy1 = wy0 + (WIN_H + extra.get((s, side), 0)) * IN
            quad = [rot(x, y, cx, cy, -ang) for x, y in ((wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1))]
            shift = 0.0
            if min(y for _, y in quad) < 0:
                shift = -min(y for _, y in quad) / math.cos(math.radians(ang)) + 0.5
                wy0 += shift
                quad = [rot(x, y, cx, cy, -ang) for x, y in ((wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1))]
            ww, wh = wx1 - wx0, wy1 - wy0
            mx = (target[0] - ww) / 2; my = TOP_PAD * IN + shift
            plan.append({"spread": s, "side": side, "pdf_page": idx, "angle": round(ang, 3), "kind": kind,
                         "gray": idx in gray,
                         "corners": [round(v, 2) for xy in quad for v in xy],
                         "media": [round(-mx, 2), round(-my, 2), round(ww + mx, 2), round(-my + target[1], 2)]})
    return plan


# ---------------------------------------------------------------- verify

def cmd_verify(a):
    wd = a.workdir or tempfile.mkdtemp(prefix="pdffix-verify-")
    info = doc_info(a.input, wd); pages = info["pages"]; n = len(pages)
    sizes = Counter((round(p["width"], 1), round(p["height"], 1)) for p in pages)
    labels = [p.get("label") for p in pages]
    nums = printed_numbers(text_pages(a.input)[:n])
    off = offsets(nums, labels)
    out = {"file": a.input, "bytes": info.get("file_size"), "pages": n, "sizes_pt": dict((f"{k[0]}x{k[1]}", v) for k, v in sizes.items()),
           "labels_first": labels[:6], "printed_minus_label": off.most_common(4),
           "pages_matching_label": off.get(0, 0), "pages_with_a_number": sum(off.values())}
    if MAGICK:
        vdir = os.path.join(wd, "v"); os.makedirs(vdir, exist_ok=True)

        def check(p):
            f = render(a.input, p, 50, os.path.join(vdir, f"p{p:04d}.png"))
            t = magick([f, "-colorspace", "gray", "-deskew", "40%", "-format", "%[deskew:angle]", "info:"]).stdout.strip()
            b = magick([f, "-colorspace", "gray", "-threshold", "50%", "-fuzz", "5%", "-format", "%@", "info:"]).stdout.strip()
            w, h = png_size(f)
            m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", b)
            if not m or int(m.group(1)) <= 1:
                return p, None, None, True
            bw, bh, bx, by = map(int, m.groups())
            edge = bx <= 1 or by <= 1 or bx + bw >= w - 1 or by + bh >= h - 1
            dense = bw > 0.5 * w and bh > 0.4 * h        # tilt is only meaningful on a real block of text
            return p, (float(t or 0) if dense else None), edge, False
        res = pmap(check, list(range(1, n + 1)), a.jobs)
        tilts = sorted(((abs(t), p, t) for p, t, e, blank in res if t is not None), reverse=True)
        out["blank_pages"] = [p for p, _, _, blank in res if blank]
        out["tilt_over_0.3deg"] = [(p, round(t, 2)) for _, p, t in tilts if abs(t) > 0.3]
        out["ink_at_page_edge"] = [p for p, _, e, _ in res if e]
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- CLI

def main():
    global CLI, MAGICK
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("inspect"); p.add_argument("input"); p.add_argument("--workdir")
    p = sub.add_parser("thumbs"); p.add_argument("input"); p.add_argument("outdir")
    p.add_argument("--pages"); p.add_argument("--dpi", type=float, default=20); p.add_argument("--sheet", action="store_true")
    p.add_argument("--per-sheet", type=int, default=60); p.add_argument("--cols", type=int, default=10)
    p.add_argument("--jobs", type=int, default=jobs_default())

    def common(p):
        p.add_argument("input"); p.add_argument("output")
        p.add_argument("--workdir", required=True, help="scratch folder; rerun with the same folder to resume")
        p.add_argument("--ppi", type=float, default=400, help="output resolution of the 1-bit pages (default 400; fractional values allowed, e.g. to land the render on the source grid)")
        p.add_argument("--page-size", default="6x9", help="output page in inches, e.g. 6x9, or 'native' (build only)")
        p.add_argument("--level", type=int, default=65, help="black/white cutoff 0-100; higher = bolder text (default 65)")
        p.add_argument("--gray-level", type=int, default=60, help="cleanup level for grayscale pages (default 60)")
        p.add_argument("--labels", help="page labels, e.g. '1-8:lower-roman,9-:decimal:1' or '1-:decimal:2' (output page numbers)")
        p.add_argument("--title"); p.add_argument("--author")
        p.add_argument("--ocr", default="auto", choices=["auto", "ocrs", "tesseract", "none"])
        p.add_argument("--gray-ppi", type=int, default=200); p.add_argument("--gray-quality", type=int, default=70)
        p.add_argument("--jobs", type=int, default=jobs_default())
    p = sub.add_parser("build", help="one book page per PDF page"); common(p)
    p.add_argument("--keep", help="source pages to keep, e.g. 5-476 (default all)")
    p.add_argument("--skip", help="source pages to drop (duplicates, covers, scanner targets)")
    p.add_argument("--gray", help="source pages to keep in grayscale (photos, halftone plates)")
    p.add_argument("--scale", default="auto", help="source->output size factor (auto fits the largest page into --page-size)")
    p.add_argument("--book-height-in", type=float, help="real page height in inches when the PDF's page size is wrong")
    p.add_argument("--trim", type=float, default=7, help="points trimmed off every edge (scanner-bed slivers), default 7")
    p.add_argument("--clean", type=int, default=60, help="page_enhance_scan background removal 0-100 (0 = skip), default 60")
    p.add_argument("--deskew", action="store_true", help="straighten tilted text pages (measured with ImageMagick, rotated by PdfCraft)")
    p.add_argument("--render-dpi", type=float, help="render the source at exactly this dpi and derive --ppi from the scale; "
                   "set it to the scan's text-mask ppi (see inspect) so the mask comes through pixel for pixel")
    p.add_argument("--trim-at", action="append", help="SOURCE_PAGES:POINTS per-page trim, e.g. 772-775:3 for tables "
                   "close to the scan edge (repeatable; overrides --trim)")
    p.add_argument("--chunk", type=int, default=30)
    p = sub.add_parser("spreads", help="two book pages per PDF page"); common(p)
    p.add_argument("--skip", help="spreads (source pages) to drop, e.g. a duplicate re-scan")
    p.add_argument("--only", help="process only these spreads (for testing)")
    p.add_argument("--gutter-only", help="spreads positioned from the gutter (maps, sideways charts)")
    p.add_argument("--gray-pages", type=lambda s: [int(x) for x in s.split(",")], help="OUTPUT page numbers to keep grayscale")
    p.add_argument("--extra-bottom", action="append", help="SPREAD:L|R:INCHES extend a page's crop downward (repeatable)")
    p.add_argument("--gutter-at", action="append", help="SPREAD:POINTS force the gutter x position (full-scan points, from the left)")
    p.add_argument("--head-margin", type=float, default=0.75, help="space kept above the running head, inches")
    p.add_argument("--side-margin", type=float, default=0.2, help="space kept beside the text block, inches")
    p.add_argument("--plan-only", action="store_true", help="stop after writing plan.json")
    p.add_argument("--chunk", type=int, default=24)
    p = sub.add_parser("verify"); p.add_argument("input"); p.add_argument("--workdir")
    p.add_argument("--jobs", type=int, default=jobs_default())
    a = ap.parse_args()
    CLI = which_pdfcraft(); MAGICK = which_magick()
    {"doctor": cmd_doctor, "inspect": cmd_inspect, "thumbs": cmd_thumbs, "build": cmd_build,
     "spreads": cmd_spreads, "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    main()
