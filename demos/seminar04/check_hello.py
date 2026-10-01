"""Boot the one-sector teaching program and inspect its VGA text in QEMU."""

from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import re
import socket
import subprocess
import time


def check(image: Path) -> None:
    assert image.stat().st_size == 1440 * 1024
    with TemporaryDirectory() as directory:
        monitor = Path(directory) / "monitor.sock"
        proc = subprocess.Popen([
            "qemu-system-i386", "-machine", "pc", "-m", "16M", "-boot", "order=a",
            "-drive", f"file={image},format=raw,if=floppy", "-display", "none",
            "-serial", "none", "-no-reboot",
            "-monitor", f"unix:{monitor},server=on,wait=off",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 12
            observed = None
            while time.monotonic() < deadline:
                try:
                    with socket.socket(socket.AF_UNIX) as connection:
                        connection.connect(str(monitor))
                        connection.settimeout(.3)
                        output = b""
                        while time.monotonic() < deadline:
                            try:
                                connection.recv(4096)  # clear QEMU prompt
                            except socket.timeout:
                                pass
                            connection.sendall(b"xp /20bx 0xb8000\n")
                            output = b""
                            while b"(qemu)" not in output and time.monotonic() < deadline:
                                try:
                                    output += connection.recv(4096)
                                except socket.timeout:
                                    continue
                            rows = re.findall(rb"(?m)^[0-9a-fA-F]{8,16}: (.*)$", output)
                            values = [int(value, 16) for row in rows
                                      for value in re.findall(rb"0x([0-9a-fA-F]{2})\b", row)]
                            if len(values) == 20:
                                observed = bytes(values[::2])
                            if len(values) == 20 and bytes(values[::2]) == b"HELLO BIOS":
                                print("BIOS boot sector: HELLO BIOS on VGA — OK")
                                return
                        raise AssertionError(f"Нет HELLO BIOS в первой строке VGA: {observed!r}; last monitor: {output!r}")
                except (OSError, ConnectionError):
                    if proc.poll() is not None:
                        assert proc.stderr is not None
                        raise AssertionError(f"QEMU завершился: {proc.stderr.read()!r}")
                    time.sleep(.05)
            raise AssertionError("QEMU monitor не стал доступен")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    check(parser.parse_args().image)
