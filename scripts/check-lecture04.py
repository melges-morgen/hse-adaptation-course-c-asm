"""Independent exact checks of the lecture's arithmetic, addresses and layouts."""
from fractions import Fraction
import struct


def check(name, actual, expected):
    if actual != expected:
        raise AssertionError(f"{name}: {actual!r} != {expected!r}")
    print(f"OK: {name}")


check("HDD 7200 rpm: revolution in ms", Fraction(60_000, 7200), Fraction(25, 3))
check("mean rotational latency in ms", Fraction(30_000, 7200), Fraction(25, 6))
check("3 GHz: cycle in ns", Fraction(10**9, 3 * 10**9), Fraction(1, 3))
check("100 ns at 3 GHz: cycles", Fraction(100, 10**9) * (3 * 10**9), 300)
check("100 us + 1 MB / 1 GB/s in ms", (Fraction(100, 10**6) + Fraction(10**6, 10**9)) * 1000, Fraction(11, 10))
check("array addresses", [0x1000 + 4 * i for i in range(3)], [0x1000, 0x1004, 0x1008])
check("little-endian bytes", struct.pack("<I", 0x12345678).hex(" "), "78 56 34 12")
check("big-endian bytes", struct.pack(">I", 0x12345678).hex(" "), "12 34 56 78")
check("array before", struct.pack("<3i", 10, 20, 30).hex(" "), "0a 00 00 00 14 00 00 00 1e 00 00 00")
check("array after", struct.pack("<3i", 10, 20 + 5, 30).hex(" "), "0a 00 00 00 19 00 00 00 1e 00 00 00")
check("ints in a cache line", 64 // 4, 16)
check("aligned sequential: 16 accesses / lines", len({(0x1000 + 4 * i) // 64 for i in range(16)}), 1)
check("aligned sequential: 17 accesses / lines", len({(0x1000 + 4 * i) // 64 for i in range(17)}), 2)
check("offset sequential: 16 accesses / lines", len({(0x1004 + 4 * i) // 64 for i in range(16)}), 2)
check("stride 16: 16 accesses / lines", len({(0x1000 + 4 * 16 * i) // 64 for i in range(16)}), 16)
check("direct-mapped example: tag, index, offset", (0x1234 >> 12, (0x1234 >> 6) & 63, 0x1234 & 63), (1, 8, 52))
check("4 KiB page: number, offset", divmod(0x1234, 4096), (1, 564))
print("Лекция №4: все 17 расчётных проверок пройдены.")
