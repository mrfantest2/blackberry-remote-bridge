/* CP006.7: QEMU virt-8.2 GICv2 one-shot SGI service and return-to-console.
 *
 * QEMU VIRTUAL MACHINE ONLY. Not BlackBerry firmware, not a GIC driver.
 * Normal boot never executes cp067_probe_gicv2_resume: IRQ/FIQ stay masked
 * and the GIC is never touched. A hosted test enters the probe through a
 * GDB PC redirect after a verified boot; the GUEST then performs all GIC
 * MMIO, the CPU takes a real IRQ exception, and the guest handler performs
 * IAR acknowledge, ID validation, EOIR and ARMv7-A exception return.
 *
 * QEMU hw/arm/virt.c (GICv2): distributor 0x08000000, CPU iface 0x08010000.
 */
.syntax unified
.cpu cortex-a15
.arm

.equ GICD_BASE,        0x08000000
.equ GICD_CTLR,        0x000
.equ GICD_ISENABLER0,  0x100
.equ GICD_ICENABLER0,  0x180
.equ GICD_ICPENDR0,    0x280
.equ GICD_SGIR,        0xf00
.equ GICC_BASE,        0x08010000
.equ GICC_CTLR,        0x000
.equ GICC_PMR,         0x004
.equ GICC_IAR,         0x00c
.equ GICC_EOIR,        0x010
.equ GIC_SPURIOUS,     1023
.equ CP067_SUPPORTED_ID, 0          /* only SGI 0 is accepted */
.equ PHASE_IRQ_REJECTED,   0x067bad01
.equ PHASE_IRQ_NESTED,     0x067bad02
.equ PHASE_PROBE_REJECTED, 0x067bad03

/* RAM-only telemetry, zeroed by the existing BSS clear. Read via QMP/GDB. */
.section .bss
.p2align 2
.global cp067_irq_armed, cp067_in_irq, cp067_irq_count, cp067_spurious_count
.global cp067_last_iar, cp067_resume_pc, cp067_resume_spsr
.global cp067_test_sgi_id, cp067_rejected_id, cp067_probe_cpsr
cp067_irq_armed:      .space 4  /* 1 only between probe arm and service   */
cp067_in_irq:         .space 4  /* re-entrancy guard                      */
cp067_irq_count:      .space 4  /* accepted + EOI'd SGI0 interrupts       */
cp067_spurious_count: .space 4
cp067_last_iar:       .space 4  /* raw GICC_IAR value read by the guest   */
cp067_resume_pc:      .space 4  /* preferred return address (LR_irq - 4)  */
cp067_resume_spsr:    .space 4  /* CPSR restored on exception return      */
cp067_test_sgi_id:    .space 4  /* host test selects SGI; default 0       */
cp067_rejected_id:    .space 4
cp067_probe_cpsr:     .space 4

