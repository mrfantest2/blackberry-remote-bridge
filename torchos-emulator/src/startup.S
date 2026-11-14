/* CP006.6: ARMv7-A exception vector foundation, QEMU virt-8.2 only.
 * IRQ/FIQ remain masked. No GIC, device IRQ routing or physical support.
 */
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
    /* Establish separate, bounded banked stacks before installing vectors. */
    cps #0x1b               /* Undefined mode */
    ldr sp, =__und_stack_top
    cps #0x17               /* Abort mode */
    ldr sp, =__abt_stack_top
    cps #0x12               /* IRQ mode (delivery still disabled) */
    ldr sp, =__irq_stack_top
    cps #0x11               /* FIQ mode (delivery still disabled) */
    ldr sp, =__fiq_stack_top
    cps #0x13               /* Supervisor mode, original kernel */
    ldr sp, =__stack_top
    /* VBAR only handles normal low vectors. Disable SCTLR.V high vectors. */
    mrc p15, 0, r1, c1, c0, 0
    bic r1, r1, #0x2000
    mcr p15, 0, r1, c1, c0, 0
    isb
    ldr r0, =cp066_vector_table
    mcr p15, 0, r0, c12, c0, 0
    isb
    mrc p15, 0, r1, c12, c0, 0
    ldr r2, =cp066_vbar_readback
    str r1, [r2]
    bl kmain
3:  b 3b

/* Preserve the accepted CP006.4 named fail-closed halt symbol/loop. */
.global cp064_halt
.type cp064_halt, %function
cp064_halt:
4:  wfi
    b 4b

/* Eight consecutive 32-bit A32 instructions, 32-byte aligned for VBAR.
 * An IRQ vector is defined but real delivery remains MASKED on purpose. */
.p2align 5
.global cp066_vector_table
.type cp066_vector_table, %function
cp066_vector_table:
    b cp066_trap_reset
    b cp066_trap_undefined
    b cp066_trap_svc
    b cp066_trap_prefetch
    b cp066_trap_data
    b cp066_trap_reserved
    b cp066_trap_irq
    b cp066_trap_fiq

cp066_trap_reset:
    mov r0, #7
    b cp066_trap_record
cp066_trap_undefined:
    mov r0, #1
    b cp066_trap_record
cp066_trap_svc:
    mov r0, #2
    b cp066_trap_record
cp066_trap_prefetch:
    mov r0, #3
    b cp066_trap_record
cp066_trap_data:
    mov r0, #4
    b cp066_trap_record
cp066_trap_reserved:
    mov r0, #8
    b cp066_trap_record
cp066_trap_irq:
    mov r0, #5
    b cp066_trap_record
cp066_trap_fiq:
    mov r0, #6
    b cp066_trap_record

/* Deliberately no printf, MMIO, stack use, nesting or recovery.
 * Captures exception class, exception-mode LR and saved pre-trap CPSR.
 * Both SVC and Undefined are real ARM exceptions in hosted guest tests. */
.global cp066_trap_record
cp066_trap_record:
    ldr r1, =cp066_exception_kind
    str r0, [r1]
    ldr r1, =cp066_saved_lr
    str lr, [r1]
    mrs r2, spsr
    ldr r1, =cp066_saved_spsr
    str r2, [r1]
    ldr r1, =cp064_boot_phase
    ldr r2, =0x066bad00
    str r2, [r1]
    b cp064_halt

/* Test-only, non-user-facing symbols. QEMU GDB sets PC here ONLY AFTER
 * a normal guest cold boot, to cause actual CPU-generated exceptions.
 * They are never called by the command processor or original boot path. */
.global cp066_probe_svc
cp066_probe_svc:
    svc #0x66
    b cp064_halt
.global cp066_probe_undefined
cp066_probe_undefined:
    .word 0xe7f000f0   /* A32 UDF #0 */
    b cp064_halt
/* CP006.6 TEST-ONLY QEMU virt-8.2 GICv2 stimulus.
 * Executed only by a hosted GDB PC redirection AFTER verified guest boot.
 * Not called by normal kernel, serial console, or any BlackBerry app.
 * QEMU virt.c: GIC distributor 0x08000000, CPU interface 0x08010000.
 */
.global cp066_probe_gicv2_sgi0
cp066_probe_gicv2_sgi0:
    ldr r0, =0x08000000
    mov r1, #1
    str r1, [r0]              /* GICD_CTLR enable */
    ldr r3, [r0]
    ldr r2, =cp066_gic_dist_readback
    str r3, [r2]

    ldr r0, =0x08010000
    mov r1, #0xff
    str r1, [r0, #4]          /* GICC_PMR allow priorities */
    ldr r3, [r0, #4]
    ldr r2, =cp066_gic_pmr_readback
    str r3, [r2]
    mov r1, #1
    str r1, [r0]              /* GICC_CTLR enable */
    ldr r3, [r0]
    ldr r2, =cp066_gic_cpu_readback
    str r3, [r2]

    ldr r0, =0x08000100
    mov r1, #1
    str r1, [r0]              /* Enable SGI 0 on GICD */
    ldr r0, =0x08000f00
    ldr r1, =0x02000000
    str r1, [r0]              /* SGI0, target filter: self */
    cpsie i                   /* Test-only interrupt unmask */
cp066_irq_test_pending:
    b cp066_irq_test_pending

.ltorg
