#!/usr/bin/python3
"""Render the default Lucent wallpaper (light + dark) as PNG at build time.

A soft diagonal gradient with two blurred "light" blobs, ordered-dithered to
avoid banding. Pure stdlib so the image needs no extra packages and the repo
needs no binary blobs.
"""
import math
import struct
import sys
import zlib
from pathlib import Path

W, H = 2560, 1440
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

THEMES = {
    "images": dict(a=(226, 234, 250), b=(244, 238, 250), blobs=[((0.78, 0.30), 0.45, (190, 212, 255)), ((0.18, 0.85), 0.40, (232, 214, 250))]),
    "images_dark": dict(a=(16, 20, 34), b=(30, 22, 44), blobs=[((0.78, 0.30), 0.45, (34, 62, 128)), ((0.18, 0.85), 0.40, (70, 40, 96))]),
}


def lerp(a, b, t):
    return a + (b - a) * t


def render(theme):
    rows = []
    for y in range(H):
        row = bytearray(b"\x00")  # PNG filter type 0
        fy = y / H
        for x in range(0, W):
            fx = x / W
            t = (fx + fy) / 2
            px = [lerp(theme["a"][i], theme["b"][i], t) for i in range(3)]
            for (cx, cy), radius, col in theme["blobs"]:
                d = math.hypot((fx - cx) * W / H, fy - cy) / radius
                k = max(0.0, 1 - d) ** 2 * 0.8
                px = [lerp(px[i], col[i], k) for i in range(3)]
            dither = (BAYER[y & 3][x & 3] / 16) - 0.5
            row += bytes(min(255, max(0, int(v + dither + 0.5))) for v in px)
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


def main(dest):
    for folder, theme in THEMES.items():
        out = Path(dest) / folder
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{W}x{H}.png").write_bytes(render(theme))


if __name__ == "__main__":
    main(sys.argv[1])