/* Disable distributor + CPU interface, clear SGI enables/pending. r0,r1. */
.macro QUIESCE_GIC
    ldr r0, =GICD_BASE
    ldr r1, =0xffff
    str r1, [r0, #GICD_ICENABLER0]
    str r1, [r0, #GICD_ICPENDR0]
    mov r1, #0
    str r1, [r0, #GICD_CTLR]
    ldr r0, =GICC_BASE
    str r1, [r0, #GICC_CTLR]
    dsb
.endm

.macro FAIL_CLOSED phase
    ldr r0, =cp067_irq_armed
    mov r1, #0
    str r1, [r0]
    QUIESCE_GIC
    ldr r0, =cp064_boot_phase
    ldr r1, =\phase
    str r1, [r0]
    b cp064_halt                    /* IRQ stays masked; bounded halt */
.endm

.section .text
/* TEST-ONLY entry. Precondition set by host GDB while the guest is stopped
 * in the console loop: original PC pushed onto the SVC stack, PC = here.
 * Every register and the CPSR flags are preserved; the return is a single
 * atomic CPSR<-SPSR_svc / PC load, so the pending SGI is taken by the
 * console code itself, not by this probe. */
.p2align 2
.global cp067_probe_gicv2_resume
.type cp067_probe_gicv2_resume, %function
cp067_probe_gicv2_resume:
    push {r0-r12, lr}
    mrs r4, cpsr
    ldr r5, =cp067_probe_cpsr
    str r4, [r5]
    and r6, r4, #0x1f
    cmp r6, #0x13                   /* must be the original SVC kernel */
    bne cp067_probe_reject
    and r6, r4, #0xc0
    cmp r6, #0xc0                   /* must enter with IRQ+FIQ masked */
    bne cp067_probe_reject
    ldr r5, =cp067_irq_armed
    ldr r6, [r5]
    cmp r6, #0                      /* no double arming */
    bne cp067_probe_reject
    ldr r5, =cp067_irq_count
    ldr r6, [r5]
    cmp r6, #0                      /* one serviced interrupt per boot */
    bne cp067_probe_reject
    ldr r7, =cp067_test_sgi_id
    ldr r7, [r7]
    cmp r7, #15                     /* SGI range only */
    bhi cp067_probe_reject

    ldr r0, =GICD_BASE
    mov r1, #1
    str r1, [r0, #GICD_CTLR]
    mov r1, #1
    lsl r1, r1, r7
    str r1, [r0, #GICD_ISENABLER0]
    ldr r0, =GICC_BASE
    mov r1, #0xff
    str r1, [r0, #GICC_PMR]
    mov r1, #1
    str r1, [r0, #GICC_CTLR]
    ldr r5, =cp067_irq_armed
    mov r6, #1
    str r6, [r5]
    dsb
    ldr r0, =GICD_BASE
    ldr r1, =0x02000000             /* TargetListFilter=self */
    orr r1, r1, r7
    str r1, [r0, #GICD_SGIR]
    dsb
    isb

    bic r4, r4, #0x80               /* resume console with IRQ unmasked */
    msr spsr_cxsf, r4
    pop {r0-r12, lr}
    ldm sp!, {pc}^                  /* atomic PC + CPSR<-SPSR_svc */

cp067_probe_reject:
    ldr r0, =cp064_boot_phase
    ldr r1, =PHASE_PROBE_REJECTED
    str r1, [r0]
    b cp064_halt

/* IRQ vector target. Unarmed IRQs fall back to the CP006.6 fail-closed
 * recorder with LR/SPSR untouched. Runs on the bounded banked IRQ stack
 * with IRQ masked by hardware; no nesting, no UART, no C calls. */
.p2align 2
.global cp067_irq_entry
.type cp067_irq_entry, %function
cp067_irq_entry:
    push {r0-r3, r12, lr}
    ldr r0, =cp067_irq_armed
    ldr r1, [r0]
    cmp r1, #1
    popne {r0-r3, r12, lr}
    bne cp066_trap_irq
    ldr r0, =cp067_in_irq
    ldr r1, [r0]
    cmp r1, #0
    bne cp067_irq_nested
    mov r1, #1
    str r1, [r0]

    ldr r2, =GICC_BASE
    ldr r3, [r2, #GICC_IAR]         /* acknowledge */
    ldr r0, =cp067_last_iar
    str r3, [r0]
    ldr r1, =0x3ff
    and r1, r3, r1
    ldr r0, =GIC_SPURIOUS
    cmp r1, r0
    beq cp067_irq_spurious
    cmp r1, #CP067_SUPPORTED_ID
    bne cp067_irq_bad_id
    str r3, [r2, #GICC_EOIR]        /* EOI with full IAR (incl. CPUID) */
    ldr r0, =cp067_irq_count
    ldr r1, [r0]
    add r1, r1, #1
    str r1, [r0]

cp067_irq_finish:
    ldr r0, =cp067_irq_armed
    mov r1, #0
    str r1, [r0]
    QUIESCE_GIC
    mrs r1, spsr
    orr r1, r1, #0x80               /* one-shot: console resumes masked */
    msr spsr_cxsf, r1
    ldr r0, =cp067_resume_spsr
    str r1, [r0]
    ldr r1, [sp, #20]               /* stacked LR_irq */
    sub r1, r1, #4
    ldr r0, =cp067_resume_pc
    str r1, [r0]
    ldr r0, =cp067_in_irq
    mov r1, #0
    str r1, [r0]
    pop {r0-r3, r12, lr}
    subs pc, lr, #4                 /* ARMv7-A IRQ return, CPSR<-SPSR_irq */

cp067_irq_spurious:
    ldr r0, =cp067_spurious_count   /* no EOI for 1023 per GICv2 */
    ldr r1, [r0]
    add r1, r1, #1
    str r1, [r0]
    b cp067_irq_finish

cp067_irq_bad_id:
    ldr r0, =cp067_rejected_id
    str r1, [r0]
    cmp r1, #1020                   /* EOI real IDs so the GIC is not wedged */
    strlo r3, [r2, #GICC_EOIR]
    FAIL_CLOSED PHASE_IRQ_REJECTED

cp067_irq_nested:
    FAIL_CLOSED PHASE_IRQ_NESTED

.ltorg
