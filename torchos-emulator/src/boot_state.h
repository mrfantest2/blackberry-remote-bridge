/* QEMU-only guest telemetry; read-only from QMP/GDB. */
#ifndef TORCHOS_BOOT_STATE_H
#define TORCHOS_BOOT_STATE_H
#include <stdint.h>
#define BOOT_PARSING 0x06410001u
#define BOOT_REJECTED 0x064bad00u
#define BOOT_HAL_READY 0x06460002u
#define BOOT_CONSOLE_READY 0x06460003u
#define BOOT_UART_FAILED 0x064bad11u
#define BOOT_EXCEPTION_FAILED 0x066bad00u
#define CP066_UNDEFINED 1u
#define CP066_SVC 2u
#define CP066_PREFETCH_ABORT 3u
#define CP066_DATA_ABORT 4u
#define CP066_IRQ 5u
#define CP066_FIQ 6u
extern volatile uint32_t cp064_boot_phase;
extern volatile uint32_t cp064_mmio_reads;
extern volatile uint32_t cp064_mmio_writes;
extern volatile uint32_t cp066_vbar_readback;
extern volatile uint32_t cp066_exception_kind;
extern volatile uint32_t cp066_saved_lr;
extern volatile uint32_t cp066_saved_spsr;
/* QEMU GICv2 debug-only probe; not accessed on normal boot. */
extern volatile uint32_t cp066_gic_dist_readback;
extern volatile uint32_t cp066_gic_cpu_readback;
extern volatile uint32_t cp066_gic_pmr_readback;
void cp064_halt(void) __attribute__((noreturn));
#endif
