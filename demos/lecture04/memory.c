/* Lecture 4 demonstration: specifically Linux x86-64, LP64, little-endian. */
#include <assert.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern void add_middle(int *a);
/* The NASM labels mark the instruction bytes used in the slides. */
extern const unsigned char trace_start[];

struct S { char c; int x; };

static void show_array(const char *label, const int a[3]) {
    printf("%s: %d %d %d\n", label, a[0], a[1], a[2]);
}

int main(void) {
    _Static_assert(CHAR_BIT == 8, "8-bit bytes required");
    _Static_assert(sizeof(int) == 4, "32-bit int required");
    _Static_assert(sizeof(long) == 8 && sizeof(void *) == 8, "LP64 required");
    printf("sizeof: char=%zu int=%zu long=%zu pointer=%zu\n",
           sizeof(char), sizeof(int), sizeof(long), sizeof(void *));

    uint32_t x = UINT32_C(0x12345678);
    const unsigned char expected[] = {0x78, 0x56, 0x34, 0x12};
    const unsigned char *bytes = (const unsigned char *)&x;
    assert(memcmp(bytes, expected, sizeof x) == 0);
    printf("0x12345678:");
    for (size_t i = 0; i < sizeof x; ++i) printf(" %02X", (unsigned)bytes[i]);
    putchar('\n');

    int a[3] = {10, 20, 30};
    const int result[] = {10, 25, 30};
    assert(sizeof a == 12);
    for (size_t i = 0; i < 3; ++i) {
        /* Object representation of the whole array: byte offsets are defined. */
        assert((unsigned char *)&a[i] == (unsigned char *)&a + i * sizeof a[0]);
        printf("a[%zu]: address=%p byte offset=%zu\n", i, (void *)&a[i], i * sizeof a[0]);
    }
    show_array("before", a);
    add_middle(a);
    for (size_t i = 0; i < 3; ++i) assert(a[i] == result[i]);
    show_array("after NASM", a);

    const unsigned char machine_code[] = {
        0x8b, 0x43, 0x04, 0x83, 0xc0, 0x05, 0x89, 0x43, 0x04
    };
    assert(memcmp(trace_start, machine_code, sizeof machine_code) == 0);
    puts("NASM instruction bytes: 8B 43 04 | 83 C0 05 | 89 43 04");

    int *p = malloc(3 * sizeof *p);
    if (p == NULL) return EXIT_FAILURE;
    p[0] = 10;
    p[1] = 20;
    p[2] = 30;
    p[1] += 5;
    for (size_t i = 0; i < 3; ++i) assert(p[i] == result[i]);
    show_array("after C, dynamic storage", p);
    free(p);
    p = NULL;

    assert(offsetof(struct S, x) == 4 && sizeof(struct S) == 8);
    printf("struct S: offset(x)=%zu size=%zu\n", offsetof(struct S, x), sizeof(struct S));
    puts("Lecture 4: sizes, bytes, array addresses, NASM and C results — OK");
}
