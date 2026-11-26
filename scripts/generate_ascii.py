"""Generate real ASCII from Willam's supplied photo, with a reproducible crop.

Only printable ASCII glyphs encode the image. No embedded raster, filters, paths,
or generated facial details. The SVG's rectangle is a uniform background.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
from html import escape
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageFont, ImageOps, ImageDraw

try:
    from .common import ROOT, atomic_write
except ImportError:
    from common import ROOT, atomic_write

RAMP = ' .`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$'
DEFAULT_CROP = (285, 130, 825, 715)


def prepare_photo(image: Image.Image, crop=DEFAULT_CROP) -> np.ndarray:
    image = ImageOps.exif_transpose(image).convert("RGB")
    if not (0 <= crop[0] < crop[2] <= image.width and 0 <= crop[1] < crop[3] <= image.height):
        raise ValueError("Crop must lie inside the original photograph")
    rgb = np.array(image)
    cv2.setRNGSeed(0)
    # Known plain studio background; no facial landmark warping or synthesis.
    mask = np.zeros(rgb.shape[:2], dtype=np.uint8)
    cv2.grabCut(rgb, mask, (155, 120, image.width-260, image.height-121), np.zeros((1,65), np.float64), np.zeros((1,65), np.float64), 6, cv2.GC_INIT_WITH_RECT)
    foreground = np.where((mask == 1) | (mask == 3), 1, 0).astype(np.float32)
    foreground = cv2.GaussianBlur(foreground, (5,5), 0.8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 14, 14)
    local = cv2.createCLAHE(clipLimit=1.35, tileGridSize=(12,12)).apply(gray)
    # Blend local contrast with source luminance to retain expression/skin gradation.
    gray = cv2.addWeighted(gray, 0.45, local, 0.55, 0)
    blurred = cv2.GaussianBlur(gray, (0,0), 0.8)
    gray = cv2.addWeighted(gray, 1.45, blurred, -0.45, 0)
    gray = gray.astype(np.float32) * foreground + 255 * (1-foreground)
    left, top, right, bottom = crop
    return gray[top:bottom, left:right].astype(np.uint8)


def ascii_rows(gray: np.ndarray, columns: int, cell_ratio: float = 0.60) -> list[str]:
    rows = round(gray.shape[0] / gray.shape[1] * columns * cell_ratio)
    reduced = np.array(Image.fromarray(gray).resize((columns, rows), Image.Resampling.LANCZOS)).astype(float)
    # Darkness maps monotonically to glyph density; background stays spaces.
    darkness = np.clip((255-reduced) / 255, 0, 1) ** 0.90
    # Calibrate actual ink coverage instead of assuming the glyph order is linear.
    coverage = np.array([glyph_coverage()[c] for c in RAMP])
    indexes = np.abs(darkness[:,:,None]-coverage[None,None,:]).argmin(axis=2)
    return ["".join(RAMP[i] for i in row) for row in indexes]


@lru_cache(maxsize=1)
def glyph_coverage() -> dict[str, float]:
    font = ImageFont.truetype(font_path(), 40)
    coverage = []
    chars = ''.join(chr(i) for i in range(32,127))
    for char in chars:
        tile = Image.new("L", (24,40), 0)
        ImageDraw.Draw(tile).text((0,-4), char, font=font, fill=255)
        coverage.append(float(np.array(tile).mean()))
    coverage = np.array(coverage)
    coverage /= max(coverage[chars.index(c)] for c in RAMP)
    return dict(zip(chars, coverage))


def portrait_svg(rows: list[str], theme: str = "dark") -> str:
    columns, cell, line, pad = len(rows[0]), 6.6, 11, 24
    width, height = columns*cell+2*pad, len(rows)*line+2*pad
    bg = "#0A1425" if theme == "dark" else "#F8FAFC"
    # A narrow ink palette preserves luminance contrast instead of washing out skin.
    colors = ["#1D4ED8", "#1D4ED8", "#1E40AF", "#172554"]
    if theme == "mono":
        bg, colors = "#FFFFFF", ["#111111"]*4
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height}" viewBox="0 0 {width:.1f} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Willam Huaman - photographic ASCII portrait</title>',
        '<desc id="desc">Printable ASCII sampled from the original portrait: natural hair, eyes, smile, neck and shoulders. Every glyph represents source-image luminance.</desc>',
        f'<rect width="100%" height="100%" rx="24" fill="{bg}"/>',
        *([f'<rect x="12" y="12" width="{width-24:.1f}" height="{height-24}" rx="16" fill="#E7F0FF"/>'] if theme == "dark" else []),
        '<g font-family="Consolas,DejaVu Sans Mono,Liberation Mono,monospace" font-size="11" xml:space="preserve">']
    for y, row in enumerate(rows):
        # Each character gets an explicit position: font fallback cannot accumulate drift.
        for x, char in enumerate(row):
            if char == " ":
                continue
            density = glyph_coverage()[char]
            color = colors[min(3, int(density*4))]
            chunks.append(f'<text x="{pad+x*cell:.1f}" y="{pad+9+y*line}" fill="{color}">{escape(char)}</text>')
    return "\n".join(chunks) + "\n</g></svg>\n"


def font_path():
    for path in ["C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]:
        if Path(path).exists():
            return path
    raise FileNotFoundError("A monospace font is required for the comparison sheet")


def render_ascii(rows: list[str], width: int = 540) -> Image.Image:
    font = ImageFont.truetype(font_path(), 14)
    cell, line = font.getlength("M"), 14
    result = Image.new("RGB", (round(len(rows[0])*cell+32), len(rows)*line+32), "white")
    draw = ImageDraw.Draw(result)
    for y, row in enumerate(rows):
        draw.text((16, 12+y*line), row, font=font, fill="#111111")
    return result.resize((width, round(result.height*width/result.width)), Image.Resampling.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="The original, unmodified photograph")
    parser.add_argument("--output", type=Path, default=ROOT / "assets/ascii")
    parser.add_argument("--columns", type=int, default=160, choices=[80,120,160])
    parser.add_argument("--crop", type=int, nargs=4, default=DEFAULT_CROP, metavar=("LEFT","TOP","RIGHT","BOTTOM"))
    args = parser.parse_args()
    original = ImageOps.exif_transpose(Image.open(args.source)).convert("RGB")
    gray = prepare_photo(original, args.crop)
    args.output.mkdir(parents=True, exist_ok=True)
    variants = {}
    for columns in (80,120,160):
        rows = ascii_rows(gray, columns)
        variants[columns] = rows
        atomic_write(args.output / f"portrait-{columns}.txt", "\n".join(rows) + "\n")
        for theme in ("light", "dark", "mono"):
            atomic_write(args.output / f"portrait-{columns}-{theme}.svg", portrait_svg(rows, theme))
    selected = variants[args.columns]
    atomic_write(args.output / "portrait.txt", "\n".join(selected) + "\n")
    for theme in ("light", "dark", "mono"):
        atomic_write(args.output / f"portrait-{theme}.svg", portrait_svg(selected, theme))
    # Comparison is a review artifact, never embedded into the profile SVG.
    photos = [original.crop(args.crop).resize((540,585))] + [render_ascii(variants[c]) for c in variants]
    sheet = Image.new("RGB", (4*564, 690), "#E2E8F0")
    draw = ImageDraw.Draw(sheet)
    for i, (label, picture) in enumerate(zip(["Original crop", "80 columns", "120 columns", "160 columns"], photos)):
        draw.text((i*564+12,14), label, font=ImageFont.truetype(font_path(),22), fill="#0F172A")
        sheet.paste(picture, (i*564+12,60))
    review = ROOT / "preview"
    review.mkdir(exist_ok=True)
    sheet.save(review / "ascii-comparison.png")
    atomic_write(args.output / "parameters.json", json.dumps({"source": "perfil.jpg (user supplied; not committed)", "crop": list(args.crop), "selected_columns": args.columns, "cell_width": 6.6, "line_height": 11, "background": "OpenCV GrabCut; no generative reconstruction", "ramp": RAMP}, indent=2) + "\n")
    print(f"Generated 80, 120, 160 column variants; selected {args.columns}. Comparison: {review / 'ascii-comparison.png'}")


if __name__ == "__main__":
    main()
