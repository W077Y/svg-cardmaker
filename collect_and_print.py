#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect & Print Sheets for SVG Cards (Magic-size)
- Reads individual SVG card files (63x88 mm design; e.g., 744x1039 px)
- Rasterizes them with Inkscape (CLI), then packs them 3x3 per A4 page at 300 dpi
- Adds optional crop marks
- Writes a multi-page PDF

Usage example:
python collect_and_print.py --cards ./cards \
  --add "Sword_of_the_Autumn_Wolf=10" \
  --add "Potion_of_Brightmind=5" \
  --out sheets/cards_print.pdf --dpi 300 --crop

Requires: Inkscape in PATH (for SVG rasterization). Pillow for PDF assembly.
"""
import argparse, os, math, shutil, subprocess, tempfile
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw

def find_inkscape() -> str:
    exe = shutil.which("inkscape")
    if exe:
        return exe
    candidates = [
        r"C:\Program Files\Inkscape\bin\inkscape.exe",
        r"C:\Program Files\Inkscape\inkscape.exe",
        r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
        r"C:\Program Files (x86)\Inkscape\inkscape.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return str(c)
    return ""

def rasterize_svg(inkscape_exe: str, svg_path: Path, out_png: Path, width_px: int, height_px: int, dpi: int) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        inkscape_exe,
        "--export-type=png",
        f"--export-filename={str(out_png)}",
        f"--export-width={width_px}",
        f"--export-height={height_px}",
        "--export-dpi", str(dpi),
        str(svg_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Inkscape export failed for {svg_path.name}:\n{result.stderr}")

def a4_dimensions(dpi: int, orientation: str):
    if orientation == "a4portrait":
        w_in, h_in = 8.267716535, 11.692913386
    else:
        w_in, h_in = 11.692913386, 8.267716535
    return int(round(w_in * dpi)), int(round(h_in * dpi))

def layout_positions(sheet_w: int, sheet_h: int, card_w: int, card_h: int, cols: int, rows: int, margin_px: int, gutter_px: int):
    positions = []
    total_cards_w = cols*card_w + (cols-1)*gutter_px
    total_cards_h = rows*card_h + (rows-1)*gutter_px
    x0 = (sheet_w - total_cards_w)//2
    y0 = (sheet_h - total_cards_h)//2
    for r in range(rows):
        for c in range(cols):
            x = x0 + c*(card_w + gutter_px)
            y = y0 + r*(card_h + gutter_px)
            positions.append((x,y))
    return positions

def draw_crop_marks(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, bleed:int=0, len_px: int=24, offset:int=6, color=(0,0,0)):
    draw.line([(x - offset - len_px, y - offset), (x - offset, y - offset)], fill=color, width=1)
    draw.line([(x - offset, y - offset - len_px), (x - offset, y - offset)], fill=color, width=1)
    draw.line([(x + w + offset, y - offset), (x + w + offset + len_px, y - offset)], fill=color, width=1)
    draw.line([(x + w + offset, y - offset - len_px), (x + w + offset, y - offset)], fill=color, width=1)
    draw.line([(x - offset - len_px, y + h + offset), (x - offset, y + h + offset)], fill=color, width=1)
    draw.line([(x - offset, y + h + offset), (x - offset, y + h + offset + len_px)], fill=color, width=1)
    draw.line([(x + w + offset, y + h + offset), (x + w + offset + len_px, y + h + offset)], fill=color, width=1)
    draw.line([(x + w + offset, y + h + offset), (x + w + offset, y + h + offset + len_px)], fill=color, width=1)

def collect_files(cards_dir: Path, requests):
    index = {}
    for p in cards_dir.glob("*.svg"):
        index[p.stem.lower()] = p
    out = []
    for base, count in requests:
        key = base.lower()
        if key not in index:
            raise FileNotFoundError(f"Card SVG '{base}.svg' not found in {cards_dir}")
        out.extend([index[key]]*count)
    return out

def make_sheets(svg_paths, out_pdf: Path, dpi: int = 300, orientation: str = "a4portrait", cols:int=3, rows:int=3, margin_px:int=60, gutter_px:int=18, card_w:int=744, card_h:int=1039, add_crop: bool=False):
    inkscape = find_inkscape()
    if not inkscape:
        raise EnvironmentError("Inkscape not found. Please install Inkscape and ensure it's in PATH.")
    sheet_w, sheet_h = a4_dimensions(dpi, orientation)
    positions = layout_positions(sheet_w, sheet_h, card_w, card_h, cols, rows, margin_px, gutter_px)
    per_page = cols*rows
    pages = []
    import tempfile
    tmpdir = Path(tempfile.mkdtemp(prefix="cards_ras_"))
    try:
        pngs = []
        for i, svg in enumerate(svg_paths, 1):
            png = tmpdir / f"card_{i:04d}.png"
            rasterize_svg(inkscape, svg, png, card_w, card_h, dpi)
            pngs.append(png)
        for i in range(0, len(pngs), per_page):
            page = Image.new("RGB", (sheet_w, sheet_h), (255,255,255))
            draw = ImageDraw.Draw(page)
            chunk = pngs[i:i+per_page]
            for png, (x,y) in zip(chunk, positions):
                img = Image.open(png).convert("RGB")
                page.paste(img, (x,y))
                if add_crop:
                    draw_crop_marks(draw, x, y, card_w, card_h, len_px=28, offset=8)
            pages.append(page)
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        if len(pages) == 1:
            pages[0].save(out_pdf, "PDF", resolution=dpi)
        else:
            pages[0].save(out_pdf, "PDF", resolution=dpi, save_all=True, append_images=pages[1:])
    finally:
        pass

def parse_adds(add_list):
    out = []
    for item in add_list:
        if "=" not in item:
            raise ValueError(f"--add expects 'Name=count', got: {item}")
        name, cnt = item.split("=",1)
        cnt = int(cnt)
        if cnt <= 0:
            continue
        out.append((name.strip(), cnt))
    return out

def main():
    ap = argparse.ArgumentParser(description="Collect & Print Sheets for SVG Cards (Magic-size)")
    ap.add_argument("--cards", type=str, default="cards", help="Directory with SVG cards")
    ap.add_argument("--add", action="append", default=[], help="Add 'Name=count' (use base filename without .svg). Can repeat.")
    ap.add_argument("--out", type=str, default="cards_print.pdf", help="Output PDF path")
    ap.add_argument("--dpi", type=int, default=300, help="Sheet DPI (default 300)")
    ap.add_argument("--orientation", choices=["a4portrait","a4landscape"], default="a4portrait", help="Sheet orientation")
    ap.add_argument("--cols", type=int, default=3, help="Columns per page")
    ap.add_argument("--rows", type=int, default=3, help="Rows per page")
    ap.add_argument("--margin", type=int, default=60, help="Outer margin in px (at sheet DPI)")
    ap.add_argument("--gutter", type=int, default=18, help="Gap between cards in px (at sheet DPI)")
    ap.add_argument("--crop", action="store_true", help="Add crop marks around each card")

    args = ap.parse_args()

    cards_dir = Path(args.cards)
    requests = parse_adds(args.add)
    if not requests:
        ap.error("Please add at least one --add 'Name=count'")

    svg_list = collect_files(cards_dir, requests)
    make_sheets(svg_list, Path(args.out), dpi=args.dpi, orientation=args.orientation, cols=args.cols, rows=args.rows, margin_px=args.margin, gutter_px=args.gutter, add_crop=args.crop)
    print(f"Created: {args.out}")

if __name__ == "__main__":
    main()
