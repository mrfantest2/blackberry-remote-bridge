"""CP006.6 experimental actual QEMU GICv2 software-generated interrupt.

The test redirects QEMU guest CPU PC through GDB into an isolated
ARM-only probe which programs QEMU virt-8.2 GICv2 and unmasks CPU IRQ. The *actual*
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
                     "cp066_probe_gicv2_sgi0",
                     "cp066_gic_dist_readback", "cp066_gic_cpu_readback",
                     "cp066_gic_pmr_readback",
                     "__image_start", "__image_end",
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
                # QEMU virt-8.2 GICv2 distributor/CPU addresses are
                # restricted to the lab-only ARM probe in startup.S.
                # SGI0 is enabled and targeted to self in the guest-only
                # probe (normal kernel and IRQ mask unchanged).
                gdb = subprocess.run([
                    "gdb-multiarch", "-q", "--batch",
                    "-ex", "set architecture arm",
                    "-ex", f"target remote {gdb_sock}",
                    "-ex", f"set $pc = 0x{self.syms['cp066_probe_gicv2_sgi0']:x}",
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
                                 f"actual IRQ not observed: phase {phase!r}; dist={qmp.word(self.syms['cp066_gic_dist_readback']):#x}; cpu={qmp.word(self.syms['cp066_gic_cpu_readback']):#x}; pmr={qmp.word(self.syms['cp066_gic_pmr_readback']):#x}; GDB={gdb.stdout!r}; registers={qmp.registers()!r}")
                qmp.hmp("stop")
                self.assertEqual(qmp.word(self.syms["cp066_exception_kind"]), 5,
                                 "CPU took wrong exception vector, not IRQ")
                self.assertEqual(qmp.word(self.syms["cp066_gic_dist_readback"]) & 1, 1,
                                 "guest did not enable GIC distributor")
                self.assertEqual(qmp.word(self.syms["cp066_gic_cpu_readback"]) & 1, 1,
                                 "guest did not enable GIC CPU interface")
                self.assertEqual(qmp.word(self.syms["cp066_gic_pmr_readback"]) & 0xff, 0xff,
                                 "guest GIC priority mask not set")
                exception_lr = qmp.word(self.syms["cp066_saved_lr"])
                self.assertGreaterEqual(exception_lr, self.syms["__image_start"])
                self.assertLess(exception_lr, self.syms["__image_end"] + 4)
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
