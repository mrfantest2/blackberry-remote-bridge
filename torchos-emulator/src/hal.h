/* QEMU ARM virt virtual HAL ONLY. No physical BlackBerry support. */
#ifndef TORCHOS_VIRTUAL_HAL_H
#define TORCHOS_VIRTUAL_HAL_H
int hal_init(void); /* fail closed on guest FDT / ELF memory mismatch */
int hal_uart_write(unsigned char byte); /* 0 on bounded stall / fault */
int hal_uart_read(void); /* -1 if RX empty, else byte */
int hal_failed(void);
const char *hal_machine_label(void);
#endif
