#!/usr/bin/env python3
"""Build the local BPI264 lab 4 PDF from the saved Calc grade sheet."""

import argparse
import csv
import statistics
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import TypedDict


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/2026-autumn/ЛБ-4-ведомость-защиты-актуальная.ods"
ROSTER = ROOT / "groups/students.csv"
OUTPUT = ROOT / "results/2026-autumn/БПИ264/ЛБ-4/reports/ЛБ-4-results.tex"
OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
TABLE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"


class Summary(TypedDict):
    total: int
    graded: int
    ungraded: int
    submitted: int
    no_report: int
    mean: float | None
    median: float | None
    min: int | None
    max: int | None
    bins: tuple[int, ...]


def cell_text(cell):
    return "".join(cell.itertext()).strip()


def grade(cell, name):
    label = cell_text(cell)
    if not label:
        return None
    raw = cell.get(f"{{{OFFICE}}}value")
    if cell.get(f"{{{OFFICE}}}value-type") != "float" or raw != label:
        raise ValueError(f"Некорректный числовой балл: {name}: {label!r}")
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"Не целый балл: {name}: {label!r}") from error
    if not 0 <= value <= 10:
        raise ValueError(f"Балл вне шкалы 0--10: {name}: {value}")
    return value


def parse_rows(xml):
    document = ET.fromstring(xml)
    tables = document.findall(f".//{{{OFFICE}}}spreadsheet/{{{TABLE}}}table")
    if not tables or tables[0].get(f"{{{TABLE}}}name") != "Защита ЛБ4":
        raise ValueError("Не найден лист «Защита ЛБ4»")
    rows = []
    for row in tables[0].findall(f"{{{TABLE}}}table-row"):
        cells = []
        for cell in row.findall(f"{{{TABLE}}}table-cell"):
            repeats = int(cell.get(f"{{{TABLE}}}number-columns-repeated", "1"))
            if repeats < 1 or len(cells) + repeats > 7:
                raise ValueError("Лист содержит неожиданное повторение ячейки")
            cells.extend([cell] * repeats)
        if len(cells) != 7:
            raise ValueError(f"В строке {len(rows) + 2} ожидалось 7 столбцов, найдено {len(cells)}")
        name, group, variant, date = map(cell_text, cells[:4])
        report = cell_text(cells[5])
        if report not in ("Сдан", "Не сдан"):
            raise ValueError(f"Неизвестный статус отчёта: {name}: {report!r}")
        if variant not in ("", "QEMU", "Factorial"):
            raise ValueError(f"Неизвестный вариант работы: {name}: {variant!r}")
        if (report == "Сдан") != bool(variant):
            raise ValueError(f"Отчёт и вариант расходятся: {name}")
        defense = grade(cells[4], name)
        final = grade(cells[6], name)
        expected = None if defense is None else min(defense, 5) if report == "Не сдан" else defense
        if final != expected:
            raise ValueError(f"{name}: итог {final!r} не совпадает с правилом ЛБ4 ({expected!r})")
        rows.append(dict(name=name, group=group, variant=variant, date=date,
                         report=report, defense=defense, final=final))
    if len({(row["group"], row["name"]) for row in rows}) != len(rows):
        raise ValueError("Повторяющийся студент в ведомости")
    return rows


