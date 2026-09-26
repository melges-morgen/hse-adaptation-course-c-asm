; 16-bit NASM, real mode. BIOS boots a floppy; grades use a separate HDD.
bits 16
org 0
%ifndef STAGE
%define STAGE 6
%endif
%define UNSET 0xff
%define STUDENTS 16
%define WORKS 4

entry:
    cli
    mov ax, cs
    mov ds, ax
    mov es, ax
    mov ax, 0x7000
    mov ss, ax
    mov sp, 0xf000
    sti
    call serial_init
    mov si, msg_boot
    call serial_str
    mov al, STAGE + '0'
    call serial_char
    mov si, msg_lf
    call serial_str
    mov di, grades
    mov cx, 64
    mov al, UNSET
    rep stosb                   ; explicit sentinel: zero is a valid grade
%if STAGE >= 6
    call load_grades
%endif
%if STAGE = 1
    mov ax, 0x0003
    int 0x10                    ; BIOS: text mode
    mov si, first_record
    call bios_text
%else
    call redraw                ; from stage 2: write VGA memory directly
%endif
%if STAGE >= 4
    call install_irq1
%endif
    mov si, msg_ready
    call serial_str
.loop:
%if STAGE = 3
    mov ah, 0x01
    int 0x16                    ; BIOS: key available?
    jz .loop
    xor ah, ah
    int 0x16                    ; BIOS: read key, scan code in AH
    mov al, ah
    call handle_scan
%elif STAGE >= 4
    call dequeue
    jc .loop
    call handle_scan
%else
    hlt
%endif
    jmp .loop

; VGA cell: physical B8000 = segment B800, offset 0; 2 bytes per cell.
vga_text:                      ; BH row, BL column, DS:SI zero-terminated
    push ax
    push cx
    push dx
    push di
    push es
    xor ax, ax
    mov al, bh
    mov cx, 160
    mul cx
    mov di, ax
    xor ax, ax
    mov al, bl
    shl ax, 1
    add di, ax
    mov ax, 0xb800
    mov es, ax
.next:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0f
    stosw
    jmp .next
.done:
    pop es
    pop di
    pop dx
    pop cx
    pop ax
    ret

vga_two:                       ; AL=0..10, BH=row BL=col
    push ax
    push bx
    push dx
    push si
    xor ah, ah
    mov dl, 10
    div dl                      ; AL tens, AH units
    add al, '0'
    add ah, '0'
    mov [two_digits], ax
    mov byte [two_digits+2], 0
    mov si, two_digits
    call vga_text
    pop si
    pop dx
    pop bx
    pop ax
    ret

bios_text:                     ; stage 1: INT 10h teletype output
    push ax
    push bx
.next:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0e
    mov bx, 0x0007
    int 0x10
    jmp .next
.done:
    pop bx
    pop ax
    ret

redraw:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    mov ax, 0xb800
    mov es, ax
    xor di, di
    mov ax, 0x0720
    mov cx, 2000
    rep stosw
    mov bx, 0x0001
    mov si, title_text
    call vga_text
    mov bx, 0x0101
    mov si, help_text
    call vga_text
    mov bx, 0x0302
    mov si, headings
    call vga_text
    xor cx, cx                   ; student index
.student:
    mov bx, 0x0402
    add bh, cl
    mov si, label_student
    call vga_text
    mov al, cl
    inc al
    mov bl, 3
    call vga_two
    xor dx, dx                   ; DL work index, DH count
    mov word [running_sum], 0
.work:
    mov ax, cx
    shl ax, 2
    add al, dl
    mov si, grades
    add si, ax
    mov al, [si]
    mov [current_grade], al
    mov bx, 0x0409
    add bh, cl
    push dx
    xor ah, ah
    mov al, dl
    mov dh, 5
    mul dh
    add bl, al
    pop dx
    cmp byte [current_grade], UNSET
    je .missing
    mov al, [current_grade]
    xor ah, ah
    add [running_sum], ax
    inc dh
    call vga_two
    jmp .next_work
.missing:
    mov si, missing_text
    call vga_text
.next_work:
    inc dl
    cmp dl, WORKS
    jb .work
