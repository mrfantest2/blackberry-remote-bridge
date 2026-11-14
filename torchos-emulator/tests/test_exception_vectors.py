"""CP006.6: real AArch32 CPU exceptions under QEMU 8.2.2 virt/Cortex-A15.

GDB sets the PC to a guest instruction containing SVC or UDF AFTER the
normal OS-independent boot. The CPU must take the real architectural trap
via the installed VBAR vector; a host-side handler simulation is insufficient.

IRQ/FIQ remain masked and no GIC interrupt injection is claimed here.
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

class QemuAarch32Exception(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.syms = symbols()
        for name in ("cp066_vector_table", "cp066_vbar_readback",
                     "cp066_exception_kind", "cp066_saved_lr",
                     "cp066_saved_spsr", "cp066_probe_svc",
                     "cp066_probe_undefined", "cp064_boot_phase",
                     "cp064_halt", "cp065_command_dispatch_count",
                     "__image_start", "__image_end", "__bss_end",
                     "__und_stack_bottom", "__und_stack_top",
                     "__abt_stack_bottom", "__abt_stack_top",
                     "__irq_stack_bottom", "__irq_stack_top",
                     "__fiq_stack_bottom", "__fiq_stack_top",
                     "__stack_bottom"):
            if name not in cls.syms:
                raise AssertionError("missing ARM symbol: " + name)

    def with_guest(self, trigger=None, expected_kind=None):
        with tempfile.TemporaryDirectory(prefix="cp066-qemu-") as tmp:
            folder = Path(tmp)
            qmp_sock = folder / "qmp.sock"
            gdb_sock = folder / "gdb.sock"
            cmd = [
                "qemu-system-arm", "-machine", "virt-8.2",
                "-cpu", "cortex-a15", "-m", "128M", "-nic", "none",
                "-display", "none", "-monitor", "none",
                "-serial", "stdio", "-no-reboot",
                "-kernel", str(ELF), "-S",
                "-chardev", f"socket,path={gdb_sock},server=on,wait=off,id=gdb0",
                "-gdb", "chardev:gdb0",
                "-qmp", f"unix:{qmp_sock},server=on,wait=off",
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            qmp = None
            try:
                qmp = Qmp(qmp_sock)
                qmp.hmp("cont")
                until = time.monotonic() + 5
                phase = None
                while time.monotonic() < until:
                    if proc.poll() is not None:
                        self.fail(f"QEMU exited during boot: {proc.returncode}")
                    phase = qmp.word(self.syms["cp064_boot_phase"])
                    if phase == READY:
                        break
                    time.sleep(0.03)
                self.assertEqual(phase, READY, f"normal boot failed: {phase!r}")
                vector = self.syms["cp066_vector_table"]
                self.assertEqual(vector & 31, 0)
                self.assertEqual(qmp.word(self.syms["cp066_vbar_readback"]), vector,
                                 "ARM CP15 VBAR hardware readback differs from linked vector")
                self.assertEqual(qmp.word(self.syms["cp066_exception_kind"]), 0)
                self.assertEqual(qmp.word(self.syms["cp065_command_dispatch_count"]), 0)
                if trigger is not None:
                    probe_addr = self.syms[trigger]
                    qmp.hmp("stop")
                    # GDB changes only the PC to the named ARM trap instruction.
                    # It does not modify guest exception telemetry, VBAR, SPSR,
                    # mode state, or the actual handler entry.
                    gdb = subprocess.run([
                        "gdb-multiarch", "-q", "--batch",
                        "-ex", "set architecture arm",
                        "-ex", f"target remote {gdb_sock}",
                        "-ex", f"set $pc = 0x{probe_addr:x}",
                        "-ex", "detach",
                    ], capture_output=True, text=True, timeout=12)
                    self.assertEqual(gdb.returncode, 0,
                                     f"failed to point real CPU at trap: {gdb.stdout} {gdb.stderr}")
                    if not qmp.command("query-status")["running"]:
                        qmp.hmp("cont")
                    until = time.monotonic() + 4
                    phase = None
                    while time.monotonic() < until:
                        if proc.poll() is not None:
                            self.fail(f"QEMU exited during exception: {proc.returncode}")
                        phase = qmp.word(self.syms["cp064_boot_phase"])
                        if phase == EXCEPTION:
                            break
                        time.sleep(0.025)
                    self.assertEqual(phase, EXCEPTION,
                                     f"actual guest exception did not reach fail-closed marker: {phase!r}")
                    qmp.hmp("stop")
                    self.assertEqual(qmp.word(self.syms["cp066_exception_kind"]),
                                     expected_kind)
                    self.assertEqual(qmp.word(self.syms["cp066_saved_lr"]),
                                     probe_addr + 4,
                                     "CPU did not populate architectural exception LR")
                    saved = qmp.word(self.syms["cp066_saved_spsr"])
                    self.assertEqual(saved & 0x1F, 0x13,
                                     "exception did not save pre-trap SVC-mode status")
                    self.assertEqual(qmp.word(self.syms["cp065_command_dispatch_count"]),
                                     0, "command dispatch occurred after fault")
                    regs = qmp.registers()
                    match = re.search(r"\bR15=([0-9a-fA-F]{8})", regs)
                    self.assertIsNotNone(match, regs)
                    self.assertIn(int(match.group(1), 16),
                                  (self.syms["cp064_halt"],
                                   self.syms["cp064_halt"] + 4),
                                  "guest PC is not in named fail-closed WFI halt")
                    print(f"CP006.6 trigger={trigger} kind={expected_kind} "
                          f"LR=0x{probe_addr+4:08x} saved_SPSR=0x{saved:08x} "
                          f"VBAR=0x{vector:08x}")
                else:
                    # The complete VBAR table is in guest executable RAM
                    # and contains eight 32-bit unconditional ARM branches.
                    qmp.hmp("stop")
                    for offset in range(0, 32, 4):
                        op = qmp.word(vector + offset)
                        self.assertEqual(op & 0xFF000000, 0xEA000000,
                                         f"vector +{offset:#x} is not an A32 B instruction")
                    self.assertEqual(qmp.word(self.syms["cp064_boot_phase"]), READY)
                    print(f"CP006.6 VBAR=0x{vector:08x} eight vectors linked; "
                          "IRQ/FIQ delivery still MASKED/UNVERIFIED")
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
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream:
                        stream.close()

    def test_guest_vbar_eight_vectors_and_unmodified_console_boot(self):
        self.with_guest()

    def test_actual_arm_svc_exception_records_cpu_lr_spsr_then_halts(self):
        self.with_guest("cp066_probe_svc", 2)

    def test_actual_arm_undefined_instruction_records_cpu_lr_spsr_then_halts(self):
        self.with_guest("cp066_probe_undefined", 1)

    def test_exception_stacks_fit_between_bss_and_main_stack(self):
        s = self.syms
        self.assertEqual(s["cp066_vector_table"] & 31, 0)
        self.assertGreaterEqual(s["cp066_vector_table"], s["__image_start"])
        self.assertLess(s["cp066_vector_table"], s["__image_end"])
        previous = s["__bss_end"]
        for name in ("und", "abt", "irq", "fiq"):
            low, high = s[f"__{name}_stack_bottom"], s[f"__{name}_stack_top"]
            self.assertGreaterEqual(low, previous)
            self.assertEqual(high - low, 1024)
            previous = high
        self.assertGreaterEqual(s["__stack_bottom"], previous)
        self.assertLess(s["__stack_bottom"], s["__image_end"])


if __name__ == "__main__":
    unittest.main()
