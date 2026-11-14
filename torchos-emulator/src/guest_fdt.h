/* CP006.3: bounded read-only flattened-device-tree parser, QEMU ARM virt only. */
#ifndef TORCHOS_GUEST_FDT_H
#define TORCHOS_GUEST_FDT_H
#include <stddef.h>
#include <stdint.h>
#define GUEST_FDT_LIMIT (1024u * 1024u)
struct guest_fdt_devices {
    uintptr_t uart_address;
    uint32_t uart_size;
    uintptr_t ram_address;
    uint32_t ram_size;
};
/* Never performs MMIO; returns 0 and clears output on any invalid DTB. */
int guest_fdt_parse(const void *dtb, size_t accessible_bytes,
                    struct guest_fdt_devices *out);
#endif
