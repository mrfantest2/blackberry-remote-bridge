"""CP006.6 experimental actual QEMU GICv2 software-generated interrupt.

The host test programs a disposable QEMU 8.2.2 virt-8.2 GICv2 via the
emulator's GDB memory protocol, then unmasks IRQ in CPU CPSR. The *actual*
virtual ARM core must take the IRQ and enter the installed vector.
This does NOT implement a reusable in-guest GIC driver or touch real hardware.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest
from test_guest_boot_faults import Qmp, symbols

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "build" / "torchos.elf"
READY = 0x06460003
EXCEPTION = 0x066BAD00

class QemuGicV2GuestIRQ(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.syms = symbols()
        for name in ("cp066_vector_table", "cp066_exception_kind",
                     "cp066_saved_lr", "cp066_saved_spsr",
                     "cp064_boot_phase", "cp064_halt",
                     "cp065_command_dispatch_count"):
            if name not in cls.syms:
                raise AssertionError("required guest telemetry absent: " + name)

    def test_real_gicv2_sgi_reaches_guest_irq_vector(self):
        with tempfile.TemporaryDirectory(prefix="cp066-gic-") as tmp:
            folder = Path(tmp)
            gdb_sock = folder / "gdb.sock"
            qmp_sock = folder / "qmp.sock"
            cmd = [
                "qemu-system-arm", "-machine", "virt-8.2,gic-version=2",
                "-cpu", "cortex-a15", "-m", "128M",
                "-display", "none", "-monitor", "none", "-nic", "none",
                "-serial", "stdio", "-no-reboot", "-kernel", str(ELF),
                "-S",
                "-chardev", f"socket,path={gdb_sock},server=on,wait=off,id=gdb0",
                "-gdb", "chardev:gdb0",
                "-qmp", f"unix:{qmp_sock},server=on,wait=off",
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            qmp = None
            try:
                qmp = Qmp(qmp_sock)
                qmp.hmp("cont")
                until = time.monotonic() + 5
                phase = None
                while time.monotonic() < until:
                    if proc.poll() is not None:
                        self.fail(f"QEMU stopped before boot: {proc.returncode}")
                    phase = qmp.word(self.syms["cp064_boot_phase"])
                    if phase == READY:
                        break
                    time.sleep(0.03)
                self.assertEqual(phase, READY)
                self.assertEqual(qmp.word(self.syms["cp066_exception_kind"]), 0)
                qmp.hmp("stop")
                # QEMU virt-8.2 GICv2 maps its distributor 0x08000000
                # and CPU interface 0x08010000 (QEMU v8.2.2 hw/arm/virt.c).
                # SGI0 is enabled in distributor and targeted to self via
                # the architected GICD_SGIR target filter 0b10.
                gdb = subprocess.run([
                    "gdb-multiarch", "-q", "--batch",
                    "-ex", "set architecture arm",
                    "-ex", f"target remote {gdb_sock}",
                    "-ex", "set {unsigned int}0x08000000 = 1",
                    "-ex", "set {unsigned int}0x08010004 = 255",
                    "-ex", "set {unsigned int}0x08010000 = 1",
                    "-ex", "set {unsigned int}0x08000100 = 1",
                    "-ex", "set {unsigned int}0x08000f00 = 0x02000000",
                    "-ex", "set $cpsr = $cpsr & ~0x80",
                    "-ex", "detach",
                ], capture_output=True, text=True, timeout=12)
                self.assertEqual(gdb.returncode, 0,
                                 f"GICv2/CPU test injection failed: {gdb.stdout} {gdb.stderr}")
                if not qmp.command("query-status")["running"]:
                    qmp.hmp("cont")
                until = time.monotonic() + 4
                phase = None
                while time.monotonic() < until:
                    if proc.poll() is not None:
                        self.fail(f"QEMU crashed: {proc.returncode}")
                    phase = qmp.word(self.syms["cp064_boot_phase"])
                    if phase == EXCEPTION:
                        break
                    time.sleep(0.03)
                self.assertEqual(phase, EXCEPTION,
                                 f"actual IRQ not observed: phase {phase!r}")
                qmp.hmp("stop")
                self.assertEqual(qmp.word(self.syms["cp066_exception_kind"]), 5,
                                 "CPU took wrong exception vector, not IRQ")
                saved_spsr = qmp.word(self.syms["cp066_saved_spsr"])
                self.assertEqual(saved_spsr & 0x1f, 0x13)
                self.assertEqual(saved_spsr & 0x80, 0,
                                 "IRQ was not unmasked in pre-exception CPU")
                self.assertEqual(qmp.word(self.syms["cp065_command_dispatch_count"]),
                                 0)
                regs = qmp.registers()
                match = re.search(r"\bR15=([0-9a-fA-F]{8})", regs)
                self.assertIsNotNone(match, regs)
                self.assertIn(int(match.group(1), 16),
                              (self.syms["cp064_halt"],
                               self.syms["cp064_halt"] + 4))
                print("CP006.6 genuine QEMU GICv2 SGI0 IRQ reached guest vector; "
                      f"SPSR=0x{saved_spsr:08x}")
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
                for s in (proc.stdin, proc.stdout, proc.stderr):
                    if s:
                        s.close()


if __name__ == "__main__":
    unittest.main()
