/* TorchOS CP005: QEMU virt ARMv7 boot, not BlackBerry firmware. */
.syntax unified
.cpu cortex-a15
.arm
.section .text.boot, "ax"
.global _start
.type _start, %function

_start:
    cpsid if
    ldr r0, =__bss_start
    ldr r1, =__bss_end
    mov r2, #0
1:
    cmp r0, r1
    bhs 2f
    str r2, [r0], #4
    b 1b
2:
    ldr sp, =__stack_top
    bl kmain
3:
    b 3b
