#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    const char *message = getenv("COURSE_MESSAGE");
    int status = 0;

    if (message == NULL) {
        message = "<не задана>";
    }

    for (int i = 0; i < argc; ++i) {
        printf("argv[%d]=%s\n", i, argv[i]);
    }
    printf("COURSE_MESSAGE=%s\n", message);

    if (argc > 1 && strncmp(argv[1], "--status=", 9) == 0) {
        char *end = NULL;
        long parsed = strtol(argv[1] + 9, &end, 10);
        if (end == argv[1] + 9 || *end != '\0' || parsed < 0 || parsed > 125) {
            fprintf(stderr, "process-demo: ожидается код от 0 до 125\n");
            return 2;
        }
        status = (int)parsed;
    }

    int ch;
    while ((ch = getchar()) != EOF) {
        if (putchar(ch) == EOF) {
            fprintf(stderr, "process-demo: ошибка записи в stdout\n");
            return 3;
        }
    }
    if (ferror(stdin)) {
        fprintf(stderr, "process-demo: ошибка чтения stdin\n");
        return 4;
    }
    if (fflush(stdout) == EOF) {
        fprintf(stderr, "process-demo: ошибка записи в stdout\n");
        return 3;
    }

    fprintf(stderr, "process-demo: завершение с кодом %d\n", status);
    return status;
}
