/* Freestanding, mockable PL011 polling. No MMIO access unless bus is ready. */
#ifndef TORCHOS_UART_POLL_H
#define TORCHOS_UART_POLL_H
#include <stdint.h>
typedef uint32_t (*uart_read32)(void *, uint32_t);
typedef void (*uart_write32)(void *, uint32_t, uint32_t);
struct uart_poll_bus {
    void *ctx;
    uart_read32 read32;
    uart_write32 write32;
    unsigned ready;
};
/* Returns 1 only if TX accepted within budget; never loops without bound. */
int uart_poll_send(const struct uart_poll_bus *bus, uint8_t value, unsigned budget);
int uart_poll_receive(const struct uart_poll_bus *bus); /* -1 when RX empty/disabled */
#endif
