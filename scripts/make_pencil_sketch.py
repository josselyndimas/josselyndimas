#!/usr/bin/env python3
"""One-off helper: turns a portrait photo into a pencil-sketch PNG for the hero card.

    python scripts/make_pencil_sketch.py path/to/photo.png

Writes assets/portrait-pencil-light.png and assets/portrait-pencil-dark.png (transparent background).
The hero card (scripts/render_cards.py) just embeds those two files, so after replacing them you only
need to commit and push. Needs: pip install pillow numpy scipy
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets" / "josselyn-photo.png"
CROP = (0.12, 0.04, 0.86, 0.70)   # left, top, right, bottom (fractions): head, shoulders and part of the arms
SOFT = 0.62                        # pencil pressure: lower = lighter strokes
OUT_W = 560

im = Image.open(SRC).convert("RGB")
L = np.array(im.convert("L"), dtype=float)
h, w = L.shape

H0 = h
# 1) cut the plain studio background out: fit a smooth background plane from the borders
yy, xx = np.mgrid[0:h, 0:w]
edge = (xx < w * 0.11) | (xx > w * 0.92) | (yy < h * 0.06)
A = np.stack([np.ones(h * w), xx.ravel() / w, yy.ravel() / h, (xx.ravel() / w) ** 2,
              (yy.ravel() / h) ** 2, (xx.ravel() * yy.ravel()) / (w * h)], 1)
coef, *_ = np.linalg.lstsq(A[edge.ravel()], L.ravel()[edge.ravel()], rcond=None)
bg = (A @ coef).reshape(h, w)
mask = np.abs(ndi.gaussian_filter(L, 1.5) - bg) > 16
mask = ndi.binary_fill_holes(ndi.binary_opening(ndi.binary_closing(mask, iterations=6), iterations=3))
lab, n = ndi.label(mask)
if n > 1:
    mask = lab == (1 + int(np.argmax(ndi.sum(mask, lab, range(1, n + 1)))))
soft = ndi.gaussian_filter(mask.astype(float), 3)

# 2) pencil sketch: colour-dodge against the blurred negative keeps only the lines; the real tone is mixed
#    back lightly so hair and suit get graphite shading
blur = ndi.gaussian_filter(255 - L, 4)
sketch = np.clip(L * 255.0 / (255.0 - blur + 1.0), 0, 255)
sketch = 255 * (sketch / 255) ** 2.2                      # darker, crisper strokes
shade = 0.35 * (255 - L) * (L < 110)                      # graphite in the dark areas only
ink = np.clip((255 - sketch) * 1.1 + shade, 0, 255) / 255 # 0 = paper, 1 = full graphite
alpha_f = ink * soft * SOFT
# fade the drawing out at the bottom edge so it dissolves into the card instead of ending in a hard cut
fade = np.clip((H0 * CROP[3] - yy) / (H0 * 0.10), 0, 1)
alpha = (alpha_f * fade * 255).astype(np.uint8)

W, H = im.size
box = (int(W * CROP[0]), int(H * CROP[1]), int(W * CROP[2]), int(H * CROP[3]))
for name, color in (("light", (0x6B, 0x52, 0x40)), ("dark", (0xD3, 0xB9, 0x9B))):
    rgba = Image.new("RGBA", (W, H), color + (0,))
    rgba.putalpha(Image.fromarray(alpha))
    rgba = rgba.crop(box)
    rgba = rgba.resize((OUT_W, round(rgba.height * OUT_W / rgba.width)), Image.LANCZOS)
    rgba = rgba.quantize(colors=48, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    rgba.save(ROOT / "assets" / f"portrait-pencil-{name}.png", optimize=True)
print("portraits written", rgba.size)
