"""Bounded, host-side Flattened Device Tree inspector for QEMU virt only.

Not a BlackBerry bootloader, a guest driver, or a source of physical-device IDs.
Designed to reject malformed blobs instead of guessing register addresses.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

MAGIC = 0xD00DFEED
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9
MAX_DTB_BYTES = 1024 * 1024
MAX_NODES = 2048
MAX_DEPTH = 32
MAX_PROPS = 8192
MAX_PROPERTY_BYTES = 128 * 1024


class DeviceTreeError(ValueError):
    """Malformed or unsupported device tree."""


def _align4(value: int) -> int:
    return (value + 3) & ~3


def _u32(data: bytes, offset: int, end: int) -> int:
    if offset < 0 or offset + 4 > end:
        raise DeviceTreeError("truncated 32-bit field")
    return struct.unpack_from(">I", data, offset)[0]


def _cells(raw: bytes, count: int) -> int:
    if count not in (1, 2) or len(raw) != 4 * count:
        raise DeviceTreeError("unsupported or malformed address cells")
    v = 0
    for off in range(0, len(raw), 4):
        v = (v << 32) | struct.unpack_from(">I", raw, off)[0]
    return v


def parse_dtb(data: bytes) -> dict:
    if not isinstance(data, bytes) or len(data) < 40:
        raise DeviceTreeError("DTB header missing")
    if len(data) > MAX_DTB_BYTES:
        raise DeviceTreeError("DTB exceeds 1 MiB safety limit")

    (
        magic, total, struct_off, strings_off, reserve_off,
        version, last_compatible, _cpu, strings_size, struct_size,
    ) = struct.unpack_from(">10I", data, 0)
    if magic != MAGIC:
        raise DeviceTreeError("bad FDT magic")
    if total != len(data) or total > MAX_DTB_BYTES:
        raise DeviceTreeError("FDT length mismatch")
    if version < 17 or last_compatible > version:
        raise DeviceTreeError("unsupported FDT header version")
    if struct_off % 4 or strings_off % 4 or reserve_off % 8:
        raise DeviceTreeError("misaligned section")
    if (
        struct_off < 40 or strings_off < 40 or reserve_off < 40
        or struct_size < 8 or strings_size < 1
        or struct_off + struct_size > total
        or strings_off + strings_size > total
        or reserve_off + 16 > total
    ):
        raise DeviceTreeError("invalid FDT section bounds")
    # Do not accept overlapping string / structure data or arbitrary offsets.
    if max(struct_off, strings_off) < min(struct_off + struct_size, strings_off + strings_size):
        raise DeviceTreeError("overlapping FDT sections")

    strings = data[strings_off:strings_off + strings_size]
    pos = struct_off
    limit = struct_off + struct_size
    stack: list[str] = []
    nodes: dict[str, dict[str, bytes]] = {}
    properties = 0
    done = False

    while pos < limit:
        tag = _u32(data, pos, limit)
        pos += 4
        if tag == BEGIN_NODE:
            end = data.find(b"\0", pos, limit)
            if end == -1:
                raise DeviceTreeError("unterminated node name")
            try:
                name = data[pos:end].decode("ascii")
            except UnicodeDecodeError as exc:
                raise DeviceTreeError("invalid node name encoding") from exc
            if len(name) > 255 or "/" in name or not (stack or name == ""):
                raise DeviceTreeError("invalid node name")
            if len(stack) >= MAX_DEPTH or len(nodes) >= MAX_NODES:
                raise DeviceTreeError("too many FDT nodes/depth")
            path = "/" if not stack else stack[-1].rstrip("/") + "/" + name
            if path in nodes:
                raise DeviceTreeError("duplicate FDT path")
            nodes[path] = {}
            stack.append(path)
            pos = _align4(end + 1)
            if pos > limit:
                raise DeviceTreeError("node name exceeds FDT section")
        elif tag == END_NODE:
            if not stack:
                raise DeviceTreeError("unbalanced node end")
            stack.pop()
        elif tag == PROP:
            if not stack or pos + 8 > limit:
                raise DeviceTreeError("invalid FDT property header")
            length, name_off = struct.unpack_from(">2I", data, pos)
            pos += 8
            if length > MAX_PROPERTY_BYTES or pos + length > limit or name_off >= len(strings):
                raise DeviceTreeError("invalid FDT property bounds")
            name_end = strings.find(b"\0", name_off)
            if name_end < 0:
                raise DeviceTreeError("unterminated property name")
            try:
                name = strings[name_off:name_end].decode("ascii")
            except UnicodeDecodeError as exc:
                raise DeviceTreeError("invalid property name encoding") from exc
            if not name or len(name) > 127 or name in nodes[stack[-1]]:
                raise DeviceTreeError("invalid or duplicate property name")
            properties += 1
            if properties > MAX_PROPS:
                raise DeviceTreeError("too many FDT properties")
            nodes[stack[-1]][name] = data[pos:pos + length]
            pos = _align4(pos + length)
            if pos > limit:
                raise DeviceTreeError("property alignment outside section")
        elif tag == NOP:
            continue
        elif tag == END:
            if stack or not nodes or pos != limit:
                raise DeviceTreeError("unfinished or extra FDT structure")
            done = True
            break
        else:
            raise DeviceTreeError("unknown FDT token")

    if not done or "/" not in nodes:
        raise DeviceTreeError("missing FDT_END or root")

    def cell_setting(name: str, default: int) -> int:
        value = nodes["/"].get(name)
        if value is None:
            return default
        if len(value) != 4:
            raise DeviceTreeError("malformed root " + name)
        n = _u32(value, 0, len(value))
        if n not in (1, 2):
            raise DeviceTreeError("unsupported root " + name)
        return n

    address_cells = cell_setting("#address-cells", 2)
    size_cells = cell_setting("#size-cells", 1)

    def ranges_of(raw: bytes) -> list[dict]:
        stride = 4 * (address_cells + size_cells)
        if not raw or len(raw) % stride:
            raise DeviceTreeError("malformed memory/peripheral reg")
        ranges = []
        for off in range(0, len(raw), stride):
            addr_end = off + address_cells * 4
            base = _cells(raw[off:addr_end], address_cells)
            extent = _cells(raw[addr_end:off + stride], size_cells)
            if extent < 1:
                raise DeviceTreeError("zero-sized register region")
            ranges.append({"base": "0x%x" % base, "size_bytes": extent})
        return ranges

    pl011 = []
    memory = []
    for path, props in nodes.items():
        compat = [p for p in props.get("compatible", b"").split(b"\0") if p]
        device_type = props.get("device_type", b"").split(b"\0", 1)[0]
        # A disabled device must not be advertised as an active UART.
        status = props.get("status", b"okay").split(b"\0", 1)[0]
        if b"arm,pl011" in compat and status in (b"ok", b"okay"):
            reg = props.get("reg")
            if reg is None:
                raise DeviceTreeError("PL011 missing reg property")
            pl011.append({"node": path, "registers": ranges_of(reg)})
        if device_type == b"memory":
            reg = props.get("reg")
            if reg is None:
                raise DeviceTreeError("memory missing reg property")
            memory.extend(ranges_of(reg))

    if not pl011:
        raise DeviceTreeError("no enabled PL011 found")
    if not memory:
        raise DeviceTreeError("no memory node found")

    return {
        "source": "QEMU-generated virtual device tree, host-side analysis only",
        "physical_blackberry_support": "NOT VERIFIED",
        "fdt_version": version,
        "root_address_cells": address_cells,
        "root_size_cells": size_cells,
        "uart_pl011": pl011,
        "virtual_memory": memory,
        "virtual_nodes_checked": len(nodes),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: fdt_inventory.py <QEMU-generated-virt.dtb>", file=sys.stderr)
        return 2
    try:
        path = Path(argv[0])
        if path.stat().st_size > MAX_DTB_BYTES:
            raise DeviceTreeError("DTB exceeds 1 MiB safety limit")
        report = parse_dtb(path.read_bytes())
    except (OSError, DeviceTreeError) as exc:
        print("FDT inspection rejected: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
