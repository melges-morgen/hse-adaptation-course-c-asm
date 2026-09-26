bits 64
section .text
global add_middle
global trace_start
global trace_end

; System V AMD64: RDI contains int *a. RBX must be preserved.
add_middle:
    push rbx
    mov rbx, rdi
trace_start:
    mov eax, [rbx + 4]
    add eax, 5
    mov [rbx + 4], eax
trace_end:
    pop rbx
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
