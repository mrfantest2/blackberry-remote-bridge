"""CP006.7: real QEMU GICv2 SGI serviced by the guest, then console resumes.

Host role is limited to: cold boot, pause in the console loop, push the
interrupted PC on the guest SVC stack and redirect PC to the test-only
probe (GDB), plus read-only RAM/MMIO observation (QMP) and UART bytes.
The GUEST performs all GIC MMIO, the CPU takes a genuine IRQ exception,
and the guest handler performs IAR, ID check, EOIR and exception return.
QEMU virt-8.2 only. No BlackBerry, firmware, or physical hardware.
"""
from pathlib import Path
import os
import re
import select
import subprocess
import tempfile
import time
import unittest
from test_guest_boot_faults import Qmp, symbols

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "build" / "torchos.elf"
READY = 0x06460003
IRQ_REJECTED = 0x067BAD01
IRQ_NESTED = 0x067BAD02
PROBE_REJECTED = 0x067BAD03
GICD_CTLR = 0x08000000
GICC_CTLR = 0x08010000
PROMPT = b"torch> "


class Guest:
    def __init__(self, tmp):
        folder = Path(tmp)
        self.gdb_sock = folder / "gdb.sock"
        qmp_sock = folder / "qmp.sock"
        self.proc = subprocess.Popen([
            "qemu-system-arm", "-machine", "virt-8.2,gic-version=2",
            "-cpu", "cortex-a15", "-m", "128M",
            "-display", "none", "-monitor", "none", "-nic", "none",
            "-serial", "stdio", "-no-reboot", "-kernel", str(ELF), "-S",
            "-chardev", f"socket,path={self.gdb_sock},server=on,wait=off,id=gdb0",
            "-gdb", "chardev:gdb0",
            "-qmp", f"unix:{qmp_sock},server=on,wait=off",
        ], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0)
        self.out = bytearray()
        self.offset = 0
        self.qmp = Qmp(qmp_sock)

    def until(self, token, timeout=6):
        deadline = time.monotonic() + timeout
        while token not in self.out[self.offset:]:
            if self.proc.poll() is not None:
                raise AssertionError(f"QEMU exited: {bytes(self.out)!r}")
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError(f"timeout for {token!r}: {bytes(self.out)[-600:]!r}")
            ready, _, _ = select.select([self.proc.stdout], [], [], min(left, 0.2))
            if ready:
                self.out.extend(os.read(self.proc.stdout.fileno(), 4096))
        chunk = bytes(self.out[self.offset:])
        self.offset = len(self.out)
        return chunk

    def send(self, line):
        for b in line.encode() + b"\n":
            self.proc.stdin.write(bytes((b,)))
            self.proc.stdin.flush()
            time.sleep(0.002)
        return self.until(PROMPT)

    def wait_word(self, addr, wanted, timeout=4):
        deadline = time.monotonic() + timeout
        value = None
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise AssertionError(f"QEMU crashed: {self.proc.returncode}")
            value = self.qmp.word(addr)
            if value == wanted:
                return value
            time.sleep(0.03)
        return value

    def psr(self):
        regs = self.qmp.registers()
        m = re.search(r"\bPSR=([0-9a-fA-F]{8})", regs)
        if not m:
            raise AssertionError(regs)
        return int(m.group(1), 16), regs

    def pc(self):
        regs = self.qmp.registers()
        return int(re.search(r"\bR15=([0-9a-fA-F]{8})", regs).group(1), 16)

    def gdb(self, *commands):
        args = ["gdb-multiarch", "-q", "--batch", "-ex", "set architecture arm",
                "-ex", f"target remote {self.gdb_sock}"]
        for c in commands:
            args += ["-ex", c]
        args += ["-ex", "detach"]
        r = subprocess.run(args, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            raise AssertionError(f"gdb failed: {r.stdout} {r.stderr}")
        return r.stdout

    def resume(self):
        if not self.qmp.command("query-status")["running"]:
            self.qmp.hmp("cont")

    def close(self):
        try:
            self.qmp.close()
        finally:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=2)
            for s in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                if s:
                    s.close()


