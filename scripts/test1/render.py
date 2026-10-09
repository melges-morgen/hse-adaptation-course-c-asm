"""Render the same problem data as printable exams and teacher keys."""


def escape(value):
    return (value.replace('\\', r'\textbackslash{}').replace('&', r'\&')
            .replace('%', r'\%').replace('#', r'\#').replace('_', r'\_')
            .replace('{', r'\{').replace('}', r'\}'))


def gate(symbol):
    return {'\\oplus': 'исключ. ИЛИ', '\\lor': 'ИЛИ', '\\land': 'И'}[symbol]


def circuit(data):
    labels = data['labels']
    a, b, c = labels[:3]
    common = [r'\begin{center}',
              r'\begin{tikzpicture}[line width=.8pt, every node/.style={font=\footnotesize},'
              r'  logic/.style={draw,align=center,minimum height=.62cm,minimum width=1.15cm}]']
    if data['inputs'] == 4:
        d = labels[3]
        common.extend([
            rf'\node[logic] (g1) at (2,4) {{{gate(data["g1"])}}};',
            rf'\node[logic] (g2) at (2,2.2) {{{gate(data["g2"])}}};',
            r'\node[logic] (g3) at (4,4) {НЕ};',
            r'\node[logic] (g4) at (4,2.2) {НЕ};',
            rf'\node[logic] (g5) at (6,3.5) {{{gate(data["g5"])}}};',
            r'\node[logic] (g6) at (6,.5) {исключ. ИЛИ};',
            r'\node[logic] (g7) at (8,2.1) {И};',
            r'\node[logic] (g8) at (9.7,2.1) {НЕ};',
            rf'\draw (0.15,4.25) node[left] {{$ {a} $}} -- ($(g1.west)+(0,.15)$);',
            rf'\draw (0.15,3.75) node[left] {{$ {b} $}} -- ($(g1.west)-(0,.15)$);',
            rf'\draw (0.15,2.45) node[left] {{$ {c} $}} -- ($(g2.west)+(0,.15)$);',
            rf'\draw (0.15,1.95) node[left] {{$ {d} $}} -- ($(g2.west)-(0,.15)$);',
            r'\draw (g1.east) -- (g3.west);',
            r'\draw (g2.east) -- (g4.west);',
            r'\draw (g3.east) -- ($(g5.west)+(0,.15)$);',
            r'\draw (g4.east) -- ($(g5.west)-(0,.15)$);',
            rf'\draw (4.8,.75) node[left] {{$ {a} $}} -- ($(g6.west)+(0,.15)$);',
            rf'\draw (4.8,.25) node[left] {{$ {c} $}} -- ($(g6.west)-(0,.15)$);',
            r'\draw (g5.east) -- ($(g7.west)+(0,.15)$);',
            r'\draw (g6.east) -- ($(g7.west)-(0,.15)$);',
            r'\draw (g7.east) -- (g8.west);',
            r'\draw (g8.east) -- (10.55,2.1) node[right] {$F$};',
        ])
    else:
        branch = data['formula'].count('\\land') > 1
        last_gate = gate(data['g5']) if branch else 'ИЛИ'
        common.extend([
            rf'\node[logic] (g1) at (2,2.5) {{{gate(data["g1"])}}};',
            r'\node[logic] (g2) at (2,.7) {НЕ};',
            r'\node[logic] (g3) at (4,2.1) {И};',
            rf'\node[logic] (g4) at (6,1.8) {{{last_gate}}};',
            r'\node[logic] (g5) at (8,1.8) {НЕ};',
            rf'\draw (0.15,2.75) node[left] {{$ {a} $}} -- (g1.west);',
            rf'\draw (0.15,2.25) node[left] {{$ {b} $}} -- (g1.west);',
            rf'\draw (0.15,.7) node[left] {{$ {c} $}} -- (g2.west);',
            r'\draw (g1.east) -- (g3.west);',
            r'\draw (g2.east) -- (g3.west);',
            r'\draw (g3.east) -- (g4.west);',
        ])
        if branch:
            common.extend([
                r'\node[logic] (g6) at (4,.1) {И};',
                rf'\draw (2.75,.3) node[left] {{$ {a} $}} -- (g6.west);',
                rf'\draw (2.75,-.2) node[left] {{$ {c} $}} -- (g6.west);',
                r'\draw (g6.east) -- (g4.west);',
            ])
        else:
            common.append(rf'\draw (4.4,1) node[left] {{$ {b} $}} -- (g4.west);')
        common.extend([r'\draw (g4.east) -- (g5.west);',
                       r'\draw (g5.east) -- (9,1.8) node[right] {$F$};'])
    return '\n'.join(common + [r'\end{tikzpicture}', r'\end{center}'])


