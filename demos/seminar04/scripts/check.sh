#!/bin/sh
set -eu
python3 -m unittest demos.seminar04.test_prepare demos.seminar04.test_disk
python3 demos/seminar04/lab_solution.py
SEMINAR4_HELLO_SOURCE=demos/seminar04/hello.asm \
SEMINAR4_WORK=build/seminar04/hello sh demos/seminar04/scripts/build-hello.sh
python3 demos/seminar04/check_hello.py build/seminar04/hello/hello.img
JOURNAL_SOURCE=demos/seminar04/solutions/lab/journal.asm \
JOURNAL_OUT=build/seminar04/lab-solution/stage6 \
    sh demos/lecture04-journal/build.sh 6
python3 demos/seminar04/check_lab.py --image-root build/seminar04/lab-solution

for stage in 1 2 3 4 5 6; do
    JOURNAL_SOURCE="demos/seminar04/starters/stage$stage/journal.asm" \
    JOURNAL_OUT="build/seminar04/starters/stage$stage" \
        sh demos/lecture04-journal/build.sh "$stage"

    source="demos/lecture04-journal/stages/stage$stage/journal.asm"
    case "$stage" in
        2) source=demos/seminar04/solutions/stage2/journal.asm ;;
        6) source=demos/seminar04/solutions/stage6-homework/journal.asm ;;
    esac
    JOURNAL_SOURCE="$source" JOURNAL_OUT="build/seminar04/solutions/stage$stage" \
        sh demos/lecture04-journal/build.sh "$stage"
    python3 demos/seminar04/check.py --solution --stage "$stage"
done
python3 demos/seminar04/check.py --solution --homework

mkdir -p build/seminar04
gcc -std=c11 -Wall -Wextra -Werror -g -O0 demos/seminar04/memory.c -o build/seminar04/memory
build/seminar04/memory
gdb -batch -x demos/seminar04/memory.gdb build/seminar04/memory
