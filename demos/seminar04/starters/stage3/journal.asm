; BIOS уже прочитал код с дискеты в RAM по адресу 1000:0000.
; Этап 3: ввод и исправление через BIOS INT 16h.
; Запись 0x... — шестнадцатеричное число, ; начинает комментарий.
; Слева от запятой — место для результата; [адрес] — обращение к RAM.
; push/pop сохраняют/восстанавливают регистр в стеке, call/ret вызывают
; подпрограмму и возвращают управление, jmp/je/jc — переходы.
; bits/org/%define/db/dw/times — директивы сборки, не инструкции CPU.
bits 16                       ; собирать 16-битные инструкции
org 0                         ; начало кода имеет смещение 0000h
%define UNSET 0xff
%define STUDENTS 16
%define WORKS 4

entry:
    cli                         ; запретить IRQ, пока настраиваем стек
    mov ax, cs                  ; AX = сегмент загруженного кода (1000h)
    mov ds, ax                  ; DS = сегмент данных программы
    mov es, ax                  ; ES = сегмент назначения строковых команд
    mov ax, 0x7000              ; выбрать отдельный сегмент для стека
    mov ss, ax                  ; SS = 7000h
    mov sp, 0xf000              ; SP = вершина стека; стек растёт вниз
    sti                         ; разрешить IRQ после настройки стека
    call serial_init
    mov si, msg_boot
    call serial_str
    mov al, '3'
    call serial_char
    mov si, msg_lf
    call serial_str
    mov di, grades              ; ES:DI → начало массива оценок
    mov cx, 64                  ; нужно заполнить 64 байта
    mov al, UNSET               ; FF = «нет оценки» (0 — оценка)
    rep stosb                   ; повторить запись AL в ES:DI 64 раза
    call redraw                 ; с версии 2 писать напрямую в VGA
    mov si, msg_ready
    call serial_str
.loop:
    mov ah, 0x01                ; BIOS: функция проверки клавиши
    int 0x16                    ; проверить буфер клавиатуры
    jz .loop                    ; ZF=1: клавиши нет, повторить
    xor ah, ah                  ; AH=0: функция чтения клавиши
    int 0x16                    ; BIOS вернёт скан-код в AH
    mov al, ah                  ; перенести скан-код в AL
    call handle_scan            ; превратить клавишу в действие
    jmp .loop

; Ячейка VGA: физический B8000 = сегмент B800, смещение 0; 2 байта.
vga_text:                      ; BH=строка, BL=столбец, DS:SI=строка с нулём
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
    mov ax, 0xb800              ; сегмент видеопамяти VGA
    mov es, ax                  ; ES:DI будет адресом записи на экран
.next:
    lodsb                       ; прочитать символ DS:SI в AL; SI += 1
    test al, al                 ; проверить, равен ли символ нулю
    jz .done                    ; нуль означает конец строки
    mov ah, 0x0f                ; AH = атрибут цвета, AL = символ
    stosw                       ; записать AX в ES:DI; DI += 2
    jmp .next                   ; перейти к следующему символу
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
    call vga_two
    jmp .next_work
.missing:
    mov si, missing_text
    call vga_text
.next_work:
    inc dl
    cmp dl, WORKS
    jb .work
.next_student:
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

; В AL приходит скан-код из BIOS INT 16h.
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
    cmp al, 0x0e                ; Backspace
    je .erase
    cmp al, 0x7f                ; ЗАДАНИЕ 3: скан-код A
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
.done:
    pop dx
    pop cx
    pop bx
    pop ax
    ret

; COM1 — канал диагностики теста, а не экран пользователя.
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
    jmp .finish
.number:
    xor ah, ah
    call serial_uint
.finish:
    mov si, msg_lf
    call serial_str
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret

title_text: db 'COURSE GRADES - BIOS / NASM 16-BIT', 0
help_text: db 'arrows:select 0-9/A:grade Backspace:clear', 0
headings: db 'ID     W1   W2   W3   W4', 0
footer_text: db 'QEMU PC / BIOS / VGA / PS2 / real mode', 0
label_student: db 'S', 0
missing_text: db '--', 0
two_digits: times 3 db 0
notice: times 32 db 0
grades: times 64 db UNSET
student: db 0
work: db 0
extended: db 0
current_grade: db 0
msg_boot: db 'BOOT STAGE=', 0
msg_ready: db 'READY', 13, 10, 0
msg_grade: db 'GRADE S', 0
msg_work: db ' W', 0
msg_lf: db 13, 10, 0
