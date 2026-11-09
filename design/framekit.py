"""Shared helpers for the Lucent theme generators.

Frames (panel, popups, task-manager states, window decoration) are drawn as
signed-distance fields of rounded rectangles, rasterised with supersampling at
2x and embedded into SVG as PNG <image> elements. Plasma (KSvg) and Aurorae
slice SVGs by element id, so every 9-slice part is its own element. Raster
slices keep radii, hairlines and soft shadows exactly as specified in
docs/mockups/lucent.css; at 1x they are pixel-exact and at 2x still crisp.
"""
import base64
import io
import math

import numpy as np
from PIL import Image

SCALE = 2      # embedded pixel density
SS = 4         # supersampling factor for edges


def rgba(css):
    """'rgba(10,15,30,.22)' / '#rrggbb' -> (r,g,b,a) floats 0..1."""
    css = css.strip()
    if css.startswith("#"):
        h = css[1:]
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)
    parts = css[css.index("(") + 1:-1].split(",")
    r, g, b = (float(p) / 255 for p in parts[:3])
    a = float(parts[3]) if len(parts) > 3 else 1.0
    return (r, g, b, a)


def sdf_roundrect(w, h, x0, y0, bw, bh, r, scale, ss=1):
    """Signed distance (in logical px) to a rounded rect, sampled on a
    (h*scale*ss, w*scale*ss) grid covering logical [0,w)x[0,h)."""
    n = scale * ss
    ys = (np.arange(h * n) + 0.5) / n
    xs = (np.arange(w * n) + 0.5) / n
    X, Y = np.meshgrid(xs, ys)
    cx, cy = x0 + bw / 2, y0 + bh / 2
    qx = np.abs(X - cx) - (bw / 2 - r)
    qy = np.abs(Y - cy) - (bh / 2 - r)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
    inside = np.minimum(np.maximum(qx, qy), 0)
    return outside + inside - r


def coverage(d):
    """Area coverage from a supersampled SDF: 1 inside, 0 outside."""
    return (d <= 0).astype(np.float32)


def downsample(a, ss):
    if ss == 1:
        return a
    h, w = a.shape[0] // ss, a.shape[1] // ss
    return a.reshape(h, ss, w, ss, *a.shape[2:]).mean(axis=(1, 3))


def over(dst, color, alpha):
    """Composite a flat colour with per-pixel alpha over a premultiplied RGBA image."""
    r, g, b, a = color
    k = (alpha * a)[..., None]
    src = np.concatenate([np.full(alpha.shape + (3,), (r, g, b)) * k, k], axis=-1)
    return src + dst * (1 - k)


def unpremultiply(img):
    out = img.copy()
    a = img[..., 3:4]
    nz = a[..., 0] > 1e-6
    out[nz, :3] = img[nz, :3] / a[nz]
    return out


def png_data(img):
    """premultiplied float RGBA -> data URI"""
    u = unpremultiply(img)
    arr = np.clip(u * 255 + 0.5, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def render_box(w, h, box, r, fill=None, border=None, border_w=1.0, ring=None,
               shadows=(), cut_inside_shadow=True, extra=None):
    """Render a logical w x h canvas (premultiplied RGBA at SCALE) holding a
    rounded rect `box`=(x,y,bw,bh) with radius r.

    fill   : css colour inside
    border : css colour of an inner hairline (inside the edge)
    ring   : css colour of a 1px ring just outside the edge
    shadows: [(css colour, blur_px (CSS blur radius), dx, dy, spread)]
    extra  : callable(img, X, Y) for custom drawing (logical coords)
    """
    x0, y0, bw, bh = box
    img = np.zeros((h * SCALE, w * SCALE, 4), np.float32)
    d_lo = sdf_roundrect(w, h, x0, y0, bw, bh, r, SCALE)  # pixel-centre SDF
    for col, blur, dx, dy, spread in shadows:
        sigma = max(blur / 2.0, 0.01)
        ds = sdf_roundrect(w, h, x0 + dx - spread, y0 + dy - spread, bw + 2 * spread,
                           bh + 2 * spread, r + spread, SCALE)
        a = 0.5 * (1 - _erf(ds / (sigma * math.sqrt(2))))
        if cut_inside_shadow:
            a = a * np.clip(d_lo * SCALE + 0.5, 0, 1)
        img = over(img, rgba(col), a.astype(np.float32))
    d = sdf_roundrect(w, h, x0, y0, bw, bh, r, SCALE, SS)
    inside = downsample(coverage(d), SS)
    if ring:
        dr = sdf_roundrect(w, h, x0 - 1, y0 - 1, bw + 2, bh + 2, r + 1, SCALE, SS)
        ring_a = downsample(coverage(dr), SS) - inside
        img = over(img, rgba(ring), np.clip(ring_a, 0, 1))
    if fill:
        img = over(img, rgba(fill), inside)
    if border:
        di = sdf_roundrect(w, h, x0 + border_w, y0 + border_w, bw - 2 * border_w,
                           bh - 2 * border_w, max(r - border_w, 0), SCALE, SS)
        inner = downsample(coverage(di), SS)
        img = over(img, rgba(border), np.clip(inside - inner, 0, 1))
    if extra:
        img = extra(img)
    return img


def _erf(x):
    # Abramowitz-Stegun 7.1.26, vectorised; max error 1.5e-7
    s = np.sign(x)
    x = np.abs(x)
    t = 1 / (1 + 0.3275911 * x)
    y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-x * x)
    return s * y


