#include <stdio.h>

unsigned long long factorial(unsigned int n)
{
    unsigned long long result = 1;
    for (unsigned int i = 1; i <= n; ++i) {
        result *= i;
    }
    return result;
}

int main(void)
{
    int n;
    if (fscanf(stdin, "%d", &n) != 1) {
        fprintf(stderr, "Ошибка ввода.\n");
        return 1;
    }
    if (n < 0 || n > 20) {
        fprintf(stderr, "Нужно 0..20.\n");
        return 1;
    }
    unsigned long long value = factorial((unsigned int)n);
    printf("factorial(%d) = %llu\n", n, value);
    return 0;
}
