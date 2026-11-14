/* Only for QEMU ARM 'virt', 128 MiB RAM starting at 0x40000000.
 * Link away from the DTB at RAM start. NEVER flash to BlackBerry hardware.
 */
ENTRY(_start)
SECTIONS
{
    . = 0x40100000;
    .text : ALIGN(4) {
        KEEP(*(.text.boot))
        *(.text .text.*)
    }
    .rodata : ALIGN(4) { *(.rodata .rodata.*) }
    .data : ALIGN(4) { *(.data .data.*) }
    .ARM.exidx : ALIGN(4) { *(.ARM.exidx*) }
    .bss (NOLOAD) : ALIGN(4) {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    }
    .stack (NOLOAD) : ALIGN(16) {
        . = . + 16384;
        __stack_top = .;
    }
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
