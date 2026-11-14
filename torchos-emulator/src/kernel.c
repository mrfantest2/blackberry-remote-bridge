/*
 * TorchOS CP005 — original tiny ARMv7 research monitor.
 *
 * Runs ONLY on QEMU's generic ARM virt machine. This is not Linux, Parrot,
 * BlackBerry OS, a driver port, or a flashable BlackBerry image.
 * QEMU virt's PL011 UART base is a version-specific test assumption;
 * a real hardware target must discover its devices and use proper drivers.
 */
#include "hal.h"
#define INPUT_CAPACITY 64u
#define HISTORY_CAPACITY 8u
#define HISTORY_MASK (HISTORY_CAPACITY - 1u)
#define NOTE_CAPACITY 49u

static char input[INPUT_CAPACITY];
static char history[HISTORY_CAPACITY][INPUT_CAPACITY];
static char volatile_note[NOTE_CAPACITY];
static unsigned int input_length;
static unsigned int history_cursor;
static unsigned int history_count;
static unsigned int swallow_line_feed;

static void uart_putc(char ch) {
    if (ch == '\n') {
        hal_uart_write('\r');
    }
    hal_uart_write((unsigned char)ch);
}

static void uart_puts(const char *s) {
    while (*s != '\0') {
        uart_putc(*s++);
    }
}

static int uart_read(void) {
    return hal_uart_read();
}

static int same(const char *a, const char *b) {
    while (*a != '\0' && *b != '\0') {
        if (*a != *b) {
            return 0;
        }
        ++a;
        ++b;
    }
    return (*a == '\0' && *b == '\0');
}

static int starts_with(const char *text, const char *prefix) {
    while (*prefix != '\0') {
        if (*text++ != *prefix++) {
            return 0;
        }
    }
    return 1;
}

static void set_note(const char *value) {
    unsigned int n = 0u;
    if (*value == '\0') {
        uart_puts("Note rejected: empty value.\n");
        return;
    }
    while (value[n] != '\0') {
        ++n;
        if (n >= NOTE_CAPACITY) {
            uart_puts("Note rejected: exceeds 48 bytes; previous note preserved.\n");
            return;
        }
    }
    for (n = 0u; value[n] != '\0'; ++n) {
        volatile_note[n] = value[n];
    }
    volatile_note[n] = '\0';
    uart_puts("Note saved in volatile RAM only.\n");
}

static void remember(const char *cmd) {
    unsigned int i = 0u;
    unsigned int idx = history_cursor & HISTORY_MASK;
    while (i < INPUT_CAPACITY - 1u && cmd[i] != '\0') {
        history[idx][i] = cmd[i];
        ++i;
    }
    history[idx][i] = '\0';
    history_cursor = (history_cursor + 1u) & HISTORY_MASK;
    if (history_count < HISTORY_CAPACITY) {
        ++history_count;
    }
}

static void print_history(void) {
    unsigned int i;
    for (i = 0u; i < history_count; ++i) {
        unsigned int idx = (history_cursor + HISTORY_CAPACITY - history_count + i) & HISTORY_MASK;
        uart_puts(history[idx]);
        uart_putc('\n');
    }
}

static void execute_command(const char *cmd) {
    if (cmd[0] == '\0') {
        return;
    }
    remember(cmd);
    if (same(cmd, "help")) {
        uart_puts("Available: help about status clear history notes files\n");
    } else if (same(cmd, "about")) {
        uart_puts("TorchOS CP006: independent ARMv7 QEMU research monitor.\n");
        uart_puts("Not BlackBerry firmware. No Linux, network, or device access.\n");
    } else if (same(cmd, "status")) {
        uart_puts("Machine: ");
        uart_puts(hal_machine_label());
        uart_putc('\n');
        uart_puts("Console: virtual PL011 UART\n");
        uart_puts("BlackBerry hardware: NOT CONNECTED\n");
        uart_puts("Storage, Wi-Fi, touchscreen and power: NOT IMPLEMENTED\n");
    } else if (same(cmd, "clear")) {
        uart_puts("\033[2J\033[H");
    } else if (same(cmd, "history")) {
        print_history();
    } else if (same(cmd, "notes")) {
        uart_puts("Notes: RAM-only. Use notes set <text>, notes show, notes clear.\n");
    } else if (same(cmd, "notes show")) {
        if (volatile_note[0] == '\0') {
            uart_puts("No volatile note saved.\n");
        } else {
            uart_puts("Volatile note: ");
            uart_puts(volatile_note);
            uart_putc('\n');
        }
    } else if (same(cmd, "notes clear")) {
        volatile_note[0] = '\0';
        uart_puts("Volatile note cleared (RAM only).\n");
    } else if (starts_with(cmd, "notes set ")) {
        set_note(cmd + 10);
    } else if (same(cmd, "files")) {
        uart_puts("Files: no filesystem mounted. No device storage access.\n");
    } else {
        uart_puts("Unknown command. Enter help. No shell execution.\n");
    }
}

static void prompt(void) {
    uart_puts("torch> ");
}

void kmain(void) {
    uart_puts("\nTorchOS CP005 — Independent ARM Research Boot\n");
    uart_puts("QEMU VIRTUAL MACHINE ONLY — NOT BLACKBERRY HARDWARE\n");
    uart_puts("No firmware, phone access, filesystem, network or remote commands.\n");
    uart_puts("Type help to see local commands.\n");
    prompt();

    for (;;) {
        int c = uart_read();
        if (c < 0) {
            continue;
        }
        if (c == '\r' || c == '\n') {
            if (c == '\n' && swallow_line_feed != 0u) {
                swallow_line_feed = 0u;
                continue;
            }
            swallow_line_feed = (c == '\r') ? 1u : 0u;
            uart_putc('\n');
            input[input_length] = '\0';
            execute_command(input);
            input_length = 0u;
            prompt();
        } else if (c == 8 || c == 127) {
            swallow_line_feed = 0u;
            if (input_length > 0u) {
                --input_length;
                uart_puts("\b \b");
            }
        } else if (c >= 32 && c <= 126) {
            swallow_line_feed = 0u;
            if (input_length >= INPUT_CAPACITY - 1u) {
                uart_puts("\nInput too long; discarded.\n");
                input_length = 0u;
                prompt();
            } else {
                input[input_length++] = (char)c;
                uart_putc((char)c);
            }
        } else {
            swallow_line_feed = 0u;
            input_length = 0u;
            uart_puts("\nNon-printable input rejected.\n");
            prompt();
        }
    }
}
