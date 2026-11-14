/* CP006.6: QEMU ARM exception vectors and original lightweight console.
 * CPU IRQ/FIQ remain masked; no physical BlackBerry driver or GIC code.
 */
#include "hal.h"
#include "console.h"
#include "commands.h"
#include "boot_state.h"
#include <stdint.h>
volatile uint32_t cp064_boot_phase;
volatile uint32_t cp064_mmio_reads;
volatile uint32_t cp064_mmio_writes;
volatile uint32_t cp066_vbar_readback;
volatile uint32_t cp066_exception_kind;
volatile uint32_t cp066_saved_lr;
volatile uint32_t cp066_saved_spsr;
static void halt_with(uint32_t phase) __attribute__((noreturn));
static void halt_with(uint32_t phase) {
    cp064_boot_phase = phase;
    cp064_halt();
}
void kmain(void) {
    cp064_boot_phase = BOOT_PARSING;
    if (!hal_init()) halt_with(BOOT_REJECTED);
    cp064_boot_phase = BOOT_HAL_READY;
    console_init(hal_uart_write, commands_execute);
    commands_init(console_putc, hal_machine_label);
    console_puts("\nTorchOS CP005 — Independent ARM Research Boot\n");
    console_puts("QEMU VIRTUAL MACHINE ONLY — NOT BLACKBERRY HARDWARE\n");
    console_puts("No firmware, phone access, filesystem, network or remote commands.\n");
    console_puts("Type help to see local commands.\n");
    console_start();
    if (console_faulted() || hal_failed()) halt_with(BOOT_UART_FAILED);
    cp064_boot_phase = BOOT_CONSOLE_READY;
    for (;;) {
        int c = hal_uart_read();
        if (hal_failed()) halt_with(BOOT_UART_FAILED);
        if (c >= 0) console_feed(c);
        if (console_faulted()) halt_with(BOOT_UART_FAILED);
    }
}