def truth_table(data, solutions=False):
    labels = sorted(data['labels'])
    inputs = data['inputs']
    half = (1 << inputs) // 2
    columns = '|' + 'c' * inputs + '|c||' + 'c' * inputs + '|c|'
    heading = ' & '.join(labels + ['F'] + labels + ['F']) + r' \\ \hline'
    rows = []
    for first in range(half):
        cells = []
        for index in (first, first + half):
            cells.extend(str((index >> (inputs - 1 - j)) & 1) for j in range(inputs))
            cells.append(str(data['truth_alphabetical'][index]) if solutions else r'\rule{6mm}{0pt}')
        rows.append(' & '.join(cells) + r' \\ \hline')
    return '\n'.join([r'\begin{center}', r'\begingroup\scriptsize',
                      r'\renewcommand{\arraystretch}{1.2}',
                      rf'\begin{{tabular}}{{{columns}}}\hline', heading,
                      *rows, r'\end{tabular}', r'\endgroup', r'\end{center}'])


PREAMBLE = r'''\documentclass[a4paper,10pt]{article}
\usepackage[T2A]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\usepackage{tikz}
\usetikzlibrary{calc}
\usepackage{enumitem}
\geometry{top=14mm,bottom=15mm,left=18mm,right=18mm}
\setlength{\parindent}{0pt}
\setlist[enumerate]{leftmargin=*,itemsep=.5em,topsep=.4em}
\pagestyle{empty}
\begin{document}
'''


def render_document(pairs, solutions=False, duplex=False):
    pages = []
    for student, variant in pairs:
        code = student['student_id'] + (f'-L{variant.level}' if solutions else '')
        title = f'Контрольная работа № 1 --- уровень {variant.level}' if solutions else 'Контрольная работа № 1'
        lines = [r'\begingroup',
                 rf'\begin{{center}}\large\textbf{{{title}}}\end{{center}}',
                 rf'\textbf{{Студент:}} {escape(student["full_name"])}\\',
                 rf'\textbf{{Группа:}} {escape(student["group"])}-{student["subgroup"]}'
                  rf'\hfill\textbf{{Вариант:}} \texttt{{{code}}}',
                 rf'\textbf{{Seed:}} \texttt{{{variant.seed}}}',
                 r'\vspace{2mm}\hrule\vspace{2mm}']
        if solutions:
            lines.append(r'\small Для заданий 1--8 максимальные баллы: '
                         r'0,5; 0,5; 0,5; 1; 2; 2; 1; 2,5 (всего 10).')
        lines.extend([r'\small Каждый ответ запишите в указанном формате.', r'\begin{enumerate}'])
        for i, task in enumerate(variant.tasks, 1):
            weight = str(task.weight).replace('.0', '').replace('.', ',')
            ending = 'балл' if task.weight == 1 else 'балла'
            lines.append(rf'\item {task.question}' +
                         (rf' \textbf{{({weight} {ending})}}' if solutions else ''))
            if i == 8:
                lines.append(circuit(task.data))
                lines.append(truth_table(task.data, solutions))
        lines.append(r'\end{enumerate}')
        if solutions:
            lines.extend([r'\vspace{2mm}\textbf{Краткие ответы и решения}',
                          r'\begin{enumerate}[itemsep=.4em]'])
            for task in variant.tasks:
                lines.append(rf'\item \textbf{{Ответ:}} {task.answer} {task.solution}')
            lines.append(r'\end{enumerate}')
        lines.append(r'\endgroup')
        pages.append('\n'.join(lines))
    separator = r'\cleardoublepage' if duplex else r'\clearpage'
    preamble = PREAMBLE.replace('[a4paper,10pt]', '[a4paper,10pt,twoside]') if duplex else PREAMBLE
    return preamble + ('\n' + separator + '\n').join(pages) + '\n\\end{document}\n'
