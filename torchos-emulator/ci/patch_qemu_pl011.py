#!/usr/bin/env python3
"""Temporarily instrument the official QEMU v8.2.2 PL011 read handler.

This changes a disposable QEMU process, NEVER the TorchOS guest. This is an
instrumented device test and NOT the behavior of unmodified upstream QEMU.
"""
import pathlib
import sys

BEFORE = """    case 6: /* UARTFR */
        r = s->flags;
        break;"""
AFTER = """    case 6: /* UARTFR */
        r = s->flags;
        /* CP006.5 TEST-ONLY: genuine PL011 register MMIO will return TXFF. */
        if (g_getenv("TORCHOS_QEMU_FORCE_PL011_TXFF") != NULL) {
            static bool first_report = true;
            r |= PL011_FLAG_TXFF;
            if (first_report) {
                fprintf(stderr, "TORCHOS_PL011_TXFF_INJECTED\\n");
                first_report = false;
            }
        }
        break;"""

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_qemu_pl011.py <qemu-8.2.2/hw/char/pl011.c>")
    target = pathlib.Path(sys.argv[1])
    source = target.read_text()
    if source.count(BEFORE) != 1 or source.count("PL011_FLAG_TXFF") != 2:
        raise SystemExit("FAIL CLOSED: unexpected v8.2.2 PL011 source")
    patched = source.replace(BEFORE, AFTER)
    if patched.count("TORCHOS_PL011_TXFF_INJECTED") != 1:
        raise SystemExit("FAIL CLOSED: patch not uniquely applied")
    target.write_text(patched)
    print("TEST-ONLY QEMU PL011 UARTFR injection applied; original guest preserved.")

if __name__ == "__main__":
    main()
