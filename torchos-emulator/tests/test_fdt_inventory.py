"""Check CP006.2 FDT validity and QEMU-generated hardware claims; no devices."""
import importlib.util
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "fdt_inventory.py"
spec = importlib.util.spec_from_file_location("fdt_inventory", SCRIPT)
fdt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fdt)


def fixture(*, uart=True, memory=True):
    """Create a minimal valid FDT with a standard ten-word header."""
    string_table = b"#address-cells\0#size-cells\0compatible\0reg\0device_type\0"
    strings = {
        name: string_table.index(name.encode("ascii") + b"\0")
        for name in ("#address-cells", "#size-cells", "compatible", "reg", "device_type")
    }
    tokens = bytearray()

    def word(n):
        tokens.extend(struct.pack(">I", n))

    def aligned(data):
        tokens.extend(data)
        tokens.extend(b"\0" * (-len(tokens) % 4))

    def begin(name):
        word(1)
        aligned(name.encode() + b"\0")

    def end():
        word(2)

    def prop(name, value):
        word(3)
        word(len(value))
        word(strings[name])
        aligned(value)

    def reg(address, size):
        return struct.pack(">4I", address >> 32, address & 0xffffffff, size >> 32, size & 0xffffffff)

    begin("")
    prop("#address-cells", struct.pack(">I", 2))
    prop("#size-cells", struct.pack(">I", 2))
    if uart:
        begin("pl011@9000000")
        prop("compatible", b"arm,pl011\0arm,primecell\0")
        prop("reg", reg(0x09000000, 4096))
        end()
    if memory:
        begin("memory@40000000")
        prop("device_type", b"memory\0")
        prop("reg", reg(0x40000000, 128 * 1024 * 1024))
        end()
    end()
    word(9)

    reserve_off = 40
    struct_off = reserve_off + 16
    strings_off = struct_off + len(tokens)
    total = strings_off + len(string_table)
    header = struct.pack(">10I", 0xD00DFEED, total, struct_off, strings_off, reserve_off, 17, 16, 0,
                         len(string_table), len(tokens))
    return header + b"\0" * 16 + bytes(tokens) + string_table


class FdtNegativeTests(unittest.TestCase):
    def test_valid_fixture(self):
        result = fdt.parse_dtb(fixture())
        self.assertEqual(result["uart_pl011"][0]["registers"][0]["base"], "0x9000000")
        self.assertEqual(result["virtual_memory"][0]["size_bytes"], 128 * 1024 * 1024)
        self.assertEqual(result["physical_blackberry_support"], "NOT VERIFIED")

    def test_bad_magic_is_rejected(self):
        raw = b"\0\0\0\0" + fixture()[4:]
        with self.assertRaisesRegex(fdt.DeviceTreeError, "magic"):
            fdt.parse_dtb(raw)

    def test_truncated_blob_is_rejected(self):
        with self.assertRaisesRegex(fdt.DeviceTreeError, "length mismatch"):
            fdt.parse_dtb(fixture()[:-3])

    def test_oversized_blob_is_rejected(self):
        with self.assertRaisesRegex(fdt.DeviceTreeError, "1 MiB"):
            fdt.parse_dtb(fixture() + b"!" * (fdt.MAX_DTB_BYTES + 1))

    def test_bad_string_offset_is_rejected(self):
        raw = bytearray(fixture())
        struct_off = struct.unpack_from(">I", raw, 8)[0]
        pos = struct_off
        # BEGIN_NODE token and aligned empty name => first property is 8 bytes in.
        first_prop_name_offset = pos + 8 + 8
        struct.pack_into(">I", raw, first_prop_name_offset, 0xFFFFFFFF)
        with self.assertRaisesRegex(fdt.DeviceTreeError, "property bounds"):
            fdt.parse_dtb(bytes(raw))

    def test_no_uart_is_rejected(self):
        with self.assertRaisesRegex(fdt.DeviceTreeError, "PL011"):
            fdt.parse_dtb(fixture(uart=False))

    def test_no_ram_is_rejected(self):
        with self.assertRaisesRegex(fdt.DeviceTreeError, "memory"):
            fdt.parse_dtb(fixture(memory=False))

    def test_overlapping_sections_are_rejected(self):
        raw = bytearray(fixture())
        struct_off = struct.unpack_from(">I", raw, 8)[0]
        struct.pack_into(">I", raw, 12, struct_off + 4)  # strings offset
        with self.assertRaises(fdt.DeviceTreeError):
            fdt.parse_dtb(bytes(raw))


class ActualQemuDeviceTree(unittest.TestCase):
    """Generate the real QEMU virt DTB, not a simulated static fixture."""

    def test_virtual_dtb_inventory_matches_console_hal(self):
        with tempfile.TemporaryDirectory(prefix="torchos-cp0062-") as folder:
            image = Path(folder) / "virt.dtb"
            command = [
                "qemu-system-arm", "-machine", f"virt-8.2,dumpdtb={image}",
                "-cpu", "cortex-a15", "-m", "128M", "-nic", "none",
                "-display", "none", "-monitor", "none", "-serial", "none",
            ]
            result = subprocess.run(command, text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(image.is_file(), "QEMU did not produce the requested DTB")
            inv = fdt.parse_dtb(image.read_bytes())
            addresses = [reg["base"] for uart in inv["uart_pl011"] for reg in uart["registers"]]
            self.assertIn("0x9000000", addresses, "Current QEMU-only virtual HAL disagrees with DTB")
            self.assertTrue(any(r["size_bytes"] == 128 * 1024 * 1024 for r in inv["virtual_memory"]))
            self.assertGreater(inv["virtual_nodes_checked"], 3)
            self.assertEqual(inv["physical_blackberry_support"], "NOT VERIFIED")
            print("Generated QEMU virt DTB, validated UART and RAM:", addresses)


if __name__ == "__main__":
    unittest.main()
