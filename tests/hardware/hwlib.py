"""Host-side helpers of the hardware-live test (tests/hardware/hwlive.py):
what came out of the virtual sound card, and where the tray icons are."""
import math
import struct
import sys
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "acceptance"))
from harness import Frame  # noqa: E402,F401  (tests/acceptance/harness.py)

SILENT_DBFS = -50.0


def _wav_format(data):
    """(channels, rate, bits, offset of the samples) of a RIFF/WAVE file."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a WAVE file")
    pos, fmt = 12, None
    while pos + 8 <= len(data):
        kind, size = data[pos:pos + 4], struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if kind == b"fmt ":
            _, ch, rate, _, _, bits = struct.unpack("<HHIIHH", data[pos + 8:pos + 24])
            fmt = (ch, rate, bits)
        elif kind == b"data":
            if fmt is None:
                raise ValueError("data before fmt")
            return (*fmt, pos + 8)
        pos += 8 + size + (size & 1)
    raise ValueError("no data chunk")


def wav_stats(path, freq, start=None, end=None, window_s=0.1):
    """Loudness of a 16-bit PCM WAV that QEMU's `wav` audiodev wrote (its
    header sizes are only filled in when QEMU exits, so the samples run to
    the end of the file). `start`/`end`: byte offsets into the file, to look
    only at what was written while the guest played. Returns seconds, peak
    and RMS in dBFS, whether it is silent (no 100 ms window above -50 dBFS),
    how long it was loud and which share of the loud part's energy is at
    `freq` (1.0 for a pure tone)."""
    out = {"seconds": 0.0, "peak_dbfs": -120.0, "rms_dbfs": -120.0, "silent": True,
           "loud_seconds": 0.0, "tone_share": 0.0}
    try:
        data = Path(path).read_bytes()
        ch, rate, bits, off = _wav_format(data)
    except (OSError, ValueError, struct.error):
        return out
    if bits != 16:
        raise ValueError(f"{bits}-bit WAV not supported")
    frame_bytes = 2 * ch
    lo = max(off, start if start is not None else off)
    lo = off + (lo - off) // frame_bytes * frame_bytes
    hi = len(data) if end is None else min(end, len(data))
    hi = lo + (hi - lo) // frame_bytes * frame_bytes
    pcm = array("h")
    pcm.frombytes(data[lo:hi])
    if sys.byteorder != "little":
        pcm.byteswap()
    mono = pcm if ch == 1 else array("h", (sum(pcm[i:i + ch]) // ch for i in range(0, len(pcm), ch)))
    n = len(mono)
    out["seconds"] = round(n / rate, 3)
    if not n:
        return out
    full = 32768.0
    peak = max(abs(min(mono)), abs(max(mono)))
    total = sum(x * x for x in mono)
    out["peak_dbfs"] = round(20 * math.log10(max(peak, 1) / full), 1)
    out["rms_dbfs"] = round(10 * math.log10(max(total / n, 1e-12) / full ** 2), 1)
    win = max(1, int(rate * window_s))
    coeff = 2 * math.cos(2 * math.pi * freq / rate)
    loud = 0
    shares = []
    for i in range(0, n - win + 1, win):
        w = mono[i:i + win]
        e = sum(x * x for x in w)
        if 10 * math.log10(max(e / win, 1e-12) / full ** 2) < SILENT_DBFS:
            continue
        loud += 1
        s1 = s2 = 0.0           # Goertzel
        for x in w:
            s1, s2 = x + coeff * s1 - s2, s1
        power = s1 * s1 + s2 * s2 - coeff * s1 * s2
        shares.append(min(1.0, 2 * power / (win * e)))
    out["loud_seconds"] = round(loud * win / rate, 2)
    out["silent"] = loud == 0
    if shares:
        out["tone_share"] = round(sum(shares) / len(shares), 3)
    return out


def tray_icons(f, x0, x1, y0, y1, level=60, gap=3):
    """Centres (x, y) of the icons in a strip of the screen (the panel's
    system tray), left to right: runs of columns that hold pixels standing
    out from that column's own background (its median colour)."""
    cols = []
    for x in range(x0, x1):
        px = [f.pix[(y * f.w + x) * 3:(y * f.w + x) * 3 + 3] for y in range(y0, y1)]
        lum = [(299 * p[0] + 587 * p[1] + 114 * p[2]) // 1000 for p in px]
        med = sorted(lum)[len(lum) // 2]
        ink = [y0 + i for i, v in enumerate(lum) if abs(v - med) > level]
        cols.append((x, ink) if len(ink) >= 2 else None)
    icons = []
    run = []
    empty = 0
    for c in cols:
        if c:
            run.append(c)
            empty = 0
        elif run:
            empty += 1
            if empty > gap:
                icons.append(run)
                run, empty = [], 0
    if run:
        icons.append(run)
    centres = []
    for r in icons:
        xs = [c[0] for c in r]
        ys = [y for c in r for y in c[1]]
        centres.append(((xs[0] + xs[-1] + 1) / 2, sum(ys) / len(ys)))
    return centres
