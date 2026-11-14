"""Deterministic, synthetic QEMU-only FDT fault fixtures. No handset data."""
import struct
from test_fdt_inventory import fixture

def _pack_u32(v): return struct.pack(">I", v)
def _reg(addr, size):
    return struct.pack(">4I", addr >> 32, addr & 0xffffffff,
                       size >> 32, size & 0xffffffff)

def build(uarts=((0x09000000, 4096, None),),
          memory=((0x40000000, 128 * 1024 * 1024),),
          cells=(2, 2), depth=0, reserved=False, reserved_node=False):
    names = ("#address-cells", "#size-cells", "compatible", "reg", "device_type", "status")
    strtab = b""
    offsets = {}
    for name in names:
        offsets[name] = len(strtab)
        strtab += name.encode() + b"\0"
    buf = bytearray()
    def tok(n): buf.extend(_pack_u32(n))
    def aligned(data):
        buf.extend(data)
        buf.extend(b"\0" * (-len(buf) % 4))
    def begin(name):
        tok(1)
        aligned(name.encode() + b"\0")
    def end(): tok(2)
    def prop(name, value):
        tok(3)
        tok(len(value))
        tok(offsets[name])
        aligned(value)
    begin("")
    prop("#address-cells", _pack_u32(cells[0]))
    prop("#size-cells", _pack_u32(cells[1]))
    for i, (addr, size, status) in enumerate(uarts):
        begin(f"pl011{i}@{addr:x}")
        prop("compatible", b"arm,pl011\0arm,primecell\0")
        prop("reg", _reg(addr, size))
        if status is not None:
            prop("status", status.encode() + b"\0")
        end()
    for i, (addr, size) in enumerate(memory):
        begin(f"memory{i}@{addr:x}")
        prop("device_type", b"memory\0")
        prop("reg", _reg(addr, size))
        end()
    if reserved_node:
        begin("reserved-memory")
        end()
    for i in range(depth): begin(f"nested{i}")
    for i in range(depth): end()
    end()
    tok(9)
    reserve = (struct.pack(">4I", 0, 0x40002000, 0, 0x1000)
               if reserved else b"") + b"\0" * 16
    reserve_offset = 40
    structure_offset = reserve_offset + len(reserve)
    strings_offset = structure_offset + len(buf)
    total = strings_offset + len(strtab)
    header = struct.pack(">10I", 0xd00dfeed, total, structure_offset,
                         strings_offset, reserve_offset, 17, 16, 0,
                         len(strtab), len(buf))
    return header + reserve + bytes(buf) + strtab

def header32(blob, offset, value):
    raw = bytearray(blob)
    struct.pack_into(">I", raw, offset, value)
    return bytes(raw)

def bad_cases():
    source = fixture()
    replaced = source.replace(_reg(0x09000000, 4096), _reg(0x40000000, 4096))
    assert replaced != source
    crossing = build(uarts=((0x0ffff000, 8192, None),))
    invalid_prop = bytearray(source)
    pos = source.find(_reg(0x09000000, 4096))
    assert pos > 8
    # PL011 'reg' value is immediately after length/name offset fields.
    struct.pack_into(">I", invalid_prop, pos - 8, 0x20000)
    return {
        "bad_magic": b"\0\0\0\0" + source[4:],
        "truncated_declared_total": header32(source, 4, len(source) - 8),
        "oversized_declared_dtb": header32(source, 4, 1024 * 1024 + 1),
        "missing_uart": build(uarts=()),
        "missing_ram": build(memory=()),
        "uart_inside_ram": replaced,
        "uart_crosses_mmio_end": crossing,
        "duplicate_uart": build(uarts=((0x09000000, 4096, None),
                                       (0x09001000, 4096, None))),
        "disabled_uart": build(uarts=((0x09000000, 4096, "disabled"),)),
        "invalid_root_address_cells": build(cells=(1, 2)),
        "invalid_root_size_cells": build(cells=(2, 1)),
        "malformed_structure_offset": header32(source, 8, 0xfffffff0),
        "malformed_string_offset": header32(source, 12, 0xfffffff0),
        "invalid_property_length": bytes(invalid_prop),
        "excessive_node_depth": build(depth=33),
        "unsupported_memory_size": build(memory=((0x40000000, 64 * 1024 * 1024),)),
        "unsupported_memory_origin": build(memory=((0x41000000, 128 * 1024 * 1024),)),
        "unsupported_address_width": build(uarts=((0x109000000, 4096, None),)),
        "reserved_memory_map": build(reserved=True),
        "reserved_memory_node": build(reserved_node=True),
    }
