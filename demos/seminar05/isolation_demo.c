#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    int channel[2];
    int value = 41;
    int status;
    char signal_byte;
    pid_t child;
    int observe = argc == 2 && strcmp(argv[1], "--observe") == 0;

    if (argc > 2 || (argc == 2 && !observe)) {
        fprintf(stderr, "Использование: %s [--observe]\n", argv[0]);
        return 2;
    }
    setvbuf(stdout, NULL, _IONBF, 0);
    if (pipe(channel) == -1) {
        perror("pipe");
        return 1;
    }
    child = fork();
    if (child == -1) {
        perror("fork");
        close(channel[0]);
        close(channel[1]);
        return 1;
    }
    if (child == 0) {
        close(channel[0]);
        value = 99;
        printf("child pid=%ld address=%p value=%d\n",
               (long)getpid(), (void *)&value, value);
        if (write(channel[1], "x", 1) != 1) {
            perror("write");
            _exit(1);
        }
        close(channel[1]);
        if (observe) {
            sleep(8);  /* время посмотреть PID из другого терминала */
        }
        _exit(7);
    }

    close(channel[1]);
    printf("parent-before pid=%ld address=%p value=%d\n",
           (long)getpid(), (void *)&value, value);
    if (read(channel[0], &signal_byte, 1) != 1) {
        perror("read");
        close(channel[0]);
        waitpid(child, NULL, 0);
        return 1;
    }
    close(channel[0]);
    printf("parent-after pid=%ld address=%p value=%d\n",
           (long)getpid(), (void *)&value, value);
    if (waitpid(child, &status, 0) == -1) {
        perror("waitpid");
        return 1;
    }
    if (!WIFEXITED(status)) {
        fprintf(stderr, "Дочерний процесс не завершился штатно\n");
        return 1;
    }
    printf("child-exit=%d\n", WEXITSTATUS(status));
    return 0;
}
