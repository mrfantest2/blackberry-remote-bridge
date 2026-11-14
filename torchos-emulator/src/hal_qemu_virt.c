/* QEMU ARM virt ONLY: validate guest FDT before MMIO; no fallback.
 * This backend is not compatible with BlackBerry hardware or firmware.
 */
#include "hal.h"
#include "guest_fdt.h"
#include <stdint.h>
#define QEMU_VIRT_RAM_START ((uintptr_t)0x40000000u)
#define PL011_DATA_OFFSET ((uintptr_t)0x00u)
#define PL011_FLAGS_OFFSET ((uintptr_t)0x18u)
#define PL011_TX_FULL (1u << 5)
#define PL011_RX_EMPTY (1u << 4)
static uintptr_t uart_mmio_base;

int hal_init(void) {
    struct guest_fdt_devices devices;
    uart_mmio_base = 0u;
    if (!guest_fdt_parse((const void *)QEMU_VIRT_RAM_START,
                         GUEST_FDT_LIMIT, &devices)) return 0;
    uart_mmio_base = devices.uart_address;
    return 1;
}
static volatile uint32_t *uart_register(uintptr_t offset) {
    return (volatile uint32_t *)(uart_mmio_base + offset);
}
void hal_uart_write(unsigned char byte) {
    if (uart_mmio_base == 0u) return;
    while ((*uart_register(PL011_FLAGS_OFFSET) & PL011_TX_FULL) != 0u) { }
    *uart_register(PL011_DATA_OFFSET) = (uint32_t)byte;
}
int hal_uart_read(void) {
    if (uart_mmio_base == 0u ||
        (*uart_register(PL011_FLAGS_OFFSET) & PL011_RX_EMPTY) != 0u) return -1;
    return (int)(*uart_register(PL011_DATA_OFFSET) & 0xffu);
}
const char *hal_machine_label(void) {
    return "QEMU virt ARMv7 (guest FDT validated, simulated)";
}
