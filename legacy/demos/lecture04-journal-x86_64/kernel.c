/* Historical x86-64 QEMU teaching machine. No libc or guest operating system. */
#include <stdint.h>
#include <stddef.h>

#ifndef STAGE
#define STAGE 6
#endif

#define STUDENTS 16
#define WORKS 4
#define UNSET 0xffu
#define VGA ((volatile uint16_t *)0xb8000)

static inline void out8(uint16_t port, uint8_t v) {
    __asm__ volatile ("outb %0,%1" : : "a"(v), "Nd"(port));
}
static inline uint8_t in8(uint16_t port) {
    uint8_t v;
    __asm__ volatile ("inb %1,%0" : "=a"(v) : "Nd"(port));
    return v;
}
static void serial_init(void) {
    out8(0x3f9, 0);
    out8(0x3fb, 0x80);
    out8(0x3f8, 3);
    out8(0x3f9, 0);
    out8(0x3fb, 3);
    out8(0x3fa, 0xc7);
}
static void serial_char(char c) {
    for (unsigned n = 0; n < 100000; n++) if (in8(0x3fd) & 0x20) break;
    out8(0x3f8, (uint8_t)c);
}
static void serial(const char *s) { while (*s) serial_char(*s++); }
static void serial_number(unsigned n) {
    if (n >= 10) serial_number(n / 10);
    serial_char((char)('0' + n % 10));
}
static void vtext(unsigned row, unsigned col, const char *s, uint8_t color) {
    while (*s && row < 25 && col < 80) VGA[row * 80 + col++] = ((uint16_t)color << 8) | (uint8_t)*s++;
}
static void vchar(unsigned row, unsigned col, char c, uint8_t color) {
    if (row < 25 && col < 80) VGA[row * 80 + col] = ((uint16_t)color << 8) | (uint8_t)c;
}
static void clear(void) {
    for (unsigned i = 0; i < 80 * 25; i++) VGA[i] = 0x0720;
}
static void number2(unsigned row, unsigned col, unsigned n, uint8_t color) {
    vchar(row, col, (char)('0' + n / 10), color);
    vchar(row, col + 1, (char)('0' + n % 10), color);
}

static uint8_t grade[STUDENTS][WORKS];
static unsigned selected_student, selected_work;
static char notice[64];
static void set_notice(const char *s) {
    unsigned i = 0;
    while (s[i] && i < sizeof notice - 1) { notice[i] = s[i]; i++; }
    notice[i] = 0;
    serial(s);
    serial("\n");
}
static void redraw(void) {
    clear();
    vtext(0, 1, "COURSE GRADES - NO GUEST OS", 0x1f);
    vtext(1, 1, "arrows:select 0-9/A:grade Backspace:clear S:save L:load", 0x07);
#if STAGE == 1
    vtext(4, 2, "S01  grade 07", 0x0f);
#else
    vtext(3, 2, "ID     W1   W2   W3   W4    AVG", 0x0b);
    for (unsigned i = 0; i < STUDENTS; i++) {
        unsigned r = 4 + i;
        vtext(r, 2, "S", 0x0f);
        number2(r, 3, i + 1, 0x0f);
        unsigned sum = 0, count = 0;
        for (unsigned j = 0; j < WORKS; j++) {
            unsigned col = 9 + 5 * j;
            uint8_t g = grade[i][j];
            uint8_t color = i == selected_student && j == selected_work ? 0x70 : 0x0f;
            if (g == UNSET) vtext(r, col, "--", color);
            else { number2(r, col, g, color); sum += g; count++; }
        }
#if STAGE >= 5
        if (!count) vtext(r, 31, "--.--", 0x07);
        else {
            unsigned hundredths = (sum * 100 + count / 2) / count;
            number2(r, 31, hundredths / 100, 0x0a);
            vchar(r, 33, '.', 0x0a);
            number2(r, 34, hundredths % 100, 0x0a);
        }
#else
        (void)sum; (void)count;
#endif
    }
    vtext(21, 2, notice, 0x0e);
#endif
    vtext(23, 2, "QEMU x86-64 / VGA / PS2 / bare metal", 0x08);
}