%if STAGE >= 5
    mov [current_count], dh
    push cx
    mov bx, 0x041f
    add bh, cl
    test dh, dh
    jz .avg_missing
    mov ax, [running_sum]
    mov si, 100
    mul si
    xor ch, ch
    mov cl, [current_count]
    shr cl, 1
    add ax, cx
    xor ch, ch
    mov cl, [current_count]
    xor dx, dx
    div cx                       ; AX = rounded hundredths
    mov si, 100
    xor dx, dx
    div si                       ; AX integer, DX two decimal digits
    push dx
    call vga_two
    mov bl, 33
    mov si, dot_text
    call vga_text
    pop dx
    mov bl, 34
    mov al, dl
    call vga_two
    jmp .next_student
.avg_missing:
    mov si, missing_avg
    call vga_text
%endif
.next_student:
%if STAGE >= 5
    pop cx
%endif
    inc cl
    cmp cl, STUDENTS
    jb .student
    mov bx, 0x1502
    mov si, notice
    call vga_text
    mov bx, 0x1702
    mov si, footer_text
    call vga_text
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret

; Input value in AL: PS/2 set-1 make code (or BIOS INT 16h AH scan code).
handle_scan:
    push ax
    push bx
    push cx
    push dx
    cmp al, 0xe0
    jne .not_prefix
    mov byte [extended], 1
    jmp .done
.not_prefix:
    test al, 0x80
    jz .make
    mov byte [extended], 0
    jmp .done
.make:
    cmp byte [extended], 0
    jne .arrow
    cmp al, 0x48                ; BIOS INT16 arrows have no E0 prefix
    je .up
    cmp al, 0x50
    je .down
    cmp al, 0x4b
    je .left
    cmp al, 0x4d
    je .right
    jmp .normal
.arrow:
    mov byte [extended], 0
    cmp al, 0x48
    je .up
    cmp al, 0x50
    je .down
    cmp al, 0x4b
    je .left
    cmp al, 0x4d
    je .right
    jmp .done
.up:
    cmp byte [student], 0
    je .done
    dec byte [student]
    jmp .changed
.down:
    cmp byte [student], STUDENTS - 1
    je .done
    inc byte [student]
    jmp .changed
.left:
    cmp byte [work], 0
    je .done
    dec byte [work]
    jmp .changed
.right:
    cmp byte [work], WORKS - 1
    je .done
    inc byte [work]
    jmp .changed
.normal:
%if STAGE >= 6
    cmp al, 0x1f                ; S
    je .save
    cmp al, 0x26                ; L
    je .load
%endif
    cmp al, 0x0e                ; Backspace
    je .erase
    cmp al, 0x1e                ; A=10
    je .ten
    cmp al, 0x0b                ; key 0
    je .zero
    cmp al, 0x02
    jb .done
    cmp al, 0x0a
    ja .done
    sub al, 0x01               ; keys 1..9
    jmp .set
.erase:
    mov al, UNSET
    jmp .set
.ten:
    mov al, 10
    jmp .set
.zero:
    xor al, al
.set:
    mov bl, [student]
    xor bh, bh
    shl bx, 2
    add bl, [work]
    mov [grades+bx], al
.changed:
    call report_grade
    call redraw
    jmp .done
%if STAGE >= 6
.save:
    call save_grades
    call redraw
    jmp .done
.load:
    call load_grades
    call redraw
    call report_grade
%endif
.done:
    pop dx
    pop cx
    pop bx
    pop ax
    ret

; IRQ1 vector 09h on the BIOS-compatible PIC. We no longer use INT 16h.
%if STAGE >= 4
install_irq1:
    cli
    xor ax, ax
    mov es, ax
    mov word [es:9*4], irq1
    mov ax, cs
    mov word [es:9*4+2], ax
    mov ax, cs
    mov es, ax
    in al, 0x21
    and al, 0xfd
    out 0x21, al
.drain:
    in al, 0x64
    test al, 1
    jz .ready
    in al, 0x60
    jmp .drain
.ready:
    sti
    ret

irq1:
    push ax
    push bx
    push ds
    mov ax, cs
    mov ds, ax
    in al, 0x64
    test al, 1
    jz .eoi
    in al, 0x60
    mov bl, [qhead]
    mov bh, bl
    inc bh
    and bh, 63
    cmp bh, [qtail]
    je .eoi
    xor bh, bh
    mov [queue+bx], al
    inc byte [qhead]
    and byte [qhead], 63
.eoi:
    mov al, 0x20
    out 0x20, al
    pop ds
    pop bx
    pop ax
    iret

dequeue:                        ; AL=scan, CF=0 if available
    push bx
    xor bx, bx
    mov bl, [qtail]
    cmp bl, [qhead]
    je .empty
    mov al, [queue+bx]
    inc byte [qtail]
    and byte [qtail], 63
    clc
    pop bx
    ret
