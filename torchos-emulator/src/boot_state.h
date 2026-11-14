/* Observability in QEMU via read-only monitor memory, never MMIO.
 * These markers are test evidence, not a real firmware debug service.
 */
#ifndef TORCHOS_BOOT_STATE_H
#define TORCHOS_BOOT_STATE_H
#include <stdint.h>
#define BOOT_PARSING 0x06410001u
#define BOOT_REJECTED 0x064bad00u
#define BOOT_HAL_READY 0x06460002u
#define BOOT_CONSOLE_READY 0x06460003u
#define BOOT_UART_FAILED 0x064bad11u
extern volatile uint32_t cp064_boot_phase;
extern volatile uint32_t cp064_mmio_reads;
extern volatile uint32_t cp064_mmio_writes;
void cp064_halt(void) __attribute__((noreturn));
#endif
