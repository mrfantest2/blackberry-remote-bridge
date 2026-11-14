"""CP006.4 hosted tests for hardware-independent console and bounded UART."""
from pathlib import Path
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "module_harness"

class IndependentModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
            "-I", str(ROOT / "src"),
            str(ROOT / "tests" / "module_harness.c"),
            str(ROOT / "src" / "console.c"),
            str(ROOT / "src" / "commands.c"),
            str(ROOT / "src" / "uart_poll.c"),
            "-o", str(OUT),
        ], check=True, capture_output=True, timeout=15)
    def run_mode(self, name, marker):
        proc = subprocess.run([str(OUT), name], capture_output=True,
                              text=True, timeout=5)
        self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
        self.assertIn(marker, proc.stdout)
    def test_uart_poll_budget_and_mmio_readiness(self):
        self.run_mode("uart", "HOST_UART_BOUNDS_OK")
    def test_console_commands_and_transport_independent_of_qemu(self):
        self.run_mode("console", "HOST_CONSOLE_OK")
