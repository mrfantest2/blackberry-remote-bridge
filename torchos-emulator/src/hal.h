/* QEMU ARM virt virtual HAL only; not compatible with BlackBerry firmware. */
#ifndef TORCHOS_VIRTUAL_HAL_H
#define TORCHOS_VIRTUAL_HAL_H
int hal_init(void); /* validate guest FDT before UART MMIO; fail closed */
void hal_uart_write(unsigned char byte);
int hal_uart_read(void);
const char *hal_machine_label(void);
#endif
