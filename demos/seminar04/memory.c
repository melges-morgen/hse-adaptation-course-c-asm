/* Linux x86-64 LP64: sizes, byte offsets, byte order; run with -g -O0. */
#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

__attribute__((noinline))
static void show_memory(const char *letters, const int *numbers,
                        const long *wide, const uint32_t *x) {
    const unsigned char *bytes = (const unsigned char *)x;
    printf("sizeof: char=%zu int=%zu long=%zu pointer=%zu\n",
           sizeof(char), sizeof(int), sizeof(long), sizeof(void *));
    printf("offsets: char=%td int=%td long=%td\n",
           (const unsigned char *)&letters[1] - (const unsigned char *)&letters[0],
           (const unsigned char *)&numbers[1] - (const unsigned char *)&numbers[0],
           (const unsigned char *)&wide[1] - (const unsigned char *)&wide[0]);
    printf("0x12345678 bytes: %02X %02X %02X %02X\n",
           bytes[0], bytes[1], bytes[2], bytes[3]);
    printf("address: x=%p, first byte=%p\n", (const void *)x, (const void *)bytes);
    assert(bytes[0] == 0x78 && bytes[1] == 0x56 && bytes[2] == 0x34 && bytes[3] == 0x12);
    assert(numbers[0] == 10 && numbers[1] == 20 && numbers[2] == 30);
}

int main(void) {
    _Static_assert(CHAR_BIT == 8, "expected 8-bit bytes");
    _Static_assert(sizeof(int) == 4 && sizeof(long) == 8 && sizeof(void *) == 8,
                   "expected Linux x86-64 LP64");
    char letters[4] = {'A', 'B', 'C', '\0'};
    int numbers[3] = {10, 20, 30};
    long wide[3] = {100, 200, 300};
    uint32_t x = UINT32_C(0x12345678);
    show_memory(letters, numbers, wide, &x);
    return 0;
}