def read_roster(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        records = list(csv.DictReader(source))
    return {record["full_name"]: (record["group"], record["subgroup"])
            for record in records}


def select_group(rows, roster, group):
    expected = {name for name, (student_group, _) in roster.items() if student_group == group}
    selected = [dict(row, subgroup=roster[row["name"]][1]) for row in rows
                if row["group"] == group and row["name"] in roster
                and roster[row["name"]][0] == group]
    actual = {row["name"] for row in selected}
    if actual != expected or len(selected) != len(expected):
        raise ValueError(f"Список {group} расходится с ведомостью: нет {expected - actual}, лишние {actual - expected}")
    selected.sort(key=lambda item: (item["subgroup"], item["name"]))
    return selected


def summarize(rows) -> Summary:
    scores = [row["final"] for row in rows if row["final"] is not None]
    limits = ((0, 3), (4, 5), (6, 7), (8, 10))
    return Summary(total=len(rows), graded=len(scores), ungraded=len(rows) - len(scores),
                   submitted=sum(row["report"] == "Сдан" for row in rows),
                   no_report=sum(row["report"] == "Не сдан" for row in rows),
                   mean=statistics.mean(scores) if scores else None,
                   median=statistics.median(scores) if scores else None,
                   min=min(scores) if scores else None,
                   max=max(scores) if scores else None,
                   bins=tuple(sum(lo <= score <= hi for score in scores) for lo, hi in limits))


def escape(value):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%',
                    '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
                    '$': r'\$', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    return ''.join(replacements.get(char, char) for char in str(value))


def fmt(value, digits=1):
    return '—' if value is None else f'{value:.{digits}f}'.replace('.', ',')


def render(rows):
    overall = summarize(rows)
    by_subgroup = {subgroup: summarize([row for row in rows if row['subgroup'] == subgroup])
                   for subgroup in ('1', '2')}
    known_types = {variant: summarize([row for row in rows if row['variant'] == variant and row['final'] is not None])
                   for variant in ('QEMU', 'Factorial')}
    unknown = summarize([row for row in rows if not row['variant'] and row['final'] is not None])
    if sum(result['graded'] for result in known_types.values()) + unknown['graded'] != overall['graded']:
        raise ValueError('Не все оценённые студенты учтены в статистике вариантов')

    lines = [r'''\documentclass[a4paper,10pt]{article}
\usepackage{fontspec}
\usepackage[russian]{babel}
\usepackage{geometry}
\usepackage[table]{xcolor}
\usepackage{array,booktabs,fancyhdr}
\setmainfont{Carlito}
\setmonofont{DejaVu Sans Mono}
\geometry{left=14mm,right=14mm,top=16mm,bottom=17mm}
\definecolor{bg}{HTML}{1A1B2F}
\definecolor{panel}{HTML}{25283F}
\definecolor{accent}{HTML}{00D4AA}
\definecolor{text}{HTML}{F0F4F8}
\definecolor{muted}{HTML}{B9C5D4}
\definecolor{blue}{HTML}{8BBCFF}
\definecolor{warn}{HTML}{FFD580}
\definecolor{line}{HTML}{50556C}
\pagecolor{bg}\color{text}\arrayrulecolor{line}
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.18}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[L]{\footnotesize\color{muted}БПИ264 \textbar{} Лабораторная работа № 4}
\fancyfoot[R]{\footnotesize\color{muted}\thepage}
\newcommand{\sectitle}[2]{{\color{accent}\small\bfseries #1}\par\vspace{2mm}%
 {\color{text}\LARGE\bfseries #2}\par\vspace{3mm}%
 {\color{accent}\rule{\linewidth}{0.8pt}}\vspace{3mm}}
\newcommand{\kpi}[2]{\colorbox{panel}{\parbox[c][16mm][c]{48mm}{\centering\textcolor{accent}{\LARGE\bfseries #1}\\[-0.2mm]\textcolor{muted}{\small #2}}}}
\begin{document}
\sectitle{01 / ВЕДОМОСТЬ}{Лабораторная работа № 4}
\begingroup\footnotesize\setlength{\tabcolsep}{2pt}\renewcommand{\arraystretch}{1.17}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{69mm} >{\centering\arraybackslash}p{19mm} >{\centering\arraybackslash}p{21mm} >{\centering\arraybackslash}p{23mm} >{\centering\arraybackslash}p{18mm} >{\centering\arraybackslash}p{14mm}@{}}
\rowcolor{panel}\color{accent}\bfseries ФИО & \color{accent}\bfseries Работа & \color{accent}\bfseries Дата файла & \color{accent}\bfseries Отчёт & \color{accent}\bfseries Защита & \color{accent}\bfseries Итог \\''']
    for subgroup in ('1', '2'):
        subset = [row for row in rows if row['subgroup'] == subgroup]
        summary = by_subgroup[subgroup]
        lines.append(r'\rowcolor{panel}\multicolumn{6}{@{}l}{\strut\hspace{2mm}\color{blue}\bfseries БПИ264-' + subgroup +
                     rf' \quad ({summary["graded"]} с оценкой из {len(subset)})' + r'}\\')
        for index, row in enumerate(subset):
            prefix = r'\rowcolor{panel}' if index % 2 == 0 else ''
            name = escape(row['name'])
            variant = row['variant'] or r'\textcolor{muted}{---}'
            date = row['date'] or r'\textcolor{muted}{---}'
            status = r'\textcolor{warn}{не сдан}' if row['report'] == 'Не сдан' else 'сдан'
            if row['defense'] is None:
                last = r'\multicolumn{2}{c@{}}{\textcolor{muted}{нет оценки}}'
                lines.append(f'{prefix}{name} & {variant} & {date} & {status} & {last} '+r'\\')
            else:
                final = str(row['final'])
                if row['final'] < row['defense']:
                    final = r'\textcolor{warn}{\bfseries ' + final + '}'
                lines.append(f'{prefix}{name} & {variant} & {date} & {status} & {row["defense"]} & {final} '+r'\\')
    lines.extend([r'''\end{tabular}\endgroup
\clearpage
\sectitle{02 / ИТОГИ}{Распределение оценок}
''', r'\kpi{' + str(overall['graded']) + r'}{оценены из ' + str(overall['total']) + r'}\hfill\kpi{' + fmt(overall['mean'], 2) + r'}{средний балл из 10}\hfill\kpi{' + fmt(overall['median']) + r'}{медиана}\par\vspace{9mm}',
            r'{\large\bfseries Оценки по категориям}\par\vspace{2mm}',
            r'\begin{tabular}{@{}p{40mm}r p{76mm}r@{}}\toprule',
            r'\bfseries Категория & \bfseries Студентов & \bfseries Распределение & \bfseries Доля \\ \midrule'])
    labels = (r'0--3 \quad неуд.', r'4--5 \quad удовл.',
              r'6--7 \quad хор.', r'8--10 \quad отл.')
    for i, (label, count) in enumerate(zip(labels, overall['bins'])):
        color = r'\rowcolor{panel}' if i % 2 else ''
        length = 68 * count / overall['graded'] if overall['graded'] else 0
        bar = r'\colorbox{panel}{\makebox[68mm][l]{\textcolor{accent}{\rule{' + f'{length:.2f}' + r'mm}{2.4mm}}}}'
        percent = 100 * count / overall['graded'] if overall['graded'] else 0
        lines.append(f'{color}{label} & {count} & {bar} & {fmt(percent)}'+r'\% \\')
    lines.extend([r'\bottomrule\end{tabular}', r'\par\vspace{8mm}',
                  r'{\large\bfseries По типу работы}\par\vspace{2mm}',
                  r'\begin{tabular}{@{}lrrrrrrr@{}}\toprule',
                  r'\bfseries Работа & \bfseries Оценок & \bfseries Среднее & \bfseries Медиана & \bfseries Неуд. & \bfseries Удовл. & \bfseries Хор. & \bfseries Отл. \\ \midrule'])
    for i, (label, summary) in enumerate((*known_types.items(), ('без отчёта', unknown))):
        col = r'\rowcolor{panel}' if i % 2 else ''
        a, b, c, d = summary['bins']
        lines.append(f'{col}{label} & {summary["graded"]} & {fmt(summary["mean"], 2)} & {fmt(summary["median"])} & {a} & {b} & {c} & {d} '+r'\\')
    lines.extend([r'''\bottomrule\end{tabular}
\clearpage
\sectitle{03 / ГРУППА}{Сводка по подгруппам}
''', r'\kpi{' + str(overall['submitted']) + r'}{отчётов сдано}\hfill\kpi{' + str(overall['no_report']) + r'}{отчётов нет}\hfill\kpi{' + str(overall['ungraded']) + r'}{нет оценки}\par\vspace{11mm}',
                  r'{\large\bfseries Защита и отчёты}\par\vspace{2mm}',
                  r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
                  r'\bfseries Подгруппа & \bfseries По списку & \bfseries Отчётов & \bfseries Нет отчёта & \bfseries Оценок & \bfseries Нет оценки & \bfseries Среднее / медиана \\ \midrule'])
    for i, (label, summary) in enumerate((*((f'БПИ264-{sub}', by_subgroup[sub]) for sub in ('1', '2')), ('Вся группа', overall))):
        color = r'\rowcolor{panel}' if i == 1 else ''
        if i == 2:
            lines.append(r'\midrule')
            color = r'\bfseries '
        lines.append(f'{color}{label} & {summary["total"]} & {summary["submitted"]} & {summary["no_report"]} & {summary["graded"]} & {summary["ungraded"]} & {fmt(summary["mean"], 2)} / {fmt(summary["median"])} '+r'\\')
    lines.extend([r'\bottomrule\end{tabular}', r'\par\vspace{10mm}',
                  r'{\large\bfseries Распределение по подгруппам}\par\vspace{2mm}',
                  r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
                  r'\bfseries Подгруппа & \bfseries Оценок & \bfseries 0--3, неуд. & \bfseries 4--5, удовл. & \bfseries 6--7, хор. & \bfseries 8--10, отл. \\ \midrule'])
    for i, subgroup in enumerate(('1', '2')):
        summary = by_subgroup[subgroup]
        color = r'\rowcolor{panel}' if i else ''
        a, b, c, d = summary['bins']
        lines.append(f'{color}БПИ264-{subgroup} & {summary["graded"]} & {a} & {b} & {c} & {d} '+r'\\')
    lines.extend([r'\midrule',
                  rf'\bfseries Вся группа & {overall["graded"]} & ' + ' & '.join(map(str, overall['bins'])) + r' \\',
                  r'\bottomrule\end{tabular}',
                  r'\end{document}'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--roster', type=Path, default=ROSTER)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    with zipfile.ZipFile(args.source) as archive:
        if archive.testzip() is not None:
            raise ValueError('Повреждён ODS')
        rows = parse_rows(archive.read('content.xml'))
    selected = select_group(rows, read_roster(args.roster), 'БПИ264')
    report = render(selected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding='utf-8')
    summary = summarize(selected)
    print(f'{args.output}: {summary["total"]} студентов, {summary["graded"]} оценок, '
          f'{summary["no_report"]} без отчёта, категории {summary["bins"]}')


if __name__ == '__main__':
    main()
