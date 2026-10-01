#!/bin/sh
set -eu
work="${SEMINAR4_WORK:-work/seminar04}"
test -f "$work/journal.asm" || { printf '%s\n' 'Скопируйте полный журнал в рабочий каталог; команды приведены в demos/seminar04/README.md' >&2; exit 2; }
JOURNAL_SOURCE="$work/journal.asm" JOURNAL_OUT="$work/artifacts/stage6" \
    sh demos/lecture04-journal/build.sh 6
