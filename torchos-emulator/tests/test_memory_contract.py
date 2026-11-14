"""CP006.4 verify real linked ARM image layout and QEMU virtual RAM bounds."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "build" / "torchos.elf"
RAM_START = 0x40000000
RAM_END = 0x48000000
DTB_WINDOW_END = 0x40100000


class LinkedMemoryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ELF.is_file():
            raise AssertionError("ARM ELF missing")
        result = subprocess.run(["arm-none-eabi-nm", "-n", str(ELF)],
                                capture_output=True, text=True, timeout=20, check=True)
        cls.syms = {}
        for line in result.stdout.splitlines():
            match = re.match(r"^([0-9a-f]+) [A-Za-z] ([a-zA-Z_][a-zA-Z_0-9]*)$", line)
            if match:
                cls.syms[match.group(2)] = int(match.group(1), 16)
        mandatory = ("__image_start", "__image_end", "__bss_start", "__bss_end",
                     "__stack_bottom", "__stack_top", "_start",
                     "cp064_boot_phase", "cp064_mmio_reads", "cp064_mmio_writes")
        for name in mandatory:
            if name not in cls.syms:
                raise AssertionError(f"ELF linker symbol absent: {name}")

    def test_image_cannot_overlap_fdt_window(self):
        self.assertGreaterEqual(self.syms["__image_start"], DTB_WINDOW_END)
        self.assertLess(self.syms["__image_start"], RAM_END)

    def test_complete_image_is_within_qemu_ram(self):
        self.assertLess(self.syms["__image_start"], self.syms["__image_end"])
        self.assertLessEqual(self.syms["__image_end"], RAM_END)
        self.assertGreaterEqual(self.syms["__image_start"], RAM_START)

    def test_bss_and_stack_are_in_elf_ram(self):
        a = self.syms
        self.assertLessEqual(a["__image_start"], a["__bss_start"])
        self.assertLess(a["__bss_start"], a["__bss_end"])
        self.assertLessEqual(a["__bss_end"], a["__stack_bottom"])
        self.assertLess(a["__stack_bottom"], a["__stack_top"])
        self.assertLessEqual(a["__stack_top"], a["__image_end"])

    def test_stack_has_exact_bounded_capacity(self):
        self.assertEqual(self.syms["__stack_top"] - self.syms["__stack_bottom"], 16384)

    def test_fault_markers_reside_in_guest_bss(self):
        s = self.syms
        for name in ("cp064_boot_phase", "cp064_mmio_reads", "cp064_mmio_writes"):
            self.assertGreaterEqual(s[name], s["__bss_start"])
            self.assertLess(s[name], s["__bss_end"])
        self.assertGreaterEqual(s["_start"], s["__image_start"])
        self.assertLess(s["_start"], s["__image_end"])


if __name__ == "__main__":
    unittest.main()