.empty:
    stc
    pop bx
    ret
%endif

; COM1 is a test-only diagnostic channel, not the student's display.
serial_init:
    mov dx, 0x3f9
    xor al, al
    out dx, al
    mov dx, 0x3fb
    mov al, 0x80
    out dx, al
    mov dx, 0x3f8
    mov al, 3
    out dx, al
    inc dx
    xor al, al
    out dx, al
    mov dx, 0x3fb
    mov al, 3
    out dx, al
    mov dx, 0x3fa
    mov al, 0xc7
    out dx, al
    ret
serial_char:
    push ax
    push dx
    mov ah, al
    mov dx, 0x3fd
.wait:
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3f8
    mov al, ah
    out dx, al
    pop dx
    pop ax
    ret
serial_str:                     ; DS:SI, null-terminated
    push ax
.next:
    lodsb
    test al, al
    jz .done
    call serial_char
    jmp .next
.done:
    pop ax
    ret
serial_uint:                    ; AX unsigned decimal
    push ax
    push bx
    push cx
    push dx
    xor cx, cx
    mov bx, 10
.divide:
    xor dx, dx
    div bx
    push dx
    inc cx
    test ax, ax
    jnz .divide
.digits:
    pop ax
    add al, '0'
    call serial_char
    loop .digits
    pop dx
    pop cx
    pop bx
    pop ax
    ret

report_grade:
    push ax
    push bx
    push cx
    push dx
    push si
    mov si, msg_grade
    call serial_str
    xor ax, ax
    mov al, [student]
    inc ax
    call serial_uint
    mov si, msg_work
    call serial_str
    xor ax, ax
    mov al, [work]
    inc ax
    call serial_uint
    mov al, '='
    call serial_char
    mov bl, [student]
    xor bh, bh
    shl bx, 2
    add bl, [work]
    mov al, [grades+bx]
    cmp al, UNSET
    jne .number
    mov si, missing_text
    call serial_str
    jmp .average
.number:
    xor ah, ah
    call serial_uint
.average:
%if STAGE >= 5
    mov si, msg_avg
    call serial_str
    mov bl, [student]
    xor bh, bh
    shl bx, 2
    mov cx, WORKS
    xor dx, dx                   ; DL count, DH sum
.sum:
    mov al, [grades+bx]
    cmp al, UNSET
    je .skip
    inc dl
    add dh, al
.skip:
    inc bx
    loop .sum
    test dl, dl
    jnz .have
    mov si, missing_avg
    call serial_str
    jmp .endavg
.have:
    mov [current_count], dl
    xor ax, ax
    mov al, dh
    mov bx, 100
    mul bx
    xor ch, ch
    mov cl, [current_count]
    shr cl, 1
    add ax, cx
    xor ch, ch
    mov cl, [current_count]
    xor dx, dx
    div cx
    mov bx, 100
    xor dx, dx
    div bx                       ; AX integer, DX fractional 0..99
    call serial_uint
    mov al, '.'
    call serial_char
    mov ax, dx
    cmp ax, 10
    jae .twodigits
    push ax
    mov al, '0'
    call serial_char
    pop ax
.twodigits:
    call serial_uint
.endavg:
%endif
    mov si, msg_lf
    call serial_str
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret

%if STAGE >= 6
; 512-byte sector: GR16, version/dimensions, 64 grades, 16-bit sum.
checksum:                       ; AX=sum(bytes 0..71), unsigned modulo 65536
    push bx
    push cx
    mov bx, sector
    mov cx, 72
    xor ax, ax
.next:
    xor dx, dx
    mov dl, [bx]
    add ax, dx
    inc bx
    loop .next
    pop cx
    pop bx
    ret

disk_io:                        ; AH=0 read / AH=1 write; CF on error
    push ax
    push bx
    push cx
    push dx
    push si
    push ds
    mov bl, ah
    mov ax, cs
    mov ds, ax
    mov si, dap
    mov dl, 0x80                ; first HDD; boot floppy is DL=0
    mov ah, 0x42                ; BIOS INT 13h extensions: LBA read
    cmp bl, 0
    je .bios
    mov ah, 0x43                ; LBA write
    xor al, al
.bios:
    int 0x13
    jc .error
    clc
    jmp .done
.error:
    stc
.done:
    pop ds
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret

