/* QEMU ARM virt virtual UART only: bounded and FDT-selected MMIO. */
#include "hal.h"
#include "uart_poll.h"
#include "guest_fdt.h"
#include "boot_state.h"
#include <stdint.h>
#define VIRT_RAM ((uintptr_t)0x40000000u)
#define VIRT_RAM_SIZE ((uint32_t)0x08000000u)
#define FDT_RESERVED_END ((uintptr_t)0x40100000u)
#define UART_TX_BUDGET 65536u
static struct uart_poll_bus port;
static uintptr_t uart_base;
static unsigned fault;
extern char __image_start[], __image_end[], __bss_start[], __bss_end[];
extern char __stack_bottom[], __stack_top[];

static uint32_t mmio_read(void *ctx, uint32_t offset) {
    uintptr_t base = *(const uintptr_t *)ctx;
    ++cp064_mmio_reads;
    return *(volatile uint32_t *)(base + offset);
}
static void mmio_write(void *ctx, uint32_t offset, uint32_t value) {
    uintptr_t base = *(const uintptr_t *)ctx;
    ++cp064_mmio_writes;
    *(volatile uint32_t *)(base + offset) = value;
}
int hal_init(void) {
    struct guest_fdt_devices d;
    uintptr_t elf_start = (uintptr_t)__image_start;
    uintptr_t elf_end = (uintptr_t)__image_end;
    uintptr_t bss_start = (uintptr_t)__bss_start, bss_end = (uintptr_t)__bss_end;
    uintptr_t stack_low = (uintptr_t)__stack_bottom, stack_high = (uintptr_t)__stack_top;
    port.ready = 0u;
    uart_base = 0u;
    fault = 0u;
    if (!guest_fdt_parse((const void *)VIRT_RAM, GUEST_FDT_LIMIT, &d)) return 0;
    if (d.ram_address != VIRT_RAM || d.ram_size != VIRT_RAM_SIZE) return 0;
    if (elf_start < FDT_RESERVED_END || elf_start >= elf_end ||
        elf_end > VIRT_RAM + VIRT_RAM_SIZE ||
        bss_start < elf_start || bss_start >= bss_end || bss_end > elf_end ||
        stack_low < bss_end || stack_low >= stack_high || stack_high > elf_end) return 0;
    if (d.uart_address < 0x08000000u || d.uart_address >= 0x10000000u ||
        d.uart_size < 0x1000u || d.uart_size > 0x08000000u ||
        d.uart_address > 0x10000000u - d.uart_size) return 0;
    uart_base = d.uart_address;
    port.ctx = &uart_base;
    port.read32 = mmio_read;
    port.write32 = mmio_write;
    port.ready = 1u;
    return 1;
}
int hal_uart_write(unsigned char byte) {
    if (fault || !port.ready) return 0;
    if (!uart_poll_send(&port, byte, UART_TX_BUDGET)) {
        fault = 1u;
        port.ready = 0u;
        return 0;
    }
    return 1;
}
int hal_uart_read(void) {
    if (fault || !port.ready) return -1;
    return uart_poll_receive(&port);
}
int hal_failed(void) { return fault != 0u; }
const char *hal_machine_label(void) {
    return "QEMU virt ARMv7 (guest FDT validated, simulated)";
}
