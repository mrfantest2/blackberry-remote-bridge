"""Launch the original freestanding ARM ELF in QEMU; no device access."""
from pathlib import Path
import os
import select
import shutil
import subprocess
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "build" / "torchos.elf"


class ArmConsole:
    def __init__(self):
        self.proc = subprocess.Popen(
            [
                "qemu-system-arm", "-machine", "virt",
                "-cpu", "cortex-a15", "-m", "128M",
                "-nographic", "-monitor", "none",
                "-serial", "stdio", "-no-reboot", "-kernel", str(ELF),
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.output = bytearray()
        self.offset = 0

    def until(self, token=b"torch> ", timeout=12):
        deadline = time.monotonic() + timeout
        while token not in self.output[self.offset:]:
            if self.proc.poll() is not None:
                raise AssertionError(f"QEMU exited {self.proc.returncode}: {bytes(self.output)!r}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(f"Timed out waiting for {token!r}: {bytes(self.output)[-1200:]!r}")
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remaining, 0.25))
            if ready:
                chunk = os.read(self.proc.stdout.fileno(), 4096)
                if not chunk:
                    raise AssertionError("QEMU closed stdout")
                self.output.extend(chunk)
        result = bytes(self.output[self.offset:])
        self.offset = len(self.output)
        return result

    def command(self, cmd):
        self.proc.stdin.write(cmd)
        self.proc.stdin.flush()
        return self.until()

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3)
        for pipe in (self.proc.stdin, self.proc.stdout):
            if pipe:
                pipe.close()


class QemuBoot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("qemu-system-arm"):
            raise AssertionError("qemu-system-arm missing; no false skips")
        if not ELF.is_file() or ELF.stat().st_size < 256:
            raise AssertionError("ARM ELF missing; run make -C torchos-emulator all")

    def setUp(self):
        self.console = ArmConsole()

    def tearDown(self):
        self.console.close()

    def test_cold_boot_into_original_kernel(self):
        banner = self.console.until()
        self.assertIn(b"TorchOS CP005", banner)
        self.assertIn(b"Independent ARM Research Boot", banner)
        self.assertIn(b"QEMU VIRTUAL MACHINE ONLY", banner)
        self.assertIn(b"NOT BLACKBERRY HARDWARE", banner)

    def test_local_commands_and_truthful_hardware(self):
        self.console.until()
        help_out = self.console.command(b"help\r")
        self.assertIn(b"Available: help about status clear history notes files", help_out)
        status = self.console.command(b"status\r")
        self.assertIn(b"BlackBerry hardware: NOT CONNECTED", status)
        self.assertIn(b"NOT IMPLEMENTED", status)
        files = self.console.command(b"files\r")
        self.assertIn(b"no filesystem mounted", files)
        history = self.console.command(b"history\r")
        self.assertIn(b"help", history)
        self.assertIn(b"status", history)

    def test_rejects_unknown_and_nonprinting_input(self):
        self.console.until()
        unknown = self.console.command(b"shutdown\r")
        self.assertIn(b"Unknown command", unknown)
        invalid = self.console.command(b"\x01")
        self.assertIn(b"Non-printable input rejected.", invalid)
        self.assertIn(b"torch> ", invalid)


if __name__ == "__main__":
    unittest.main()
