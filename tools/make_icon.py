# -*- coding: utf-8 -*-
"""Draws the app icon (blue rounded square with a heartbeat line) into assets/icon.ico. Needs Pillow."""

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "icon.ico")


def draw(size):
    s = size * 4  # draw large, then downscale for smooth edges
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(s * 0.22)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=(37, 99, 235, 255))
    # a faint screen shape
    d.rounded_rectangle([s * 0.16, s * 0.2, s * 0.84, s * 0.66], radius=int(s * 0.05), fill=(255, 255, 255, 60))
    d.rectangle([s * 0.1, s * 0.74, s * 0.9, s * 0.8], fill=(255, 255, 255, 60))
    # heartbeat line
    pts = [(0.2, 0.45), (0.35, 0.45), (0.43, 0.28), (0.55, 0.6), (0.63, 0.4), (0.8, 0.45)]
    d.line([(x * s, y * s) for x, y in pts], fill=(255, 255, 255, 255), width=max(2, int(s * 0.07)), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    big = draw(256)
    big.save(OUT, sizes=[(n, n) for n in sizes], append_images=[draw(n) for n in sizes[:-1]])
    big.save(os.path.join(ROOT, "assets", "icon.png"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