class CP067GicResume(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = symbols()
        for name in ("cp067_probe_gicv2_resume", "cp067_irq_entry",
                     "cp067_irq_armed", "cp067_in_irq", "cp067_irq_count",
                     "cp067_spurious_count", "cp067_last_iar",
                     "cp067_resume_pc", "cp067_resume_spsr",
                     "cp067_test_sgi_id", "cp067_rejected_id",
                     "cp066_vector_table", "cp066_exception_kind",
                     "cp065_command_dispatch_count", "kmain",
                     "__image_start", "__image_end"):
            if name not in cls.s:
                raise AssertionError("missing guest symbol " + name)

    def booted(self, tmp):
        g = Guest(tmp)
        self.addCleanup(g.close)
        g.qmp.hmp("cont")
        g.until(PROMPT)
        self.assertEqual(g.wait_word(self.s["cp064_boot_phase"], READY), READY)
        return g

    def inject(self, g, sgi_id=0, preset_in_irq=None):
        """Pause in the console loop; push PC; redirect into guest probe."""
        g.qmp.hmp("stop")
        pc = g.pc()
        self.assertGreaterEqual(pc, self.s["__image_start"])
        self.assertLess(pc, self.s["__image_end"])
        cmds = [f"set {{unsigned int}}0x{self.s['cp067_test_sgi_id']:x} = {sgi_id}"]
        if preset_in_irq is not None:
            cmds.append(f"set {{unsigned int}}0x{self.s['cp067_in_irq']:x} = {preset_in_irq}")
        cmds += ["set $sp = $sp - 4", "set {unsigned int}$sp = $pc",
                 f"set $pc = 0x{self.s['cp067_probe_gicv2_resume']:x}"]
        g.gdb(*cmds)
        g.resume()
        return pc

    def test_normal_boot_never_touches_gic_and_keeps_irq_fiq_masked(self):
        with tempfile.TemporaryDirectory(prefix="cp067-boot-") as tmp:
            g = self.booted(tmp)
            g.qmp.hmp("stop")
            psr, regs = g.psr()
            self.assertEqual(psr & 0xC0, 0xC0, regs)
            self.assertEqual(psr & 0x1F, 0x13, regs)
            # GICD_TYPER is read-only and non-zero: proves QMP xp really
            # reads GIC MMIO, so the CTLR==0 assertions are meaningful.
            self.assertNotEqual(g.qmp.word(GICD_CTLR + 4), 0, "GIC MMIO not observable")
            self.assertEqual(g.qmp.word(GICD_CTLR) & 1, 0)
            self.assertEqual(g.qmp.word(GICC_CTLR) & 1, 0)
            for n in ("cp067_irq_armed", "cp067_irq_count", "cp067_last_iar",
                      "cp067_spurious_count", "cp066_exception_kind"):
                self.assertEqual(g.qmp.word(self.s[n]), 0, n)

    def test_sgi0_acknowledged_eoi_and_console_resumes(self):
        with tempfile.TemporaryDirectory(prefix="cp067-ok-") as tmp:
            g = self.booted(tmp)
            self.assertIn(b"Available:", g.send("help"))
            before = g.qmp.word(self.s["cp065_command_dispatch_count"])
            pc = self.inject(g, 0)
            self.assertEqual(g.wait_word(self.s["cp067_irq_count"], 1), 1,
                             "guest did not service SGI0")
            time.sleep(0.3)  # let any erroneous re-delivery surface
            g.qmp.hmp("stop")
            w = lambda n: g.qmp.word(self.s[n])
            self.assertEqual(w("cp067_irq_count"), 1, "IRQ serviced more than once")
            self.assertEqual(w("cp064_boot_phase"), READY)
            self.assertEqual(w("cp066_exception_kind"), 0, "fell into CP006.6 trap")
            self.assertEqual(w("cp067_last_iar") & 0x3FF, 0)
            self.assertEqual(w("cp067_spurious_count"), 0)
            self.assertEqual(w("cp067_irq_armed"), 0)
            self.assertEqual(w("cp067_in_irq"), 0)
            # Real IRQ was taken by the console code at the exact paused PC.
            self.assertEqual(w("cp067_resume_pc"), pc)
            spsr = w("cp067_resume_spsr")
            self.assertEqual(spsr & 0x1F, 0x13)
            self.assertEqual(spsr & 0xC0, 0xC0, "console not re-masked")
            self.assertEqual(g.qmp.word(GICD_CTLR) & 1, 0, "GICD left enabled")
            self.assertEqual(g.qmp.word(GICC_CTLR) & 1, 0, "GICC left enabled")
            psr, regs = g.psr()
            self.assertEqual(psr & 0x1F, 0x13, regs)
            self.assertEqual(psr & 0xC0, 0xC0, regs)
            g.resume()
            self.assertIn(b"Available:", g.send("help"))
            self.assertIn(b"volatile RAM", g.send("notes set cp067-ok"))
            self.assertIn(b"Volatile note: cp067-ok", g.send("notes show"))
            self.assertIn(b"no filesystem mounted", g.send("files"))
            self.assertEqual(w("cp065_command_dispatch_count"), before + 4)
            self.assertEqual(w("cp067_irq_count"), 1)
            print(f"CP006.7 SGI0 IAR=0x{w('cp067_last_iar'):08x} EOI; "
                  f"resumed console at 0x{pc:08x}, SPSR=0x{spsr:08x}")

    def assert_fail_closed(self, g, phase):
        self.assertEqual(g.wait_word(self.s["cp064_boot_phase"], phase), phase)
        g.qmp.hmp("stop")
        self.assertEqual(g.qmp.word(self.s["cp067_irq_count"]), 0)
        self.assertEqual(g.qmp.word(self.s["cp067_irq_armed"]), 0)
        self.assertEqual(g.qmp.word(GICD_CTLR) & 1, 0)
        self.assertEqual(g.qmp.word(GICC_CTLR) & 1, 0)
        pc = g.pc()
        self.assertIn(pc, (self.s["cp064_halt"], self.s["cp064_halt"] + 4))
        psr, regs = g.psr()
        self.assertEqual(psr & 0x80, 0x80, regs)

    def test_unsupported_sgi_id_is_eoi_then_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="cp067-bad-") as tmp:
            g = self.booted(tmp)
            self.inject(g, 3)
            self.assert_fail_closed(g, IRQ_REJECTED)
            self.assertEqual(g.qmp.word(self.s["cp067_rejected_id"]), 3)
            self.assertEqual(g.qmp.word(self.s["cp067_last_iar"]) & 0x3FF, 3)

    def test_nested_entry_guard_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="cp067-nest-") as tmp:
            g = self.booted(tmp)
            self.inject(g, 0, preset_in_irq=1)
            self.assert_fail_closed(g, IRQ_NESTED)
            self.assertEqual(g.qmp.word(self.s["cp067_last_iar"]), 0,
                             "nested guard must reject before IAR read")

    def test_out_of_range_probe_request_rejected_without_gic_access(self):
        with tempfile.TemporaryDirectory(prefix="cp067-range-") as tmp:
            g = self.booted(tmp)
            self.inject(g, 16)
            self.assertEqual(g.wait_word(self.s["cp064_boot_phase"], PROBE_REJECTED),
                             PROBE_REJECTED)
            g.qmp.hmp("stop")
            self.assertEqual(g.qmp.word(GICD_CTLR) & 1, 0)
            self.assertEqual(g.qmp.word(self.s["cp067_irq_armed"]), 0)


if __name__ == "__main__":
    unittest.main()
