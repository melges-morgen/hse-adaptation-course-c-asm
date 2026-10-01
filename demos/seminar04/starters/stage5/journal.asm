; BIOS уже прочитал код с дискеты в RAM по адресу 1000:0000.
; Этап 5: целочисленное среднее по выставленным оценкам.
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
    mov al, '5'
    call serial_char
    mov si, msg_lf
    call serial_str
    mov di, grades              ; ES:DI → начало массива оценок
    mov cx, 64                  ; нужно заполнить 64 байта
    mov al, UNSET               ; FF = «нет оценки» (0 — оценка)
    rep stosb                   ; повторить запись AL в ES:DI 64 раза
    call redraw                 ; с версии 2 писать напрямую в VGA
    call install_irq1
    mov si, msg_ready
    call serial_str
.loop:
    call dequeue
    jc .loop
    call handle_scan
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
    xor cl, cl                  ; ЗАДАНИЕ 5: прибавить count/2
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
.next_student:
    pop cx
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

; В AL приходит скан-код из очереди IRQ1.
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
.done:
    pop dx
    pop cx
    pop bx
    pop ax
    ret

; IRQ1 идёт через вектор 09h PIC; начиная с версии 4 INT 16h не читаем.
install_irq1:
    cli                         ; не принимать IRQ, пока меняем IVT
    xor ax, ax                  ; AX = 0
    mov es, ax                  ; ES = 0: IVT начинается с адреса 0000:0000
    mov word [es:9*4], irq1     ; вектор 09h: смещение обработчика
    mov ax, cs                  ; AX = сегмент кода обработчика
    mov word [es:9*4+2], ax     ; вектор 09h: сегмент обработчика
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
    sti                         ; PIC готов: снова разрешить IRQ
    ret

irq1:
    push ax                     ; сохранить используемые регистры
    push bx
    push ds
    mov ax, cs                  ; данные очереди лежат в нашем сегменте
    mov ds, ax                  ; DS → очередь и её индексы
    in al, 0x64                 ; прочитать статус PS/2
    test al, 1                  ; установлен ли бит готовых данных?
    jz .eoi                     ; если нет, просто подтвердить IRQ
    in al, 0x60                 ; прочитать байт клавиши
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
    mov al, 0x20                ; команда EOI для PIC
    out 0x20, al                ; сообщить о завершении IRQ
    pop ds                      ; восстановить регистры в обратном порядке
    pop bx
    pop ax
    iret                        ; вернуть сохранённые адрес и флаги

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
    jmp .average
.number:
    xor ah, ah
    call serial_uint
.average:
    mov si, msg_avg
    call serial_str
    mov bl, [student]
    xor bh, bh
    shl bx, 2
    mov cx, WORKS               ; пройти четыре оценки студента
    xor dx, dx                  ; DL = количество, DH = сумма
.sum:
    mov al, [grades+bx]        ; взять оценку из RAM
    cmp al, UNSET              ; сравнить с FF («нет оценки»)
    je .skip                   ; пропустить FF
    inc dl                     ; увеличить число оценок
    add dh, al                 ; прибавить оценку к сумме
.skip:
    inc bx                     ; перейти к следующему байту
    loop .sum                  ; уменьшить CX и повторить, пока CX ≠ 0
    test dl, dl
    jnz .have
    mov si, missing_avg
    call serial_str
    jmp .endavg
.have:
    mov [current_count], dl    ; сохранить количество оценок
    xor ax, ax                 ; AX = 0
    mov al, dh                 ; AX = сумма
    mov bx, 100                ; перейти от единиц к сотым
    mul bx                     ; DX:AX = сумма × 100
    xor ch, ch
    mov cl, [current_count]
    xor cl, cl                  ; ЗАДАНИЕ 5: прибавить count/2
    add ax, cx
    xor ch, ch
    mov cl, [current_count]
    xor dx, dx                 ; старшая часть делимого равна нулю
    div cx                     ; AX = округлённое среднее в сотых
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
headings: db 'ID     W1   W2   W3   W4    AVG', 0
footer_text: db 'QEMU PC / BIOS / VGA / PS2 / real mode', 0
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
