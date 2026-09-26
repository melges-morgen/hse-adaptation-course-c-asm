; Historical x86-64 checkpoint. GRUB Multiboot2 enters protected mode.
bits 32
section .multiboot
align 8
mb_start:
    dd 0xe85250d6, 0, mb_end - mb_start
    dd -(0xe85250d6 + (mb_end - mb_start))
    dw 0, 0
    dd 8
mb_end:

section .text
global _start
extern kmain
_start:
    cli
    mov esp, stack_top
    ; identity map the first 1 GiB using 2 MiB pages
    mov eax, pdpt
    or eax, 3
    mov [pml4], eax
    mov eax, pd
    or eax, 3
    mov [pdpt], eax
    xor ecx, ecx
.pages:
    mov eax, ecx
    shl eax, 21
    or eax, 0x83
    mov [pd + ecx * 8], eax
    inc ecx
    cmp ecx, 512
    jne .pages
    mov eax, cr4
    or eax, 1 << 5
    mov cr4, eax
    mov eax, pml4
    mov cr3, eax
    mov ecx, 0xc0000080
    rdmsr
    or eax, 1 << 8
    wrmsr
    lgdt [gdt_desc]
    mov eax, cr0
    or eax, 1 << 31
    mov cr0, eax
    jmp 0x08:long_start

bits 64
long_start:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov rsp, stack_top
    xor rbp, rbp
    call kmain
.halt:
    cli
    hlt
    jmp .halt

align 8
gdt:
    dq 0
    dq 0x00af9a000000ffff
    dq 0x00af92000000ffff
gdt_desc:
    dw gdt_desc - gdt - 1
    dd gdt

section .bss
align 4096
pml4: resb 4096
pdpt: resb 4096
pd: resb 4096
stack_bottom: resb 16384
stack_top:

section .note.GNU-stack noalloc noexec nowrite progbits
