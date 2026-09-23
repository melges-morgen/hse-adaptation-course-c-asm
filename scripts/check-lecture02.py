"""Independent numerical checks for the examples in lecture/seminar 02."""
from fractions import Fraction
from pathlib import Path
import re
import struct


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def word(x):
    return struct.pack(">f", x).hex().upper()


def flags(a, b, subtract=False):
    result = (a - b if subtract else a + b) & 255
    carry = a < b if subtract else a + b > 255
    sa, sb = a - 256 if a & 128 else a, b - 256 if b & 128 else b
    exact = sa - sb if subtract else sa + sb
    return result, (int(carry), int(not -128 <= exact <= 127),
                    int(result == 0), int(bool(result & 128)))


def check_pixel_a(path):
    html = Path(path).read_text(encoding="utf-8")
    svg = re.search(r'<svg[^>]+aria-label="[^"]*буква A[^"]*".*?</svg>', html, re.S | re.I)
    assert svg, f"pixel A SVG not found in {path}"
    assert '<path' not in svg.group(0), f"pixel A must be cell-based, not path-based: {path}"
    assert svg.group(0).count('class="pixel-on"') >= 14, f"pixel A has too few filled cells: {path}"
    pixels = [(int(x), int(y)) for x, y in re.findall(r'class="pixel-on" x="(\d+)" y="(\d+)"', svg.group(0))]
    xs, ys = zip(*pixels)
    assert min(xs) >= 80 and max(xs) <= 240, f"pixel A needs one-cell horizontal margin: {path}"
    assert min(ys) >= 50 and max(ys) <= 210, f"pixel A needs one-cell vertical margin: {path}"


def check_original_presentation(path):
    html = Path(path).read_text(encoding="utf-8")
    assert "Структура PPTX" not in html, "lecture02-original must not expose the PPTX source label"
    assert "RGB + бит интенсивности — один из исторических вариантов." in html
    assert "RGB + бит интенсивности — один из исторических вариантов, а не общее правило." not in html
    balanced_slides = {5, 7, 8, 10, 11, 14, 17, 18, 20, 22, 26, 27, 30,
                       32, 33, 35, 36, 41, 57, 59, 60}
    for number, body in re.findall(r'<section\b([^>]*)>(.*?)</section>', html, re.S):
        source = re.search(r'data-source-slide="(\d+)"', number)
        if not source or int(source.group(1)) not in balanced_slides:
            continue
        equal = re.search(r'<div class="cols equal">(.*?)</div>\s*(?:<p|<aside|$)', body, re.S)
        assert equal, f"balanced slide {source.group(1)} lost its comparison layout"
        assert equal.group(1).count('class="panel"') == 0, (
            f"balanced slide {source.group(1)} has an unjustified panel"
        )


assert 640 * 480 * 3 == 921600 == 900 * 1024
assert 320 * 200 * 3 == 192000
assert 320 * 200 * 4 // 8 + 16 * 3 == 32048
assert 48000 * 16 * 2 * 10 // 8 == 1920000
assert 48000 * 16 * 2 * 5 // 8 == 960000
assert 44100 * 16 * 3 // 8 == 264600
assert "AЯ".encode("utf-8").hex() == "41d0af"
assert "AЯ".encode("utf-16le").hex() == "41002f04"
assert "AЯ\U0001F600".encode("utf-8").hex() == "41d0aff09f9880"
assert "AЯ\U0001F600".encode("utf-16le").hex() == "41002f043dd800de"
assert (128 | 37, 255 ^ 37, (-37) & 255, -37 + 128) == (165, 218, 219, 91)
assert flags(100, 30) == (130, (0, 1, 0, 1))
assert flags(80, 50, True) == (30, (0, 0, 0, 0))
assert flags(80, 206) == (30, (1, 0, 0, 0))
assert flags(0, 1, True) == (255, (1, 0, 0, 1))
assert flags(127, 1) == (128, (0, 1, 0, 1))
assert flags(255, 1) == (0, (1, 0, 1, 0))
assert (0x5A & 0x3C, 0x5A | 0x3C, 0x5A ^ 0x3C) == (0x18, 0x7E, 0x66)
assert (0x5A | 4, 0x5A & (255 ^ 16), (0x5A >> 2) & 7) == (0x5E, 0x4A, 6)
assert (0xA6 >> 2, (-90 >> 2) & 255) == (0x29, 0xE9)
assert ((0x81 << 1) | (0x81 >> 7)) & 255 == 3
assert (0x5B << 2) & 255 == 0x6C
assert ((3 << 12) | (2 << 9) | (5 << 6)) == 0x3540
assert word(-12.625) == "C14A0000"
assert word(-6.5) == "C0D00000"
assert word(-5) == "C0A00000"
assert word(0.75) == "3F400000"
assert word(23.375) == "41BB0000"
assert word(2**-127) == "00400000"
assert struct.unpack('>f', bytes.fromhex('00400001'))[0] - 2**-127 == 2**-149
assert f32(100000000) == 100000000
assert f32(100000000 + 1) == 100000000
assert int("101111101011110000100000000", 2) == 100000000
assert f32(f32(2**24 + 1) - 2**24) == 0
assert f32(2**24 + f32(1 - 2**24)) == 1
assert round(Fraction(11, 8) * 4) / 4 == 1.5
assert round(Fraction(21, 16) * 4) / 4 == 1.25
assert round(Fraction(73, 64) * 4) / 4 == 1.25
assert round(Fraction(35, 32) * 16) / 16 * 4 == 4.5
check_pixel_a("slides/lecture02/index.html")
check_pixel_a("slides/lecture02-original/index.html")
check_original_presentation("slides/lecture02-original/index.html")

# Examples retained in lecture02-original (PPTX slide numbers in comments).
assert (1 << 4) | 7 == 0b10111  # 19: sign-magnitude −7, n=5
assert 65535 - 22 == 0xFFE9 == 0o177751  # 23–25: one's complement
assert 0o177777 == 2**16 - 1 and 8**5 == 2**15
assert ((5 + (255 ^ 3)) & 255) + ((5 + (255 ^ 3)) >> 8) == 2  # 26: end-around carry
assert 0x1D8 == 0o730 == 472
assert 65535 - 472 == 0xFE27 == 0o177047
assert 65536 - 472 == 0xFE28 == 0o177050  # 28–29
assert (-4) & 31 == 0b11100  # 32–34: two's complement in 5 bits
assert (3 + ((-4) & 31)) & 31 == 31 and 31 - 32 == -1
assert (3 - ((-4) & 31)) & 31 == 7
assert (15 + 1) & 31 == 16 and 16 - 32 == -16  # 35: overflow
assert f32(5.0 + 0.75) == 5.75  # 44–45
assert Fraction(5, 16) + 1 == Fraction(21, 16)  # 46: 1.0101₂
assert Fraction(9, 8) - 1 == Fraction(1, 8)  # 47: exact cancellation
print("Both lecture variants: sizes, Unicode, codes/flags, binary/hex/octal examples, masks, ISA and IEEE 754 — OK")
