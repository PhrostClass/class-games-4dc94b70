"""Enlarge part of a low-resolution page screenshot so small print can be read.
usage: python prep_crop.py "<image path>" <col> <row> [rows=3]
  col: 0 = left column, 1 = right column ; row: 0..rows-1 from the top
Writes tools/prepare_crops/<name>_c<col>_r<row>.png (4x upscaled, slightly overlapping) and prints its path.
"""
import sys, os
from PIL import Image, ImageEnhance

src, col, row = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rows = int(sys.argv[4]) if len(sys.argv) > 4 else 3
im = Image.open(src).convert('RGB')
w, h = im.size
x0, x1 = (0, w // 2 + 12) if col == 0 else (w // 2 - 12, w)
step = h / rows
y0, y1 = max(0, int(row * step) - 14), min(h, int((row + 1) * step) + 14)
crop = im.crop((x0, y0, x1, y1))
crop = crop.resize((crop.width * 4, crop.height * 4), Image.LANCZOS)
crop = ImageEnhance.Sharpness(crop).enhance(1.6)
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prepare_crops')
os.makedirs(out_dir, exist_ok=True)
name = os.path.splitext(os.path.basename(src))[0].replace(' ', '_')
lvl = os.path.basename(os.path.dirname(os.path.dirname(src))).replace(' ', '')
out = os.path.join(out_dir, f'{lvl}_{name}_c{col}_r{row}.png')
crop.save(out)
print(out)
