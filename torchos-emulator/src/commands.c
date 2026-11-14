/* Local allowlist and RAM-only state. No PL011, OS, or host calls. */
#include "commands.h"
#define HISTORY_CAPACITY 8u
#define INPUT_CAPACITY 64u
#define NOTE_CAPACITY 49u
static char history[HISTORY_CAPACITY][INPUT_CAPACITY];
static char note[NOTE_CAPACITY];
static unsigned int cursor, count;
static commands_emit_fn emit;
static commands_label_fn label;
static void putc_(char c) { if (emit) emit(c); }
static void puts_(const char *s) { if(s) while (*s) putc_(*s++); }
static int same(const char *a, const char *b) {
    while (*a && *b) { if (*a++ != *b++) return 0; }
    return *a == *b;
}
static int starts(const char *s, const char *p) {
    while (*p) if (*s++ != *p++) return 0;
    return 1;
}
void commands_init(commands_emit_fn out, commands_label_fn machine) {
    unsigned i;
    emit = out;
    label = machine;
    cursor = count = 0u;
    note[0] = '\0';
    for (i=0u;i<HISTORY_CAPACITY;++i) history[i][0]='\0';
}
static void remember(const char *cmd) {
    unsigned i=0u, idx=cursor%HISTORY_CAPACITY;
    while (i<INPUT_CAPACITY-1u && cmd[i]) { history[idx][i]=cmd[i]; ++i; }
    history[idx][i]='\0';
    cursor=(cursor+1u)%HISTORY_CAPACITY;
    if(count<HISTORY_CAPACITY) ++count;
}
static void show_history(void) {
    unsigned i;
    for (i=0u;i<count;++i) {
        unsigned idx=(cursor+HISTORY_CAPACITY-count+i)%HISTORY_CAPACITY;
        puts_(history[idx]); putc_('\n');
    }
}
static void set_note(const char *v) {
    unsigned n=0u, i;
    if (!*v) { puts_("Note rejected: empty value.\n"); return; }
    while(v[n]) {
        ++n;
        if(n>=NOTE_CAPACITY) {
            puts_("Note rejected: exceeds 48 bytes; previous note preserved.\n");
            return;
        }
    }
    for(i=0u;i<n;++i) note[i]=v[i];
    note[n]='\0';
    puts_("Note saved in volatile RAM only.\n");
}
void commands_execute(const char *cmd) {
    if(!cmd || !*cmd) return;
    remember(cmd);
    if (same(cmd,"help")) puts_("Available: help about status clear history notes files\n");
    else if (same(cmd,"about")) {
        puts_("TorchOS CP006: independent ARMv7 QEMU research monitor.\n");
        puts_("Not BlackBerry firmware. No Linux, network, or device access.\n");
    } else if (same(cmd,"status")) {
        puts_("Machine: "); puts_(label ? label() : "unknown"); putc_('\n');
        puts_("Console: virtual PL011 UART (guest FDT discovered)\n");
        puts_("BlackBerry hardware: NOT CONNECTED\n");
        puts_("Storage, Wi-Fi, touchscreen and power: NOT IMPLEMENTED\n");
    } else if (same(cmd,"clear")) puts_("\033[2J\033[H");
    else if (same(cmd,"history")) show_history();
    else if (same(cmd,"notes")) puts_("Notes: RAM-only. Use notes set <text>, notes show, notes clear.\n");
    else if (same(cmd,"notes show")) {
        if(!note[0]) puts_("No volatile note saved.\n");
        else { puts_("Volatile note: "); puts_(note); putc_('\n'); }
    } else if (same(cmd,"notes clear")) {
        note[0]='\0'; puts_("Volatile note cleared (RAM only).\n");
    } else if (starts(cmd,"notes set ")) set_note(cmd+10);
    else if (same(cmd,"files")) puts_("Files: no filesystem mounted. No device storage access.\n");
    else puts_("Unknown command. Enter help. No shell execution.\n");
}
