#include "uart_poll.h"
#define PL011_DR 0u
#define PL011_FR 0x18u
#define PL011_TXFF (1u << 5)
#define PL011_RXFE (1u << 4)
int uart_poll_send(const struct uart_poll_bus *bus, uint8_t value, unsigned budget) {
    unsigned i;
    if (!bus || !bus->ready || !bus->read32 || !bus->write32) return 0;
    for (i = 0u; i < budget; ++i) {
        if ((bus->read32(bus->ctx, PL011_FR) & PL011_TXFF) == 0u) {
            bus->write32(bus->ctx, PL011_DR, value);
            return 1;
        }
    }
    return 0;
}
int uart_poll_receive(const struct uart_poll_bus *bus) {
    if (!bus || !bus->ready || !bus->read32) return -1;
    if ((bus->read32(bus->ctx, PL011_FR) & PL011_RXFE) != 0u) return -1;
    return (int)(bus->read32(bus->ctx, PL011_DR) & 255u);
}
