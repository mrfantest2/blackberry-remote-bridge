/* CP006 virtual hardware abstraction.
 * Backends must never touch the real BlackBerry.
 */
#ifndef TORCHOS_VIRTUAL_HAL_H
#define TORCHOS_VIRTUAL_HAL_H

void hal_uart_write(unsigned char byte);
int hal_uart_read(void);             /* -1 if no byte available */
const char *hal_machine_label(void); /* simulator-only identification */

#endif
