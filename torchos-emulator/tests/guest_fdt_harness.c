/* Host-only parser harness; never communicates with physical BlackBerry. */
#include "guest_fdt.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
    unsigned char blob[GUEST_FDT_LIMIT];
    struct guest_fdt_devices dev;
    FILE *f;
    size_t n;
    if (argc != 2 || (f = fopen(argv[1], "rb")) == NULL) return 2;
    n = fread(blob, 1u, sizeof(blob), f);
    if (ferror(f) || !feof(f)) { fclose(f); return 2; }
    fclose(f);
    if (!guest_fdt_parse(blob, n, &dev)) { puts("FDT_REJECTED"); return 1; }
    printf("FDT_VALID uart=0x%08lx size=%lu ram=0x%08lx bytes=%lu\n",
           (unsigned long)dev.uart_address, (unsigned long)dev.uart_size,
           (unsigned long)dev.ram_address, (unsigned long)dev.ram_size);
    return 0;
}
