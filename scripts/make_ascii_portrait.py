#!/usr/bin/env python3
"""One-off helper: turns assets/josselyn-pixel-static.png into assets/portrait-ascii.txt
(pencil-style text portrait used by the hero card). Needs Pillow: pip install pillow"""
import sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 120
RAMP = "@@@#%S?*+=;:,. "  # dark -> light (few glyphs = strong contrast)

im = Image.open(ROOT / "assets" / "josselyn-pixel-static.png").convert("RGBA")
im = im.crop(im.getbbox())
im = im.crop((int(im.width * 0.21), 0, int(im.width * 0.79), int(im.height * 0.66)))  # head and shoulders
alpha = im.split()[3]
rows = round(COLS * im.height / im.width * 0.5)  # characters are ~2x taller than wide
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
bg.alpha_composite(im)
g = ImageOps.autocontrast(bg.convert("L"), cutoff=2)
g = ImageOps.autocontrast(g, cutoff=1)
g = g.resize((COLS, rows), Image.LANCZOS)
a = alpha.resize((COLS, rows), Image.LANCZOS)
lines = []
for y in range(rows):
    row = ""
    for x in range(COLS):
        if a.getpixel((x, y)) < 40:
            row += " "
        else:
            v = g.getpixel((x, y)) / 255
            v = min(1, max(0, v)) ** 0.8
            row += RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))]
    lines.append(row.rstrip())
(ROOT / "assets" / "portrait-ascii.txt").write_text("\n".join(lines) + "\n", encoding="utf8")
print(COLS, "x", rows)

# ---- also bake the text into transparent PNGs (browsers render tiny SVG text at inconsistent widths,
# an image keeps the portrait exactly as drawn). Needs a monospace TTF (DejaVu Sans Mono).
from PIL import ImageDraw, ImageFont
FONT = next((p for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                         "/Library/Fonts/Courier New Bold.ttf", "C:/Windows/Fonts/courbd.ttf"] if Path(p).exists()), None)
if FONT:
    CW, LH, FS = 7.2, 14.4, 12
    font = ImageFont.truetype(FONT, FS)
    for name, color in (("light", (0x49, 0x38, 0x2D)), ("dark", (0xD3, 0xB9, 0x9B))):
        canvas = Image.new("RGBA", (round(COLS * CW), round(len(lines) * LH)), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        for j, row in enumerate(lines):
            d.text((0, j * LH), row, font=font, fill=color + (255,))
        w = 440
        canvas = canvas.resize((w, round(canvas.height * w / canvas.width)), Image.LANCZOS)
        canvas = canvas.quantize(colors=24, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        canvas.save(ROOT / "assets" / f"portrait-pencil-{name}.png", optimize=True)
    print("png portraits written")
else:
    print("No monospace font found; PNG portraits not regenerated")
