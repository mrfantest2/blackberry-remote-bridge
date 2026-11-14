"""Prove bounded UART failure in a real ARM guest with test-instrumented QEMU.

QEMU 8.2.2's normal PL011 does not set TXFF. We patch its *device model*
in a disposable hosted build. The guest's actual ARM MMIO driver is unchanged.
This is NOT an unmodified-QEMU TX stall or BlackBerry hardware test.
"""
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_guest_boot_faults import Qmp, symbols  # noqa: E402

BUDGET = 65536
FAILED = 0x064BAD11
READY = 0x06460003
MARKER = b"TORCHOS_PL011_TXFF_INJECTED"


class ActualGuestPL011(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.elf = ROOT / "build" / "torchos.elf"
        cls.qemu = Path(os.environ["TORCHOS_CP065_QEMU"]).resolve()
        if not cls.qemu.is_file() or not cls.elf.is_file():
            raise AssertionError("QEMU laboratory executable or ARM ELF missing")
        version = subprocess.run([str(cls.qemu), "--version"],
                                 check=True, capture_output=True, timeout=5)
        if b"8.2.2" not in version.stdout:
            raise AssertionError(f"wrong QEMU release: {version.stdout!r}")
        cls.sym = symbols()
        if "cp065_command_dispatch_count" not in cls.sym:
            raise AssertionError("RAM-only command counter not found in actual ARM ELF")
        print("CP006.5 emulator:", version.stdout.decode().splitlines()[0])

    def boot(self, injected):
        with tempfile.TemporaryDirectory(prefix="cp065-") as tmp:
            qmp_sock = Path(tmp) / "qmp.sock"
            cmd = [str(self.qemu), "-machine", "virt-8.2",
                   "-cpu", "cortex-a15", "-m", "128M", "-nic", "none",
                   "-display", "none", "-monitor", "none",
                   "-serial", "stdio", "-no-reboot",
                   "-kernel", str(self.elf), "-S",
                   "-qmp", f"unix:{qmp_sock},server=on,wait=off"]
            env = dict(os.environ)
            env.pop("TORCHOS_QEMU_FORCE_PL011_TXFF", None)
            if injected:
                env["TORCHOS_QEMU_FORCE_PL011_TXFF"] = "1"
            proc = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
            qmp = None
            serial = bytearray()
            record = None
            try:
                qmp = Qmp(qmp_sock)
                qmp.hmp("cont")
                deadline = time.monotonic() + 6
                target = FAILED if injected else READY
                phase = None
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        raise AssertionError(f"QEMU crashed: {proc.returncode}")
                    phase = qmp.word(self.sym["cp064_boot_phase"])
                    if phase == target:
                        break
                    time.sleep(0.025)
                self.assertEqual(phase, target, f"ARM did not reach expected boot state: {phase!r}")
                if not injected:
                    proc.stdin.write(b"help\r")
                    proc.stdin.flush()
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        if proc.poll() is not None:
                            raise AssertionError(f"QEMU exited before terminal response: {proc.returncode}")
                        readable, _, _ = select.select([proc.stdout], [], [], 0.05)
                        if readable:
                            serial.extend(os.read(proc.stdout.fileno(), 4096))
                        if b"Available: help about status" in serial and \
                                qmp.word(self.sym["cp065_command_dispatch_count"]) > 0:
                            break
                    self.assertIn(b"Available: help about status", serial,
                                  "test QEMU normal-mode UART not functional")
                qmp.hmp("stop")
                phase = qmp.word(self.sym["cp064_boot_phase"])
                reads = qmp.word(self.sym["cp064_mmio_reads"])
                writes = qmp.word(self.sym["cp064_mmio_writes"])
                dispatched = qmp.word(self.sym["cp065_command_dispatch_count"])
                registers = qmp.registers()
                record = (phase, reads, writes, dispatched, registers)
                print(f"CP006.5 injected={injected} phase={phase:#x} "
                      f"mmio_reads={reads} mmio_writes={writes} commands={dispatched}")
            finally:
                if qmp:
                    qmp.close()
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=2)
                if proc.stdout:
                    serial.extend(proc.stdout.read())
                    proc.stdout.close()
                stderr = proc.stderr.read() if proc.stderr else b""
                if proc.stderr:
                    proc.stderr.close()
                if proc.stdin:
                    proc.stdin.close()
            if record is None:
                raise AssertionError(f"no ARM guest telemetry; QEMU stderr: {stderr[:1200]!r}")
            return (*record, bytes(serial), stderr)

    def test_01_real_arm_normal_uart_on_instrumented_device(self):
        phase, reads, writes, dispatch, _, serial, err = self.boot(False)
        self.assertEqual(phase, READY)
        self.assertGreater(reads, 0)
        self.assertGreater(writes, 0)
        self.assertGreater(dispatch, 0)
        self.assertIn(b"torch> ", serial)
        self.assertNotIn(MARKER, err)

    def test_02_real_arm_txff_forced_by_qemu_pl011_model(self):
        phase, reads, writes, dispatch, regs, serial, err = self.boot(True)
        self.assertEqual(phase, FAILED)
        self.assertEqual(reads, BUDGET, "read count must equal finite TX budget")
        self.assertEqual(writes, 0, "failed UART must transmit zero characters")
        self.assertEqual(dispatch, 0, "no commands may be dispatched after UART failure")
        pc = re.search(r"\bR15=([0-9a-fA-F]{8})", regs)
        self.assertIsNotNone(pc, regs)
        self.assertIn(int(pc.group(1), 16),
                      (self.sym["cp064_halt"], self.sym["cp064_halt"] + 4),
                      "ARM guest is not in named fail-closed WFI")
        self.assertIn(MARKER, err, "QEMU device did not emit its PL011 injection marker")
        self.assertNotIn(b"TorchOS CP005", serial,
                         "UART failure produced successful boot text")

if __name__ == "__main__":
    unittest.main()
