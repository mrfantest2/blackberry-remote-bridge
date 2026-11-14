/* CP006.4 host-only determinism tests; no device, UART MMIO or shell. */
#include "console.h"
#include "commands.h"
#include "uart_poll.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static char captured[8192];
static size_t used;
static int block_write;
static int fake_write(unsigned char c) {
    if (block_write) return 0;
    if (used+1u>=sizeof(captured)) return 0;
    captured[used++]=(char)c; captured[used]='\0'; return 1;
}
static const char *label(void) { return "Test virtual hardware"; }
static void feed(const char *input) {
    while(*input) console_feed((unsigned char)*input++);
}
#define CHECK(cond) do { if (!(cond)) { \
    fprintf(stderr,"MODULE_FAIL line %d: %s\n", __LINE__, #cond); return 1; \
} } while(0)
static int console_test(void) {
    unsigned i;
    console_init(fake_write,commands_execute);
    commands_init(console_putc,label);
    console_start();
    feed("help\r");
    CHECK(strstr(captured,"Available: help about status clear history notes files")!=NULL);
    feed("status\r");
    CHECK(strstr(captured,"Machine: Test virtual hardware")!=NULL);
    CHECK(strstr(captured,"NOT IMPLEMENTED")!=NULL);
    feed("about\r");
    CHECK(strstr(captured,"TorchOS CP006")!=NULL);
    feed("files\r");
    CHECK(strstr(captured,"no filesystem mounted")!=NULL);
    feed("notes set accepted\r");
    feed("notes show\r");
    CHECK(strstr(captured,"Volatile note: accepted")!=NULL);
    feed("notes clear\r");
    feed("notes show\r");
    CHECK(strstr(captured,"No volatile note saved.")!=NULL);
    feed("notes set good\r");
    feed("notes set XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\r");
    feed("notes show\r");
    CHECK(strstr(captured,"previous note preserved")!=NULL);
    CHECK(strstr(captured,"Volatile note: good")!=NULL);
    feed("\001");
    CHECK(strstr(captured,"Non-printable input rejected.")!=NULL);
    for(i=0u;i<9u;++i) feed("help\r");
    used=0u; captured[0]='\0';
    feed("history\r");
    /* The eight-entry history contains only the seven previous help
     * entries plus the newest history command. */
    CHECK(strstr(captured,"help\r\n")!=NULL);
    CHECK(strstr(captured,"history\r\n")!=NULL);
    feed("clear\r");
    CHECK(strstr(captured,"\033[2J\033[H")!=NULL);
    /* A transport error must become a detectable fault, never spin. */
    block_write=1;
    feed("help\r");
    CHECK(console_faulted());
    block_write=0;
    used=0u; captured[0]='\0';
    console_init(fake_write,commands_execute);
    commands_init(console_putc,label);
    feed("notes show\r");
    CHECK(strstr(captured,"No volatile note saved.")!=NULL);
    puts("HOST_CONSOLE_OK");
    return 0;
}
struct mock {
    unsigned reads, writes, busy_reads, forever_busy;
    unsigned rx_empty, rx_byte;
    unsigned last_data;
};
static uint32_t mock_read(void *c, uint32_t off) {
    struct mock *m=(struct mock*)c;
    ++m->reads;
    if(off==0x18u) {
        if(m->forever_busy || m->reads<=m->busy_reads) return (1u<<5);
        return m->rx_empty ? (1u<<4):0u;
    }
    return m->rx_byte;
}
static void mock_write(void *c, uint32_t off, uint32_t v) {
    struct mock *m=(struct mock*)c;
    if(off==0u) { ++m->writes; m->last_data=v; }
}
static int uart_test(void) {
    struct mock mock={0};
    struct uart_poll_bus bus={&mock,mock_read,mock_write,0u};
    CHECK(!uart_poll_send(&bus,(uint8_t)'A',10u));
    CHECK(uart_poll_receive(&bus)==-1);
    CHECK(mock.reads==0u && mock.writes==0u);
    bus.ready=1u;
    mock.busy_reads=3u;
    CHECK(uart_poll_send(&bus,(uint8_t)'B',5u));
    CHECK(mock.reads==4u && mock.writes==1u && mock.last_data==(unsigned)'B');
    mock.reads=0u; mock.writes=0u;
    mock.forever_busy=1u;
    CHECK(!uart_poll_send(&bus,(uint8_t)'C',7u));
    CHECK(mock.reads==7u && mock.writes==0u);
    mock.forever_busy=0u; mock.reads=0u;
    mock.rx_empty=1u;
    CHECK(uart_poll_receive(&bus)==-1);
    CHECK(mock.reads==1u);
    mock.rx_empty=0u; mock.rx_byte=(unsigned)'Z';
    CHECK(uart_poll_receive(&bus)=='Z');
    CHECK(!uart_poll_send(&bus,(uint8_t)'D',0u));
    puts("HOST_UART_BOUNDS_OK");
    return 0;
}
int main(int argc, char **argv) {
    if(argc!=2) return 2;
    if(strcmp(argv[1],"console")==0) return console_test();
    if(strcmp(argv[1],"uart")==0) return uart_test();
    return 2;
}