def crop(img, x, y, w, h):
    return img[y * SCALE:(y + h) * SCALE, x * SCALE:(x + w) * SCALE]


class SvgDoc:
    """Collects id'd elements and writes a KSvg/Aurorae-compatible SVG."""

    def __init__(self, width, height):
        self.w, self.h = width, height
        self.items = []

    def image(self, eid, x, y, img):
        h, w = img.shape[0] // SCALE, img.shape[1] // SCALE
        self.items.append(f'<image id="{eid}" x="{x}" y="{y}" width="{w}" height="{h}" '
                          f'preserveAspectRatio="none" xlink:href="{png_data(img)}"/>')

    def rect(self, eid, x, y, w, h, fill="#000", opacity=0.0):
        self.items.append(f'<rect id="{eid}" x="{x}" y="{y}" width="{w}" height="{h}" '
                          f'style="fill:{fill};fill-opacity:{opacity};stroke:none"/>')

    def group(self, eid, x, y, img, overlay=""):
        """A raster piece plus vector `overlay` (in the piece's own coordinates)
        under one id. Vector parts may use class="ColorScheme-Highlight" with
        fill:currentColor: Plasma recolours those to the current accent."""
        h, w = img.shape[0] // SCALE, img.shape[1] // SCALE
        self.items.append(f'<g id="{eid}" transform="translate({x},{y})">'
                          f'<image x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="none" '
                          f'xlink:href="{png_data(img)}"/>{overlay}</g>')

    def raw(self, s):
        self.items.append(s)

    # KSvg/Plasma replace this style sheet with the current colour scheme.
    COLOR_SCHEME_STYLE = ('<style type="text/css" id="current-color-scheme">'
                          '.ColorScheme-Highlight { color:#3daee9; } .ColorScheme-Text { color:#232629; }</style>')

    def svg(self):
        body = "\n".join(self.items)
        style = self.COLOR_SCHEME_STYLE + "\n" if "ColorScheme-" in body else ""
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" version="1.1">\n'
                + style + body + "\n</svg>\n")


class Cursor:
    """Places elements left-to-right in rows so ids never overlap."""

    def __init__(self):
        self.x = self.y = self.row_h = 0
        self.max_w = 0

    def place(self, w, h, gap=4):
        if self.x + w > 2400:
            self.x = 0
            self.y += self.row_h + gap
            self.row_h = 0
        pos = (self.x, self.y)
        self.x += w + gap
        self.row_h = max(self.row_h, h)
        self.max_w = max(self.max_w, self.x)
        return pos

    @property
    def height(self):
        return self.y + self.row_h


def nine_slice(doc, cur, prefix, img, cw_l, ch_t, cw_r, ch_b, mask=None, overlays=None):
    """Cut `img` (logical size W x H) into 9 elements with the given corner
    sizes and add them to `doc`; optional mask image gets mask-* ids.
    overlays: {"bottom": svg, ...} vector parts added to a piece, given in
    the coordinates of the whole W x H image."""
    H, W = img.shape[0] // SCALE, img.shape[1] // SCALE
    cols = [(0, cw_l), (cw_l, W - cw_l - cw_r), (W - cw_r, cw_r)]
    rows = [(0, ch_t), (ch_t, H - ch_t - ch_b), (H - ch_b, ch_b)]
    names = [["topleft", "top", "topright"], ["left", "center", "right"],
             ["bottomleft", "bottom", "bottomright"]]
    p = f"{prefix}-" if prefix else ""
    for src, pre in ((img, p), (mask, "mask-" if not prefix else f"mask-{prefix}-")):
        if src is None:
            continue
        x, y = cur.place(W, H, gap=8)
        for ri, (ry, rh) in enumerate(rows):
            for ci, (cx, cw) in enumerate(cols):
                if rw_zero(cw, rh):
                    continue
                piece = crop(src, cx, ry, cw, rh)
                extra = (overlays or {}).get(names[ri][ci]) if src is img else None
                if extra:
                    doc.group(pre + names[ri][ci], x + cx, y + ry, piece,
                              f'<g transform="translate({-cx},{-ry})">{extra}</g>')
                else:
                    doc.image(pre + names[ri][ci], x + cx, y + ry, piece)


def rw_zero(w, h):
    return w <= 0 or h <= 0


def hints(doc, cur, prefix, margins, kind="margin"):
    """margins = (left, top, right, bottom) -> hint-*-margin rects."""
    p = f"{prefix}-" if prefix else ""
    x, y = cur.place(60, 60, gap=8)
    l, t, r, b = margins
    doc.rect(f"{p}hint-left-{kind}", x, y + 20, l, 2) if l else doc.rect(f"{p}hint-left-{kind}", x, y + 20, 0.001, 2)
    doc.rect(f"{p}hint-top-{kind}", x + 20, y, 2, t) if t else doc.rect(f"{p}hint-top-{kind}", x + 20, y, 2, 0.001)
    doc.rect(f"{p}hint-right-{kind}", x + 40, y + 20, r, 2) if r else doc.rect(f"{p}hint-right-{kind}", x + 40, y + 20, 0.001, 2)
    doc.rect(f"{p}hint-bottom-{kind}", x + 20, y + 40, 2, b) if b else doc.rect(f"{p}hint-bottom-{kind}", x + 20, y + 40, 2, 0.001)
