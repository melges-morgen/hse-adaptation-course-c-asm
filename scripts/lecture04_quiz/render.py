"""Print-ready two-page forms and separate per-subgroup teacher keys."""


def escape(value):
    replacements: dict[str, str] = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%',
                    '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{',
                    '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(replacements[char] if char in replacements else char for char in value)


PREAMBLE = r'''\documentclass[a4paper,12pt]{extarticle}
\input{assessments/lecture04/quiz-style.tex}
\begin{document}
'''


def render_student(entries):
    pages = []
    for student, forms in entries:
        for form in forms:
            title = '1 · C, GCC и GDB' if form.lab == 'C' else '2 · NASM, BIOS и QEMU'
            lines = [rf'\quiznamedheader{{{escape(student["full_name"])}}}'
                      rf'{{{escape(student["group"] + "-" + student["subgroup"])}}}'
                      rf'{{{title}}}{{{form.code}}}',
                     r'\section*{Общий блок · вопросы 1–6}',
                     r'\begin{enumerate}', r'\setlength{\itemsep}{4mm}']
            for question in form.questions[:6]:
                lines.append('\\question{' + question.prompt + '}' + ''.join(
                    '{' + option + '}' for option in question.options))
            lines.extend([r'\end{enumerate}', r'\newpage',
                          rf'\section*{{Лабораторная: {title} · вопросы 7–10}}',
                          r'\begin{enumerate}', r'\setcounter{enumi}{6}',
                          r'\setlength{\itemsep}{6mm}'])
            for question in form.questions[6:]:
                lines.append('\\question{' + question.prompt + '}' + ''.join(
                    '{' + option + '}' for option in question.options))
            lines.extend([r'\end{enumerate}', r'\answergrid'])
            pages.append('\n'.join(lines))
    return PREAMBLE + '\n\\clearpage\n'.join(pages) + '\n\\end{document}\n'


def render_key(entries, subgroup):
    lines = [r'\documentclass[a4paper,10pt]{article}',
             r'\usepackage[T2A]{fontenc}', r'\usepackage[utf8]{inputenc}',
             r'\usepackage[russian]{babel}', r'\usepackage{geometry}',
             r'\usepackage{longtable}', r'\usepackage{array}', r'\geometry{margin=16mm}',
             r'\begin{document}',
             rf'\section*{{Ключ преподавателя · {escape(subgroup)} · день {entries[0][1][0].day}}}',
             'Ответы указаны в порядке напечатанных вопросов 1–10. '
             'Каждый верный ответ — 1 балл; максимум 10.\\par\\medskip',
             r'\small\begin{longtable}{|>{\raggedright\arraybackslash}p{51mm}|p{10mm}|p{55mm}|p{29mm}|}\hline',
             r'ФИО & Работа & Код бланка & Ответы \\ \hline\endhead']
    for student, forms in entries:
        for form in forms:
            answers = ''.join(q.answer for q in form.questions)
            lines.append(f'{escape(student["full_name"])} & {form.lab} & '
                         rf'\texttt{{{form.code}}} & {answers} \\ \hline')
    lines.extend([r'\end{longtable}', r'\end{document}'])
    return '\n'.join(lines) + '\n'
