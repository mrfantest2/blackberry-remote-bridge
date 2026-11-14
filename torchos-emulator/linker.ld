/* QEMU virt ARM32, RAM 0x40000000..0x48000000, FDT at 0x40000000.
 * The reserved 1MiB FDT window is never used by this ELF or its stack.
 * NOT an image for any BlackBerry.
 */
ENTRY(_start)
SECTIONS {
    . = 0x40100000;
    __image_start = .;
    .text : ALIGN(4) { KEEP(*(.text.boot)) *(.text .text.*) }
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
        __stack_bottom = .;
        . = . + 16384;
        __stack_top = .;
    }
    __image_end = .;
    ASSERT(__image_start >= 0x40100000, "ELF overlaps QEMU FDT reserve")
    ASSERT(__image_end <= 0x48000000, "ELF exceeds QEMU RAM")
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