set_notice:                     ; DS:SI status, also COM1
    push ax
    push cx
    push di
    push si
    mov di, notice
    mov cx, 31
.copy:
    lodsb
    stosb
    test al, al
    jz .log
    loop .copy
    mov byte [di], 0
.log:
    pop si
    call serial_str
    mov si, msg_lf
    call serial_str
    pop di
    pop cx
    pop ax
    ret

save_grades:
    push ax
    push cx
    push si
    push di
    push es
    mov ax, ds
    mov es, ax
    mov di, sector
    mov cx, 256
    xor ax, ax
    rep stosw
    mov byte [sector], 'G'
    mov byte [sector+1], 'R'
    mov byte [sector+2], '1'
    mov byte [sector+3], '6'
    mov byte [sector+4], 1
    mov byte [sector+5], STUDENTS
    mov byte [sector+6], WORKS
    mov si, grades
    mov di, sector+8
    mov cx, 64
    rep movsb
    call checksum
    mov [sector+72], ax
    mov ah, 1
    call disk_io
    mov si, msg_saved
    jnc .notice
    mov si, msg_no_disk
.notice:
    call set_notice
    pop es
    pop di
    pop si
    pop cx
    pop ax
    ret

load_grades:
    push ax
    push bx
    push cx
    push si
    push di
    push es
    xor ah, ah
    call disk_io
    mov si, msg_no_disk
    jc .notice
    cmp word [sector], 0
    jne .magic
    cmp word [sector+2], 0
    jne .magic
    mov si, msg_empty
    jmp .notice
.magic:
    mov si, msg_bad_format
    cmp byte [sector], 'G'
    jne .notice
    cmp byte [sector+1], 'R'
    jne .notice
    cmp byte [sector+2], '1'
    jne .notice
    cmp byte [sector+3], '6'
    jne .notice
    mov si, msg_bad_version
    cmp byte [sector+4], 1
    jne .notice
    cmp byte [sector+5], STUDENTS
    jne .notice
    cmp byte [sector+6], WORKS
    jne .notice
    cmp byte [sector+7], 0
    jne .notice
    call checksum
    mov si, msg_bad_checksum
    cmp ax, [sector+72]
    jne .notice
    mov si, sector+8
    mov cx, 64
.check:
    lodsb
    cmp al, UNSET
    je .valid
    cmp al, 10
    ja .bad_grade
.valid:
    loop .check
    mov ax, ds
    mov es, ax
    mov si, sector+8
    mov di, grades
    mov cx, 64
    rep movsb                   ; only now change live scores
    mov si, msg_loaded
    jmp .notice
.bad_grade:
    mov si, msg_bad_grade
.notice:
    call set_notice
    pop es
    pop di
    pop si
    pop cx
    pop bx
    pop ax
    ret

dap: db 16, 0
     dw 1                       ; sector count
     dw sector, 0x1000          ; buffer offset:segment
     dq 1                       ; LBA 1 on separate HDD
sector: times 512 db 0
%endif

title_text: db 'COURSE GRADES - BIOS / NASM 16-BIT', 0
help_text: db 'arrows:select 0-9/A:grade Backspace:clear S:save L:load', 0
headings: db 'ID     W1   W2   W3   W4    AVG', 0
footer_text: db 'QEMU PC / BIOS / VGA / PS2 / real mode', 0
first_record: db 'S01  grade 07', 0
label_student: db 'S', 0
missing_text: db '--', 0
missing_avg: db '--.--', 0
dot_text: db '.', 0
two_digits: times 3 db 0
notice: times 32 db 0
grades: times 64 db UNSET
student: db 0
work: db 0
extended: db 0
current_grade: db 0
current_count: db 0
running_sum: dw 0
qhead: db 0
qtail: db 0
queue: times 64 db 0
msg_boot: db 'BOOT STAGE=', 0
msg_ready: db 'READY', 13, 10, 0
msg_grade: db 'GRADE S', 0
msg_work: db ' W', 0
msg_avg: db ' AVG=', 0
msg_lf: db 13, 10, 0
msg_saved: db 'SAVED', 0
msg_loaded: db 'LOADED', 0
msg_no_disk: db 'NO_DISK', 0
msg_empty: db 'EMPTY', 0
msg_bad_format: db 'BAD_FORMAT', 0
msg_bad_version: db 'UNSUPPORTED_VERSION', 0
msg_bad_checksum: db 'BAD_CHECKSUM', 0
msg_bad_grade: db 'BAD_GRADE', 0
