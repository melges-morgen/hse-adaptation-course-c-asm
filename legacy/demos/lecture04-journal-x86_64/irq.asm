bits 64
section .text
global keyboard_entry
extern keyboard_irq
keyboard_entry:
    ; No C red-zone. Preserve every GPR used by the interrupted program.
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    push rbp
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    push r14
    push r15
    mov rbx, rsp
    and rsp, -16
    call keyboard_irq
    mov rsp, rbx
    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rbp
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    iretq

section .note.GNU-stack noalloc noexec nowrite progbits
