#ifndef TORCHOS_CONSOLE_H
#define TORCHOS_CONSOLE_H
typedef int (*console_write_byte)(unsigned char);
typedef void (*console_dispatch)(const char *);
void console_init(console_write_byte writer, console_dispatch dispatch);
void console_putc(char ch);
void console_puts(const char *text);
void console_start(void);
void console_feed(int byte);
int console_faulted(void);
#endif
