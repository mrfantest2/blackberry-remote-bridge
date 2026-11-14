/* QEMU virt ARM32 128MiB RAM at 0x40000000, DTB at 0x40000000.
 * CP006.6 adds banked exception stacks but does not enable GIC IRQs.
 * The first 1MiB remains reserved for the virtual device tree.
 * NOT a BlackBerry image.
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
    .exception_stacks (NOLOAD) : ALIGN(16) {
        __und_stack_bottom = .;
        . = . + 1024;
        __und_stack_top = .;
        __abt_stack_bottom = .;
        . = . + 1024;
        __abt_stack_top = .;
        __irq_stack_bottom = .;
        . = . + 1024;
        __irq_stack_top = .;
        __fiq_stack_bottom = .;
        . = . + 1024;
        __fiq_stack_top = .;
    }
    .stack (NOLOAD) : ALIGN(16) {
        __stack_bottom = .;
        . = . + 16384;
        __stack_top = .;
    }
    __image_end = .;
    ASSERT(__image_start >= 0x40100000, "ELF overlaps QEMU FDT reserve")
    ASSERT(__image_end <= 0x48000000, "ELF exceeds QEMU RAM")
    ASSERT((cp066_vector_table & 31) == 0, "VBAR vector table not 32-byte aligned")
    ASSERT(__und_stack_bottom >= __bss_end, "UND stack overlaps BSS")
    ASSERT(__stack_bottom >= __fiq_stack_top, "SVC stack overlaps exception stacks")
    /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
