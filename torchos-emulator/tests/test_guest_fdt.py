"""CP006.3 tests: actual guest C parser and QEMU-generated FDT, no handset access."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from test_fdt_inventory import fixture

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "build" / "guest_fdt_harness"


class GuestFdtParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        HARNESS.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
            "-I", str(ROOT / "src"),
            str(ROOT / "src" / "guest_fdt.c"),
            str(ROOT / "tests" / "guest_fdt_harness.c"),
            "-o", str(HARNESS),
        ], check=True, timeout=15)

    def check_blob(self, blob, accepted):
        with tempfile.TemporaryDirectory(prefix="torchos-cp0063-") as folder:
            target = Path(folder) / "test.dtb"
            target.write_bytes(blob)
            run = subprocess.run([str(HARNESS), str(target)],
                                 capture_output=True, text=True, timeout=5)
            self.assertEqual(run.returncode == 0, accepted,
                             run.stdout + run.stderr)
            return run.stdout

    def test_valid_fixture(self):
        output = self.check_blob(fixture(), True)
        self.assertIn("uart=0x09000000", output)
        self.assertIn("ram=0x40000000", output)

    def test_dynamic_uart_address_is_not_hardcoded(self):
        blob = fixture()
        old = struct.pack(">4I", 0, 0x09000000, 0, 4096)
        new = struct.pack(">4I", 0, 0x09001000, 0, 4096)
        self.assertEqual(blob.count(old), 1)
        output = self.check_blob(blob.replace(old, new), True)
        self.assertIn("uart=0x09001000", output)

    def test_rejects_missing_uart(self):
        self.check_blob(fixture(uart=False), False)

    def test_rejects_missing_memory(self):
        self.check_blob(fixture(memory=False), False)

    def test_rejects_bad_magic(self):
        self.check_blob(b"\0\0\0\0" + fixture()[4:], False)

    def test_rejects_truncated_blob(self):
        self.check_blob(fixture()[:-3], False)

    def test_rejects_uart_pointer_into_ram(self):
        blob = fixture()
        old = struct.pack(">4I", 0, 0x09000000, 0, 4096)
        new = struct.pack(">4I", 0, 0x40000000, 0, 4096)
        self.assertEqual(blob.count(old), 1)
        self.check_blob(blob.replace(old, new), False)

    def test_rejects_oversized_blob(self):
        self.check_blob(fixture() + b"x" * (1024 * 1024 + 1), False)

    def test_real_qemu_virt_fdt_matches_guest_parser(self):
        with tempfile.TemporaryDirectory(prefix="torchos-cp0063-qemu-") as folder:
            target = Path(folder) / "virt.dtb"
            subprocess.run([
                "qemu-system-arm", "-machine", "virt-8.2,dumpdtb=" + str(target),
                "-cpu", "cortex-a15", "-m", "128M", "-nic", "none",
                "-display", "none", "-monitor", "none", "-serial", "none",
            ], check=True, capture_output=True, timeout=15)
            run = subprocess.run([str(HARNESS), str(target)],
                                 capture_output=True, text=True, timeout=5)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("uart=0x09000000", run.stdout)
            self.assertIn("ram=0x40000000", run.stdout)


if __name__ == "__main__":
    unittest.main()
