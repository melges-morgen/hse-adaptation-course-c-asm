"""QEMU integration: real-mode BIOS boot, keyboard, IRQ and disk persistence."""
from pathlib import Path
import os
import selectors
import socket
import subprocess
import tempfile
import time


ROOT = Path("build/lecture04-journal")


class Machine:
    def __init__(self, stage, path, disk=None):
        path.unlink(missing_ok=True)
        command = [
            "qemu-system-i386", "-machine", "pc", "-m", "16M",
            "-drive", f"file={ROOT / f'stage{stage}/boot.img'},format=raw,if=floppy",
            "-boot", "order=a",
            "-display", "none", "-serial", "stdio", "-no-reboot",
            "-monitor", f"unix:{path},server=on,wait=off",
        ]
        if disk:
            command.extend(["-drive", f"file={disk},format=raw,if=ide,index=0,media=disk"])
        self.proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert self.proc.stdout is not None and self.proc.stderr is not None
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.proc.stdout, selectors.EVENT_READ)
        self.data = ""
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            try:
                self.monitor = socket.socket(socket.AF_UNIX)
                self.monitor.connect(str(path))
                self.monitor.settimeout(1)
                break
            except (OSError, ConnectionError):
                time.sleep(.05)
        else:
            self.close()
            raise AssertionError("QEMU monitor did not start")
        self.expect("READY", 15)

    def expect(self, text, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if text in self.data:
                if text == "READY":
                    self.boot_data = self.data[:self.data.index(text)]
                self.data = self.data[self.data.index(text) + len(text):]
                return
            if self.proc.poll() is not None:
                assert self.proc.stderr is not None
                raise AssertionError(f"QEMU exited: {self.proc.stderr.read()!r}; serial: {self.data!r}")
            for key, _ in self.sel.select(min(.2, max(.01, deadline - time.monotonic()))):
                assert self.proc.stdout is not None
                chunk = os.read(self.proc.stdout.fileno(), 4096)
                if chunk:
                    self.data += chunk.decode("ascii", errors="replace")
        raise AssertionError(f"Missing {text!r}; serial: {self.data!r}")

    def key(self, name, expected):
        self.monitor.sendall(f"sendkey {name}\n".encode())
        self.expect(expected)

    def ignored(self, name):
        self.monitor.sendall(f"sendkey {name}\n".encode())
        time.sleep(.15)
        for key, _ in self.sel.select(.1):
            assert self.proc.stdout is not None
            self.data += os.read(self.proc.stdout.fileno(), 4096).decode("ascii", errors="replace")
        assert "GRADE" not in self.data, f"Unsupported key changed a grade: {self.data!r}"

    def close(self):
        if hasattr(self, "monitor"):
            self.monitor.close()
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        self.sel.close()


def boot(stage, tmp, disk=None):
    return Machine(stage, tmp / "monitor.sock", disk)


def run():
    with tempfile.TemporaryDirectory(dir=ROOT) as location:
        tmp = Path(location)
        disk = tmp / "grades.img"
        with disk.open("wb") as stream:
            stream.truncate(1024 * 1024)

        for stage in (1, 2, 3, 4, 5):
            m = boot(stage, tmp)
            try:
                if stage >= 3:
                    m.key("0", "GRADE S1 W1=0")
                    m.key("a", "GRADE S1 W1=10")
                    m.key("right", "GRADE S1 W2=--")
                    m.key("2", "GRADE S1 W2=2 AVG=6.00" if stage == 5 else "GRADE S1 W2=2")
                    if stage == 5:
                        m.key("backspace", "GRADE S1 W2=-- AVG=10.00")
                        m.key("down", "GRADE S2 W2=-- AVG=--.--")
                        m.key("left", "GRADE S2 W1=-- AVG=--.--")
                        m.key("0", "GRADE S2 W1=0 AVG=0.00")
                        m.key("right", "GRADE S2 W2=-- AVG=0.00")
                        m.key("1", "GRADE S2 W2=1 AVG=0.50")
                        m.key("right", "GRADE S2 W3=-- AVG=0.50")
                        m.key("1", "GRADE S2 W3=1 AVG=0.67")
                    else:
                        m.key("backspace", "GRADE S1 W2=--")
                print(f"stage {stage}: boot and input OK")
            finally:
                m.close()

        m = boot(6, tmp, disk)
        try:
            m.ignored("b")
            m.key("0", "GRADE S1 W1=0 AVG=0.00")
            m.key("right", "GRADE S1 W2=-- AVG=0.00")
            m.key("a", "GRADE S1 W2=10 AVG=5.00")
            m.key("s", "SAVED")
        finally:
            m.close()
        assert disk.read_bytes()[512:516] == b"GR16"
        m = boot(6, tmp, disk)
        try:
            assert "LOADED" in m.boot_data
            m.key("right", "GRADE S1 W2=10 AVG=5.00")
            m.key("left", "GRADE S1 W1=0 AVG=5.00")
            m.key("2", "GRADE S1 W1=2 AVG=6.00")
            m.key("l", "LOADED")
            m.key("right", "GRADE S1 W2=10 AVG=5.00")
            m.key("backspace", "GRADE S1 W2=-- AVG=0.00")
            m.key("s", "SAVED")
        finally:
            m.close()
        print("disk: save, reboot, restore, edit, erase OK")

        original = disk.read_bytes()
        for offset, message in ((512 + 20, "BAD_CHECKSUM"), (512 + 4, "UNSUPPORTED_VERSION"),
                                (512, "BAD_FORMAT"), (512 + 8, "BAD_GRADE")):
            data = bytearray(original)
            data[offset] = 0xfe if message == "BAD_GRADE" else data[offset] ^ 0x40
            if message == "BAD_GRADE":
                checksum = sum(data[512:584]) & 0xffff
                data[584:586] = checksum.to_bytes(2, "little")
            disk.write_bytes(data)
            m = boot(6, tmp, disk)
            try:
                assert message in m.boot_data, (message, m.boot_data)
                m.key("right", "GRADE S1 W2=-- AVG=--.--")
                m.key("1", "GRADE S1 W2=1 AVG=1.00")
                m.key("l", message)
                m.key("right", "GRADE S1 W3=-- AVG=1.00")
            finally:
                m.close()
            print(f"disk: {message} detected on boot")
        disk.write_bytes(bytes(1024 * 1024))
        m = boot(6, tmp, disk)
        assert "EMPTY" in m.boot_data
        m.close()
        m = boot(6, tmp, None)
        try:
            assert "NO_DISK" in m.boot_data
            m.key("s", "NO_DISK")
        finally:
            m.close()
        print("disk: empty / missing device OK")


if __name__ == "__main__":
    run()