/* Bounded queue: IRQ owns producer, main loop owns consumer. */
static volatile uint8_t queue[64];
static volatile unsigned qhead, qtail;
static void enqueue(uint8_t code) {
    unsigned next = (qhead + 1) & 63;
    if (next != qtail) { queue[qhead] = code; qhead = next; }
}
static int dequeue(void) {
    if (qhead == qtail) return -1;
    int code = queue[qtail];
    qtail = (qtail + 1) & 63;
    return code;
}
void keyboard_irq(void) {
    if (in8(0x64) & 1) enqueue(in8(0x60));
    out8(0x20, 0x20);
}

extern void keyboard_entry(void);
struct idt_gate { uint16_t low, selector; uint8_t ist, type; uint16_t mid; uint32_t high, zero; } __attribute__((packed));
struct idtr { uint16_t limit; uint64_t address; } __attribute__((packed));
static struct idt_gate idt[256];
static void keyboard_enable(void) {
    uintptr_t p = (uintptr_t)keyboard_entry;
    idt[33] = (struct idt_gate){(uint16_t)p, 8, 0, 0x8e, (uint16_t)(p >> 16), (uint32_t)(p >> 32), 0};
    struct idtr desc = { sizeof idt - 1, (uintptr_t)idt };
    __asm__ volatile ("lidt %0" : : "m"(desc));
    /* Legacy PIC remap: IRQ0..7 -> 0x20..0x27, IRQ8..15 -> 0x28..0x2f. */
    out8(0x20, 0x11); out8(0xa0, 0x11);
    out8(0x21, 0x20); out8(0xa1, 0x28);
    out8(0x21, 4); out8(0xa1, 2);
    out8(0x21, 1); out8(0xa1, 1);
    out8(0x21, 0xfd); /* only IRQ1; IRQ0 remains masked */
    out8(0xa1, 0xff);
    while (in8(0x64) & 1) (void)in8(0x60);
    __asm__ volatile ("sti");
}

/* ATA primary master PIO, 28-bit LBA. Exactly one 512-byte sector at LBA 1. */
#if STAGE >= 6
static uint8_t sector[512];
static int ata_wait(void) {
    for (unsigned n = 0; n < 2000000; n++) {
        uint8_t s = in8(0x1f7);
        if (s == 0 || s == 0xff) return 0;
        if (!(s & 0x80)) {
            if (s & 0x21) return 0;
            if (s & 8) return 1;
        }
    }
    return 0;
}
static inline void out16(uint16_t port, uint16_t v) {
    __asm__ volatile ("outw %0,%1" : : "a"(v), "Nd"(port));
}
static inline uint16_t in16(uint16_t port) {
    uint16_t v;
    __asm__ volatile ("inw %1,%0" : "=a"(v) : "Nd"(port));
    return v;
}
static int disk_io(int write) {
    out8(0x1f6, 0xe0);
    out8(0x1f2, 1); out8(0x1f3, 1); out8(0x1f4, 0); out8(0x1f5, 0);
    out8(0x1f7, write ? 0x30 : 0x20);
    if (!ata_wait()) return 0;
    for (unsigned i = 0; i < 256; i++) {
        if (write) out16(0x1f0, (uint16_t)(sector[i*2] | ((uint16_t)sector[i*2+1] << 8)));
        else { uint16_t w = in16(0x1f0); sector[i*2] = (uint8_t)w; sector[i*2+1] = (uint8_t)(w >> 8); }
    }
    if (write) {
        out8(0x1f7, 0xe7); /* flush device write cache */
        for (unsigned n = 0; n < 2000000; n++) {
            uint8_t s = in8(0x1f7);
            if (s == 0 || s == 0xff || (s & 0x21)) return 0;
            if (!(s & 0x80)) return 1;
        }
        return 0;
    }
    return 1;
}
static uint32_t checksum(void) {
    uint32_t c = 2166136261u;
    for (unsigned i = 0; i < 72; i++) c = (c ^ sector[i]) * 16777619u;
    return c;
}
static void save(void) {
    for (unsigned i = 0; i < 512; i++) sector[i] = 0;
    sector[0] = 'G'; sector[1] = 'R'; sector[2] = 'D'; sector[3] = '4';
    sector[4] = 1; sector[5] = STUDENTS; sector[6] = WORKS;
    for (unsigned i = 0; i < STUDENTS; i++)
        for (unsigned j = 0; j < WORKS; j++) sector[8 + i * WORKS + j] = grade[i][j];
    uint32_t c = checksum();
    for (unsigned i = 0; i < 4; i++) sector[72 + i] = (uint8_t)(c >> (8 * i));
    set_notice(disk_io(1) ? "SAVED" : "NO_DISK");
}
static void load(void) {
    if (!disk_io(0)) { set_notice("NO_DISK"); return; }
    if (!sector[0] && !sector[1] && !sector[2] && !sector[3]) { set_notice("EMPTY"); return; }
    if (sector[0] != 'G' || sector[1] != 'R' || sector[2] != 'D' || sector[3] != '4') { set_notice("BAD_FORMAT"); return; }
    if (sector[4] != 1 || sector[5] != STUDENTS || sector[6] != WORKS || sector[7] != 0) { set_notice("UNSUPPORTED_VERSION"); return; }
    uint32_t stored = 0;
    for (unsigned i = 0; i < 4; i++) stored |= (uint32_t)sector[72 + i] << (8 * i);
    if (stored != checksum()) { set_notice("BAD_CHECKSUM"); return; }
    for (unsigned i = 0; i < STUDENTS * WORKS; i++)
        if (sector[8 + i] != UNSET && sector[8 + i] > 10) { set_notice("BAD_GRADE"); return; }
    for (unsigned i = 0; i < STUDENTS; i++)
        for (unsigned j = 0; j < WORKS; j++) grade[i][j] = sector[8 + i * WORKS + j];
    set_notice("LOADED");
}
#endif

