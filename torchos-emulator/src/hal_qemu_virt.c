/*
 * QEMU ARM 'virt' virtual PL011 UART backend ONLY.
 * This fixed address belongs to this emulator configuration.
 * A real target requires correct device-tree discovery and drivers.
 */
#include "hal.h"
#include <stdint.h>

#define PL011_DATA (*(volatile uint32_t *)(uintptr_t)0x09000000u)
#define PL011_FLAGS (*(volatile uint32_t *)(uintptr_t)0x09000018u)
#define PL011_TX_FULL (1u << 5)
#define PL011_RX_EMPTY (1u << 4)

void hal_uart_write(unsigned char byte) {
    while ((PL011_FLAGS & PL011_TX_FULL) != 0u) {
        /* Serial emulation is required for the QEMU smoke test. */
    }
    PL011_DATA = (uint32_t)byte;
}

int hal_uart_read(void) {
    if ((PL011_FLAGS & PL011_RX_EMPTY) != 0u) {
        return -1;
    }
    return (int)(PL011_DATA & 0xffu);
}

const char *hal_machine_label(void) {
    return "QEMU virt ARMv7 (simulated)";
}
