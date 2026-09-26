# Journal variant implementation plan

> Исторический план для x86-64. Действующий журнал перешёл на 16-битный NASM
> и описан в `../specs/2026-09-26-lecture04-real-mode-design.md`.

> **For agentic workers:** implement inline in this session; maintain checklist.

**Goal:** runnable staged bare-metal journal and synchronized lecture materials.

**Architecture:** Multiboot2/NASM bootstrap enters long mode; freestanding C
implements VGA, PS/2 polling/IRQ, table, arithmetic, ATA PIO. QEMU monitor and
serial allow deterministic hardware smoke tests. Reveal HTML supplies PDF.

**Tech Stack:** NASM, freestanding GCC, GRUB2, QEMU x86_64, Python, Docker,
Reveal.js, LaTeX.

## Global Constraints

- Keep original lecture04 intact and retain all previous uncommitted work.
- Docker for builds and emulator; no TeX/compiler/emulator host requirement.
- Russian course prose; no generated images/PDF/ISO/disk committed.

## Tasks

- [x] Boot: `demos/lecture04-journal/boot.asm`, `link.ld`, Dockerfile, build script;
      QEMU loads a 64-bit C kernel; serial and VGA boot marker observed.
- [x] Hardware/journal: `kernel.c`, `irq.asm`, stage flags; six runnable stages,
      keyboard inputs, averages, disk sector validation and error messages.
- [x] Integration tests: Python QEMU monitor script runs boot/input/disk cases;
      `make lecture4-journal-check` verifies all stages.
- [x] Course materials: add alternative LaTeX fragment to chapter 2 after
      main lecture, Reveal.js HTML with notes and diagrams, registry and Makefile.
- [x] Publishing/documentation: README, AGENTS, workflow artifacts/Pages/release.
- [x] Verification: QEMU integration, Docker PDF/slide builds, inspect logs,
      browser HTML, static PDF and git diff --check.

No commit or push unless explicitly requested.

## Verification evidence

- `make lecture4-journal` built the handbook and HTML/PDF in Docker, compiled
  all six GRUB ISOs, and ran QEMU integration checks successfully.
- Tests covered stage 3 polling, stages 4–6 IRQ1, grades 0 and 10,
  correction/clear, 0.67 rounding, reboot/restore, invalid key, missing disk,
  damaged magic/checksum, incompatible version, invalid score and RAM
  preservation on failed reload.
- Первоначальная сборка до редакторского прохода: 48 основных и 6
  дополнительных слайдов, 54 страницы PDF 16:9. После согласованных правок
  численность пересмотрена ниже. PDF содержит снимок реального экрана QEMU.
- noVNC in Firefox: version 6 booted with an empty disk, grade 5 entered with
  keyboard and reflected on VGA. The container was stopped after the check.
- `make pdf` generated the table of contents and the alternative section;
  the LaTeX log has no overfull/warnings in `lecture04_journal.tex`. Existing
  warnings elsewhere in the handbook were not modified.
- `git diff --check` returned successfully. No generated ISO, disk or PDF is
  staged or committed.

## Замечания к следующему проходу — применены

- Слайд 2 (`slides/lecture04-journal/index.html`): заголовок «Задача»;
  сократить постановку, поскольку преподаватель подробнее проговорит
  требования устно. Оставить:
  - данные: «Оценки студентов группы»;
  - действия: «Вводить, изменять и сохранять оценки; смотреть статистику»;
  - вопрос: «С чего начать, если нет готовых библиотек и решений?»
- Слайд 3: заголовок «Какие аппаратные средства у нас есть?»; перед таблицей
  кратко представить учебный x86-64 компьютер с ОЗУ, диском и устройствами;
  отдельно упомянуть BIOS и загрузчик GRUB. В серой подписи пояснить, что для
  лабораторной работы QEMU PC (i440FX) используется как виртуальная модель
  целого компьютера с выбранными устройствами.
- Слайд 4: заголовок «Версия 1: начнём с самого простого»; пояснить, что
  `S01 → 07` означает оценку 7 студенту S01. Добавить заметки и короткий
  прокомментированный фрагмент C-вывода в VGA, например вызов
  `vtext(4, 2, "S01 grade 07", ...)` и запись символа/атрибута цвета.
  Если код не поместится, выделить ему отдельный слайд. Стартовый код GRUB/NASM
  оставить для последующего блока о запуске.
- Слайд 5 («Загрузить — не то же, что исполнять»): пояснить цепочку запуска
  учебной машины QEMU PC в режиме BIOS/El Torito. BIOS выполняет POST и базовую
  инициализацию, выбирает CD-ROM, загружает стартовый образ GRUB в память и
  передаёт ему управление. GRUB читает конфигурацию, размещает сегменты
  `kernel.elf` в RAM и передаёт управление точке входа Multiboot2, передавая
  Multiboot-информацию. Уточнить, что BIOS не загружает ядро журнала напрямую.
  На следующем слайде связать GRUB с NASM-кодом: переход в long mode, таблицы
  страниц, стек, затем вызов `kmain` на C. В заметках указать, что это путь
  именно BIOS/El Torito в данной конфигурации QEMU PC, не UEFI.

## Дополнение по согласованному редакторскому проходу

- После аппаратной теории показать решение на небольшом фрагменте
  **существующего** кода: GRUB/boot, VGA, массив, PS/2 polling, обработчик
  IRQ и очередь, вычисление среднего, стек, ATA PIO, сериализация и проверки.
- Демонстрировать последовательность «потребность → механизм → код →
  наблюдаемый результат»; неизменённые части листингов сокращать только с
  явной подписью, а новые кадры оставлять видимыми в статическом PDF.
- Полный текст `lecture04_journal.tex` пополнен соответствующими объяснениями
  и листингами; README демо содержит маршрут показа.
- Реестр и README синхронизированы с новой структурой: 71 основной и 6
  дополнительных слайдов, всего 77 страниц PDF.
- После редакторского прохода `make lecture4-journal` собрал пособие,
  проверил все шесть версий в QEMU и экспортировал 77 страниц PDF из HTML.
  Отчёт вёрстки: `issues=[]`, `errors=[]`; каждый слайд содержит заметки.
  Проверены в Firefox и PDF постановка задачи, BIOS/GRUB и длинные кодовые
  фрагменты после разбиения. `git diff --check` ошибок не выявил.
