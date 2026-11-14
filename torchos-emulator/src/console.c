/* Terminal transport: bounded line editing and output, no hardware registers. */
#include "console.h"
#define INPUT_CAPACITY 64u
static char line[INPUT_CAPACITY];
static unsigned int length;
static unsigned int swallow_lf;
static unsigned int failed;
static console_write_byte writer;
static console_dispatch dispatch_line;

void console_init(console_write_byte send, console_dispatch dispatch) {
    length = swallow_lf = failed = 0u;
    writer = send;
    dispatch_line = dispatch;
}
int console_faulted(void) { return failed != 0u; }
void console_putc(char ch) {
    if (failed || !writer) { failed = 1u; return; }
    if (ch == '\n' && !writer('\r')) { failed = 1u; return; }
    if (!writer((unsigned char)ch)) failed = 1u;
}
void console_puts(const char *s) {
    if (!s) return;
    while (*s && !failed) console_putc(*s++);
}
void console_start(void) { console_puts("torch> "); }
void console_feed(int c) {
    if (failed) return;
    if (c == '\r' || c == '\n') {
        if (c == '\n' && swallow_lf) { swallow_lf = 0u; return; }
        swallow_lf = (c == '\r') ? 1u : 0u;
        console_putc('\n');
        line[length] = '\0';
        if (!failed && dispatch_line) dispatch_line(line);
        length = 0u;
        if (!failed) console_start();
    } else if (c == 8 || c == 127) {
        swallow_lf = 0u;
        if (length) { --length; console_puts("\b \b"); }
    } else if (c >= 32 && c <= 126) {
        swallow_lf = 0u;
        if (length >= INPUT_CAPACITY - 1u) {
            console_puts("\nInput too long; discarded.\n");
            length = 0u;
            if (!failed) console_start();
        } else {
            line[length++] = (char)c;
            console_putc((char)c);
        }
    } else {
        swallow_lf = 0u;
        length = 0u;
        console_puts("\nNon-printable input rejected.\n");
        if (!failed) console_start();
    }
}
