; BIOS loads this sector at 0000:7c00. A 1.44 MiB floppy has 18 sectors/track.
bits 16
org 0x7c00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov ss, ax
    mov sp, 0x7c00
    sti
    mov [boot_drive], dl
    mov ax, 0x1000
    mov es, ax
    xor bx, bx
    mov ah, 0x02                 ; BIOS: read sectors (CHS)
    mov al, 17                   ; sectors 2..18 of cylinder 0, head 0
    xor ch, ch
    mov cl, 2
    xor dh, dh
    mov dl, [boot_drive]
    int 0x13
    jc boot_error
    cmp al, 17
    jne boot_error
    mov dl, [boot_drive]
    jmp 0x1000:0x0000            ; code and data are now in RAM

boot_error:
    mov si, error_text
.print:
    lodsb
    test al, al
    jz .halt
    mov ah, 0x0e
    mov bx, 0x0007
    int 0x10
    jmp .print
.halt:
    cli
    hlt
    jmp .halt

boot_drive: db 0
error_text: db 'BOOT ERROR', 0
times 510 - ($ - $$) db 0
dw 0xaa55
