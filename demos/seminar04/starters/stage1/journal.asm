; BIOS уже прочитал код с дискеты в RAM по адресу 1000:0000.
; Этап 1: BIOS выводит одну запись без таблицы.
; Запись 0x... — шестнадцатеричное число, ; начинает комментарий.
; Слева от запятой — место для результата; [адрес] — обращение к RAM.
; push/pop сохраняют/восстанавливают регистр в стеке, call/ret вызывают
; подпрограмму и возвращают управление, jmp/je/jc — переходы.
; bits/org/%define/db/dw/times — директивы сборки, не инструкции CPU.
bits 16                       ; собирать 16-битные инструкции
org 0                         ; начало кода имеет смещение 0000h

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
    mov al, '1'
    call serial_char
    mov si, msg_lf
    call serial_str
    mov ax, 0x0003              ; BIOS-функция установки текстового режима
    int 0x10                    ; вызвать видеосервис BIOS
    mov si, first_record        ; DS:SI → строка первой оценки
    call bios_text              ; вывести строку через BIOS
    mov si, msg_ready
    call serial_str
.loop:
    hlt
    jmp .loop

bios_text:                     ; версия 1: вывод через BIOS INT 10h
    push ax
    push bx
.next:
    lodsb                       ; следующий символ DS:SI → AL
    test al, al                 ; AL равен нулю?
    jz .done                    ; если да, строка закончилась
    mov ah, 0x0e                ; функция BIOS: вывести символ
    mov bx, 0x0007              ; BH=0: видеостраница; BL=07h
    int 0x10                    ; BIOS выводит символ AL
    jmp .next                   ; повторить цикл
.done:
    pop bx
    pop ax
    ret

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
first_record: db 'S01  grade --', 0 ; ЗАДАНИЕ 1: вывести 07
msg_boot: db 'BOOT STAGE=', 0
msg_ready: db 'READY', 13, 10, 0
msg_lf: db 13, 10, 0
