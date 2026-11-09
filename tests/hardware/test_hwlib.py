"""Unit tests for the host-side helpers of the hardware-live test."""
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hwlib  # noqa: E402


def wav_bytes(samples, rate=44100, channels=2, sizes_ok=True):
    data = b"".join(struct.pack("<h", s) * channels for s in samples)
    n = len(data) if sizes_ok else 0          # QEMU fills the sizes in only at exit
    fmt = struct.pack("<HHIIHH", 1, channels, rate, rate * channels * 2, channels * 2, 16)
    return (b"RIFF" + struct.pack("<I", 36 + n) + b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
            + b"data" + struct.pack("<I", n) + data)


def tone(freq, seconds, rate=44100, amp=0.5):
    return [int(amp * 32767 * math.sin(2 * math.pi * freq * i / rate)) for i in range(int(seconds * rate))]


def test_silence_is_silent(tmp_path):
    f = tmp_path / "s.wav"
    f.write_bytes(wav_bytes([0] * 44100))
    st = hwlib.wav_stats(f, 1000)
    assert st["silent"]
    assert st["seconds"] == 1.0


def test_tone_is_found_even_with_unfinished_header(tmp_path):
    f = tmp_path / "t.wav"
    f.write_bytes(wav_bytes([0] * 22050 + tone(1000, 1.0) + [0] * 22050, sizes_ok=False))
    st = hwlib.wav_stats(f, 1000)
    assert not st["silent"]
    assert st["tone_share"] > 0.8          # most of the loud part's energy is at 1 kHz
    assert 0.9 < st["loud_seconds"] < 1.1
    assert st["peak_dbfs"] > -10


def test_noise_is_not_the_tone(tmp_path):
    import random
    rnd = random.Random(1)
    f = tmp_path / "n.wav"
    f.write_bytes(wav_bytes([rnd.randint(-12000, 12000) for _ in range(44100)]))
    st = hwlib.wav_stats(f, 1000)
    assert not st["silent"]
    assert st["tone_share"] < 0.2


def test_missing_or_empty_file(tmp_path):
    assert hwlib.wav_stats(tmp_path / "nope.wav", 1000)["silent"]
    (tmp_path / "e.wav").write_bytes(b"")
    assert hwlib.wav_stats(tmp_path / "e.wav", 1000)["silent"]


def frame(w, h, bg=(230, 235, 245)):
    return hwlib.Frame(w, h, bytearray(bytes(bg) * (w * h)))


def paint(f, x0, y0, x1, y1, rgb=(40, 40, 50)):
    for y in range(y0, y1):
        for x in range(x0, x1):
            o = (y * f.w + x) * 3
            f.pix[o:o + 3] = bytes(rgb)


def test_tray_icons_left_to_right():
    f = frame(400, 80)
    paint(f, 100, 30, 116, 46)              # icon 1
    paint(f, 104, 50, 112, 52)              # its own small detail, same column range
    paint(f, 140, 30, 156, 46)              # icon 2
    paint(f, 180, 34, 186, 40)              # the small expander arrow
    paint(f, 300, 20, 360, 60)              # outside the band: the clock
    icons = hwlib.tray_icons(f, x0=50, x1=250, y0=20, y1=60)
    assert [round(x) for x, _ in icons] == [108, 148, 183]
    assert all(20 <= y < 60 for _, y in icons)


def test_tray_icons_ignore_a_soft_gradient():
    f = frame(300, 60)
    for x in range(300):                    # panel gradient: +20 over the width
        paint(f, x, 0, x + 1, 60, (220 + x // 15, 225, 235))
    paint(f, 50, 20, 66, 36)
    assert [round(x) for x, _ in hwlib.tray_icons(f, 0, 300, 0, 60)] == [58]


def test_tray_icons_finds_a_faint_icon():
    # Plasma draws an idle Bluetooth icon in light grey on the light panel.
    f = frame(300, 60, bg=(240, 240, 247))
    paint(f, 40, 20, 56, 36, (212, 212, 220))
    paint(f, 100, 20, 116, 36)
    assert [round(x) for x, _ in hwlib.tray_icons(f, 0, 300, 0, 60)] == [48, 108]
