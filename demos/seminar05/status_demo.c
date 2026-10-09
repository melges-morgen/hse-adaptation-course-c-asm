#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    const char *prefix = "--code=";
    char *end = NULL;
    long code;

    if (argc != 2 || strncmp(argv[1], prefix, strlen(prefix)) != 0) {
        fprintf(stderr, "ошибка: укажите --code=0..125\n");
        return 2;
    }

    errno = 0;
    code = strtol(argv[1] + strlen(prefix), &end, 10);
    if (errno != 0 || end == argv[1] + strlen(prefix) || *end != '\0' ||
        code < 0 || code > 125) {
        fprintf(stderr, "ошибка: код должен быть целым числом от 0 до 125\n");
        return 2;
    }

    printf("Программа возвращает код %ld\n", code);
    return (int)code;
}
