"""CP006.4 actual ARM guest boot fault injection using a QEMU generic loader.
No host-only parser substitute: assert in-guest phase, MMIO counters and PC.
Only disposable GitHub-hosted QEMU ARM virt is used. No physical devices.
"""
from pathlib import Path
import json
import re
import socket
import subprocess
import tempfile
import time
import unittest
from test_fdt_inventory import fixture
from fdt_fault_cases import bad_cases

ROOT = Path(__file__).resolve().parents[1]
ELF = ROOT / "build" / "torchos.elf"
MACHINE = "virt-8.2"
PHASE_REJECTED = 0x064BAD00
PHASE_READY = 0x06460003


def symbols():
    process = subprocess.run(
        ["arm-none-eabi-nm", "-n", str(ELF)], capture_output=True,
        text=True, timeout=20, check=True)
    mapping = {}
    for line in process.stdout.splitlines():
        match = re.match(r"^([0-9a-f]+) [A-Za-z] ([A-Za-z_][A-Za-z_0-9]*)$", line)
        if match:
            mapping[match.group(2)] = int(match.group(1), 16)
    for k in ("cp064_boot_phase", "cp064_mmio_reads",
              "cp064_mmio_writes", "cp064_halt"):
        if k not in mapping:
            raise AssertionError(f"instrumentation symbol absent: {k}")
    return mapping


class Qmp:
    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX)
        deadline = time.monotonic() + 3
        while True:
            try:
                self.sock.connect(str(path))
                break
            except (OSError, ConnectionRefusedError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.02)
        self.sock.settimeout(3)
        self.reader = self.sock.makefile("rb")
        hello = self.read()
        assert "QMP" in hello, hello
        self.command("qmp_capabilities")

    def read(self):
        while True:
            line = self.reader.readline()
            if not line:
                raise AssertionError("QMP disconnected")
            event = json.loads(line)
            if "event" not in event:
                return event

    def command(self, name, arguments=None):
        obj = {"execute": name}
        if arguments:
            obj["arguments"] = arguments
        self.sock.sendall((json.dumps(obj) + "\r\n").encode())
        result = self.read()
        if "error" in result:
            raise AssertionError(result["error"])
        return result.get("return", "")

    def hmp(self, command):
        return str(self.command("human-monitor-command",
                                {"command-line": command}))

    def word(self, addr):
        output = self.hmp(f"xp /1wx 0x{addr:x}")
        found = re.search(r":\s+0x([0-9a-fA-F]+)", output)
        if not found:
            raise AssertionError(f"No RAM word at 0x{addr:x}: {output}")
        return int(found.group(1), 16)

    def registers(self):
        return self.hmp("info registers")

    def close(self):
        self.reader.close()
        self.sock.close()


class ActualGuestFaults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sym = symbols()

    def boot(self, blob, accepted):
        """Inject a synthetic FDT over QEMU's DTB, verify actual guest state."""
        with tempfile.TemporaryDirectory(prefix="torch-cp064-") as tmp:
            folder = Path(tmp)
            dtb = folder / "injected.dtb"
            dtb.write_bytes(blob)
            sock = folder / "qmp.sock"
            cmd = [
                "qemu-system-arm", "-machine", MACHINE, "-cpu", "cortex-a15",
                "-m", "128M", "-display", "none", "-monitor", "none",
                "-nic", "none", "-serial", "stdio", "-no-reboot",
                "-kernel", str(ELF), "-S",
                "-chardev", f"socket,path={folder / 'gdb.sock'},server=on,wait=off,id=gdb0",
                "-gdb", "chardev:gdb0",
                "-qmp", f"unix:{sock},server=on,wait=off",
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            client = None
            try:
                try:
                    client = Qmp(sock)
                except (OSError, AssertionError) as exc:
                    if proc.poll() is None:
                        proc.terminate()
                    out, err = proc.communicate(timeout=3)
                    self.fail(f"QEMU/QMP initialization failed: {exc}; stdout={out!r}; stderr={err!r}; command={cmd!r}")
                # Pause before the first ARM instruction, write to real
                # guest RAM, and independently read back exact DTB bytes.
                restored = folder / "readback.dtb"
                gdb = subprocess.run([
                    "gdb-multiarch", "-q", "--batch",
                    "-ex", f"target remote {folder / 'gdb.sock'}",
                    "-ex", f"restore {dtb} binary 0x40000000",
                    "-ex", f"dump binary memory {restored} 0x40000000 0x{0x40000000 + len(blob):x}",
                    "-ex", "disconnect",
                ], text=True, capture_output=True, timeout=10)
                self.assertEqual(gdb.returncode, 0,
                                 f"GDB injection failed: {gdb.stdout} {gdb.stderr}")
                self.assertEqual(restored.read_bytes(), blob,
                                 "DTB readback differs from injected guest RAM")
                client.hmp("cont")
                deadline = time.monotonic() + 3
                phase = None
                while time.monotonic() < deadline:
                    if proc.poll() is not None:
                        out, err = proc.communicate(timeout=1)
                        self.fail(f"QEMU died before guest initialized: {out!r} {err!r}")
                    phase = client.word(self.sym["cp064_boot_phase"])
                    if phase in (PHASE_READY, PHASE_REJECTED):
                        break
                    time.sleep(0.03)
                expected = PHASE_READY if accepted else PHASE_REJECTED
                self.assertEqual(phase, expected, f"guest phase {phase:#x}")
                client.hmp("stop")
                read_count = client.word(self.sym["cp064_mmio_reads"])
                write_count = client.word(self.sym["cp064_mmio_writes"])
                regs = client.registers()
                if accepted:
                    self.assertGreater(read_count, 0)
                    self.assertGreater(write_count, 0)
                    self.assertIn("R15=", regs)
                else:
                    self.assertEqual(read_count, 0, "invalid DTB accessed MMIO")
                    self.assertEqual(write_count, 0, "invalid DTB transmitted")
                    match = re.search(r"\bR15=([0-9a-fA-F]{8})", regs)
                    self.assertIsNotNone(match, regs)
                    pc = int(match.group(1), 16)
                    self.assertIn(pc, (self.sym["cp064_halt"],
                                       self.sym["cp064_halt"] + 4),
                                  f"guest not in named fail-closed WFI: PC {pc:#x}")
                return read_count, write_count
            finally:
                if client:
                    client.close()
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=2)
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()

    def test_valid_synthetic_dtb_is_really_loaded_into_guest(self):
        # This is proof that QEMU raw loader puts supplied blob where
        # the bare-metal ARM image expects it; no host-parser-only pass.
        self.boot(fixture(), True)

    def test_bad_magic_fails_in_actual_guest_before_mmio(self):
        raw = b"\0\0\0\0" + fixture()[4:]
        self.boot(raw, False)


# Generate individual named unittest methods so GitHub Actions reports
# exact case counts, not a single passing outer loop or silent skips.
def _make_negative_case(image):
    def test(self):
        self.boot(image, False)
    return test

for _case_name, _image in sorted(bad_cases().items()):
    setattr(ActualGuestFaults, "test_fault_" + _case_name,
            _make_negative_case(_image))

if __name__ == "__main__":
    unittest.main()