static int extended;
static void report_grade(void) {
    serial("GRADE S"); serial_number(selected_student + 1);
    serial(" W"); serial_number(selected_work + 1);
    serial("=");
    unsigned g = grade[selected_student][selected_work];
    if (g == UNSET) serial("--"); else serial_number(g);
#if STAGE >= 5
    unsigned sum = 0, count = 0;
    for (unsigned j = 0; j < WORKS; j++) if (grade[selected_student][j] != UNSET) { sum += grade[selected_student][j]; count++; }
    serial(" AVG=");
    if (!count) serial("--.--");
    else {
        unsigned v = (sum * 100 + count / 2) / count;
        serial_number(v / 100); serial_char('.');
        serial_char((char)('0' + v % 100 / 10));
        serial_char((char)('0' + v % 10));
    }
#endif
    serial("\n");
}
static void handle(int scan) {
    if (scan == 0xe0) { extended = 1; return; }
    if (scan & 0x80) { extended = 0; return; }
    if (extended) {
        extended = 0;
        if (scan == 0x48 && selected_student) selected_student--;
        else if (scan == 0x50 && selected_student + 1 < STUDENTS) selected_student++;
        else if (scan == 0x4b && selected_work) selected_work--;
        else if (scan == 0x4d && selected_work + 1 < WORKS) selected_work++;
        else return;
        report_grade(); redraw(); return;
    }
    unsigned value = 0;
    if (scan >= 0x02 && scan <= 0x0a) value = (unsigned)(scan - 0x01);
    else if (scan == 0x0b) value = 0;
    else if (scan == 0x1e) value = 10; /* A */
    else if (scan == 0x0e) value = UNSET; /* Backspace */
#if STAGE >= 6
    else if (scan == 0x1f) { save(); redraw(); return; } /* S */
    else if (scan == 0x26) { load(); redraw(); report_grade(); return; } /* L */
#endif
    else return;
    grade[selected_student][selected_work] = (uint8_t)value;
    report_grade(); redraw();
}

void kmain(void) {
    serial_init();
    serial("BOOT STAGE="); serial_number(STAGE); serial("\n");
    for (unsigned i = 0; i < STUDENTS; i++) for (unsigned j = 0; j < WORKS; j++) grade[i][j] = UNSET;
#if STAGE >= 6
    load();
#endif
    redraw();
#if STAGE >= 4
    keyboard_enable();
#endif
    serial("READY\n");
    for (;;) {
#if STAGE == 3
        if (in8(0x64) & 1) handle(in8(0x60));
#elif STAGE >= 4
        int code = dequeue();
        if (code >= 0) handle(code);
        else __asm__ volatile ("pause");
#else
        __asm__ volatile ("hlt");
#endif
    }
}
