"""Deterministic, independently computable control-work problems."""

import csv
import hashlib
import json
import random
import re
import struct
from decimal import Decimal, localcontext
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path

DIGITS = '0123456789ABCDEF'
WEIGHTS = (.5, .5, .5, 1, 2, 2, 1, 2.5)
CONVERSION_PAIRS = ((8, 16), (16, 8), (4, 16), (16, 4), (2, 8), (8, 2),
                    (4, 8), (8, 4), (16, 2), (2, 16))


@dataclass(frozen=True)
class Task:
    weight: float
    question: str
    answer: str
    solution: str
    data: dict


@dataclass(frozen=True)
class Variant:
    level: int
    seed: str
    fingerprint: str
    tasks: tuple[Task, ...]


def load_roster(path):
    fields = ['student_id', 'group', 'subgroup', 'full_name']
    with Path(path).open(encoding='utf-8-sig', newline='') as inp:
        reader = csv.DictReader(inp)
        if reader.fieldnames != fields:
            raise ValueError('CSV: требуются student_id,group,subgroup,full_name')
        rows = list(reader)
    ids = set()
    names = set()
    for row in rows:
        sid, group, subgroup, name = (row[k].strip() for k in fields)
        if not re.fullmatch(r'BPI\d+-\d{3,}', sid) or not re.fullmatch(r'БПИ\d+', group) or subgroup not in ('1', '2') or not name:
            raise ValueError(f'Некорректная строка CSV: {row}')
        if sid in ids or (group, name) in names:
            raise ValueError(f'Повторный student_id или ФИО: {row}')
        if not sid.startswith('BPI' + group[3:] + '-'):
            raise ValueError(f'student_id не соответствует группе: {row}')
        ids.add(sid)
        names.add((group, name))
        row.update(student_id=sid, group=group, subgroup=subgroup, full_name=name)
    return rows


def base(value, radix, width=0):
    if value < 0:
        return '-' + base(-value, radix, width)
    chars = ''
    while value:
        value, digit = divmod(value, radix)
        chars = DIGITS[digit] + chars
    return (chars or '0').rjust(width, '0')


def fraction_digits(value, radix, places):
    result = ''
    for _ in range(places):
        value *= radix
        digit = value.numerator // value.denominator
        result += DIGITS[digit]
        value -= digit
    return result, value


def decimal_text(value):
    with localcontext() as ctx:
        ctx.prec = 40
        result = format(Decimal(value.numerator) / Decimal(value.denominator), 'f')
    if F(result) != value:
        raise ValueError('Для условия нужна конечная десятичная дробь')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def round_fraction(value, radix, places):
    scaled = value * radix**places
    lower, remainder = divmod(scaled.numerator, scaled.denominator)
    rounded = lower + (2 * remainder > scaled.denominator or
                       (2 * remainder == scaled.denominator and lower % 2 == 1))
    whole, frac = divmod(rounded, radix**places)
    return f'{base(whole, radix)}.{base(frac, radix, places)}', rounded


def signed(word):
    return word - 65536 if word & 0x8000 else word


def hex_word(value):
    return base(value & 0xffff, 16, 4)


def code_word(value, radix):
    return base(value & 0xffff, radix, {2: 16, 8: 6, 16: 4}[radix])


def code_tex(value, radix):
    return rf'\texttt{{{code_word(value, radix)}}}_{{{radix}}}'


def ieee(value):
    word = struct.unpack('>I', struct.pack('>f', float(value)))[0]
    sign = str(word >> 31)
    exponent = f'{(word >> 23) & 255:08b}'
    fraction = f'{word & 0x7fffff:023b}'
    return word, sign, exponent, fraction


def logic(level, rng):
    letters = list('ABCD')
    rng.shuffle(letters)
    a, b, c, d = letters
    gate1 = rng.choice(('\\oplus', '\\lor'))
    gate2 = rng.choice(('\\land', '\\lor'))
    gate5 = rng.choice(('\\lor', '\\oplus'))
    if level == 1:
        formula = rf'\lnot\bigl((({a}{gate1} {b})\land\lnot {c})\lor {b}\bigr)'
        inputs = 3
        labels = (a, b, c)
    elif level == 2:
        formula = rf'\lnot\bigl((({a}{gate1} {b})\land\lnot {c}){gate5}({a}\land {c})\bigr)'
        inputs = 3
        labels = (a, b, c)
    else:
        formula = rf'\lnot\Bigl((\lnot({a}{gate1} {b}){gate5}\lnot({c}{gate2} {d}))\land({a}\oplus {c})\Bigr)'
        inputs = 4
        labels = (a, b, c, d)

    def op(symbol, x, y):
        return (x != y) if symbol == '\\oplus' else (x or y) if symbol == '\\lor' else (x and y)

    truth = []
    for number in range(1 << inputs):
        bits = dict(zip(labels, (bool(number & (1 << (inputs - 1 - i))) for i in range(inputs))))
        x, y, z = (bits[q] for q in labels[:3])
        first = op(gate1, x, y) and not z
        if level == 1:
            result = not (first or y)
        elif level == 2:
            result = not op(gate5, first, x and z)
        else:
            other = bits[d]
            result = not (op(gate5, not op(gate1, x, y), not op(gate2, z, other)) and (x != z))
        truth.append(int(result))
    return dict(inputs=inputs, labels=labels, g1=gate1, g2=gate2, g5=gate5,
                formula=formula, truth=truth)


def generate(student_id, level, seed):
    if level not in (1, 2, 3):
        raise ValueError('Уровень должен быть 1, 2 или 3')
    student_seed = hashlib.sha256(f'v3|{seed}|{level}|{student_id}'.encode()).hexdigest()[:24]
    rng = random.Random(int(student_seed, 16))
    tasks = []

    # 1. Binary grouping with a terminating fractional part in any direction.
    source, target = rng.choice(CONVERSION_PAIRS)
    integer = rng.randint(330, 3900)
    precision = rng.randint(6, 9 if level > 1 else 6)
    part = rng.randint(1, 2**precision - 1)
    frac = F(part, 2**precision)
    source_width = (precision + (source.bit_length() - 2)) // (source.bit_length() - 1)
    representation = (f'{base(integer, source)}.' +
                      fraction_digits(frac, source, source_width)[0])
    target_width = (precision + (target.bit_length() - 2)) // (target.bit_length() - 1)
    target_fraction = fraction_digits(frac, target, target_width)[0].rstrip('0') or '0'
    answer = f'{base(integer, target)}.{target_fraction}'
    width = source.bit_length() - 1
    bits = '.'.join(''.join(f'{int(digit, source):0{width}b}' for digit in segment)
                    for segment in representation.split('.'))
    target_bits = target.bit_length() - 1
    bit_word = 'бит' if target_bits == 1 else 'бита'
    tasks.append(Task(WEIGHTS[0], rf'Переведите ${representation}_{{{source}}}$ в основание {target} через двоичные группы.',
                      rf'${answer}_{{{target}}}$.',
                      rf'Заменяем каждую цифру группой из {width} бита: \texttt{{{bits}}}. Перегруппировываем по {target_bits} {bit_word} по обе стороны точки, дополняя края нулями; получаем ${answer}_{{{target}}}$.',
                      dict(integer=integer, fraction=str(frac), representation=representation,
                           source_radix=source, target_radix=target, answer=answer)))

    # 2. An unfamiliar radix with zeroes in the answer for level 3.
    radix = rng.choice({1: (8, 12, 16), 2: (5, 6, 8, 11, 12, 16),
                        3: (5, 6, 7, 8, 9, 11, 12, 16)}[level])
    length = 4 if radix >= 11 else 5
    digs = [rng.randrange(1, min(3, radix)), rng.randrange(1, radix), 0,
            rng.randrange(1, radix), rng.randrange(1, radix)]
    digits = ''.join(DIGITS[v] for v in digs[:length])
    value = int(digits, radix)
    tasks.append(Task(WEIGHTS[1], rf'Переведите ${value}_{{10}}$ в систему с основанием {radix}.',
                      rf'${digits}_{{{radix}}}$.',
                      rf'Последовательное деление на {radix} даёт остатки справа налево: {", ".join(reversed(digits))}. Ответ ${digits}_{{{radix}}}$.',
                      dict(radix=radix, decimal=value, digits=digits)))

    # 3. Rounding; level three carries across two fractional positions.
    radix = rng.choice((2, 4, 8, 16) if level == 3 else (4, 8, 16))
    places = {2: 10, 4: 5, 8: 4, 16: 3}[radix]
    if level == 3:
        prefix = rng.randint(1, radix**(places - 2) - 1)
        fraction = (F(prefix * radix**2 + radix**2 - 1) + F(3, 4)) / radix**places
    elif level == 2:
        leading = rng.randint(radix**(places - 2), radix**places - 2)
        leading -= leading % radix
        fraction = (F(leading) + F(3, 4)) / radix**places
    else:
        fraction = F(rng.randint(1000, 8500), 10**4)
    rounded, encoded = round_fraction(fraction, radix, places)
    decimal = decimal_text(fraction)
    raw_digits, leftover = fraction_digits(fraction - fraction.numerator // fraction.denominator, radix, places)
    next_digit = (leftover * radix).numerator // (leftover * radix).denominator
    tasks.append(Task(WEIGHTS[2], rf'Переведите ${decimal}_{{10}}$ в основание {radix} с округлением до {places} цифр после точки (ближайшее, при равенстве расстояний --- к чётной младшей цифре).',
                      rf'${rounded}_{{{radix}}}$.',
                      rf'Умножение остатка на {radix} даёт первые {places} цифр \texttt{{{raw_digits}}}; следующая цифра~--- \texttt{{{DIGITS[next_digit]}}}. После округления получаем ${rounded}_{{{radix}}}$.',
                      dict(radix=radix, fraction=str(fraction), decimal=decimal, places=places, rounded=rounded)))

    # 4. Borrowing through zero digits in an unfamiliar radix.
    radix = rng.choice((5, 6, 7, 8, 9, 11, 12, 16))
    start = 10000 if level == 3 else rng.randint(2200, 7700)
    if level == 3:
        first = '10000.00'
        minuend = F(radix**4)
    else:
        first = base(start, radix) + '.00'
        minuend = F(start)
    small = rng.randint(radix + 1, min(radix**2 - 1, 45))
    two = rng.randint(1, radix - 1) * radix + rng.randint(1, radix - 1)
    sub = F(small) + F(two, radix**2)
    result = minuend - sub
    answer_int = result.numerator // result.denominator
    answer_frac, rem = fraction_digits(result - answer_int, radix, 2)
    assert rem == 0
    subtext = f'{base(small, radix)}.{base(two, radix, 2)}'
    answer = f'{base(answer_int, radix)}.{answer_frac}'
    tasks.append(Task(WEIGHTS[3], rf'Вычислите ${first}_{{{radix}}}-{subtext}_{{{radix}}}$. Ответ запишите в основании {radix}.',
                      rf'${answer}_{{{radix}}}$.',
                      rf'Вычитаем по разрядам, заимствуя через нули. Проверка: точная разность в десятичной системе равна $\frac{{{result.numerator}}}{{{result.denominator}}}$; в основании {radix} это ${answer}_{{{radix}}}$.',
                      dict(radix=radix, first=first, second=subtext, result=answer)))

    # 5. Additive inverse / missing addend in a 16-bit word.
    a = rng.randint(110, 400)
    b = -rng.randint(420, 950)
    result = a + b
    given_radix = rng.choice((2, 8, 16))
    answer_radix = rng.choice((2, 8, 16))
    if level == 3:
        question = (rf'В 16-битном дополнительном коде $A={a}_{{10}}$, '
                    rf'а код суммы $A+B$ равен ${code_tex(result, given_radix)}$. '
                    rf'Найдите знаковое значение $B$ и запишите его 16-битный код в основании {answer_radix}.')
        answer = rf'$B={b}_{{10}}$, код ${code_tex(b, answer_radix)}$.'
    else:
        question = rf'Числа $A={a}_{{10}}$ и $B={b}_{{10}}$ представлены в 16-битном дополнительном коде. Запишите код суммы $A+B$ в основании {given_radix}' + (' и укажите, есть ли знаковое переполнение.' if level == 2 else '.')
        answer = rf'${code_tex(result, given_radix)}$, ${result}_{{10}}$' + (', знакового переполнения нет.' if level == 2 else '.')
    tasks.append(Task(WEIGHTS[4], question, answer,
                      rf'Коды $A={hex_word(a)}_{{16}}$, $B={hex_word(b)}_{{16}}$. Сложение по модулю $2^{{16}}$ даёт ${code_tex(result, given_radix)}$ ({result} десятичное); неизвестный операнд: ${result}-{a}={b}$, его код ${code_tex(b, answer_radix)}$.',
                      dict(a=a, b=b, result=result, result_hex=hex_word(result), b_hex=hex_word(b),
                           given_radix=given_radix, answer_radix=answer_radix,
                           given_code=code_word(result, given_radix), answer_code=code_word(b, answer_radix))))

    # 6. Shift original operands independently before signed subtraction.
    a, b = -rng.randint(75, 490), rng.randint(21, 65)
    sa = rng.randint(1, 3) if level > 1 else 0
    sb = rng.randint(1, 2) if level == 3 else 0
    a_radix = rng.choice((8, 10, 16))
    b_radix = rng.choice((8, 10, 16))
    answer_radix = rng.choice((2, 8, 16))
    shifted_a, shifted_b = a >> sa, b << sb
    result = shifted_a - shifted_b
    question = (rf'Даны знаковые числа $A=-{base(-a, a_radix)}_{{{a_radix}}}$ '
                rf'и $B={base(b, b_radix)}_{{{b_radix}}}$. Используйте 16-битный дополнительный код. ')
    if sa:
        question += rf'Арифметически сдвиньте $A$ вправо на {sa} {"разряд" if sa == 1 else "разряда"}. '
    if sb:
        question += rf'Логически сдвиньте $B$ влево на {sb} {"разряд" if sb == 1 else "разряда"}. '
    question += (r'Вычтите значение $B$ из значения $A$ после сдвигов' +
                 (r' (операнд без сдвига берите исходным)' if level < 3 else '') +
                 rf'. Запишите 16-битный код результата в основании {answer_radix}.')
    tasks.append(Task(WEIGHTS[5], question, rf'${code_tex(result, answer_radix)}$.',
                      rf'После сдвигов $A\mathbin{{\to}}{shifted_a}$, $B\mathbin{{\to}}{shifted_b}$. Разность ${shifted_a}-({shifted_b})={result}$; её 16-битный код ${code_tex(result, answer_radix)}$.',
                      dict(a=a, b=b, shift_a=sa, shift_b=sb, result=result, code=hex_word(result),
                           a_radix=a_radix, b_radix=b_radix, a_digits=base(-a, a_radix),
                           b_digits=base(b, b_radix), answer_radix=answer_radix,
                           answer_code=code_word(result, answer_radix))))

    # 7. Binary32 carry into the exponent at level 3.
    if level == 3:
        exponent = rng.randint(7, 11)
        value = (F(2**exponent) - F(rng.randint(1, 3), 10**7)) * rng.choice((-1, 1))
    elif level == 2:
        value = -(F(rng.randint(100, 890), 1000))
    else:
        value = F(rng.randint(65, 700)) + F(rng.choice((125, 375, 625, 875)), 1000)
    decimal = decimal_text(value)
    word, sign, exp, bits = ieee(value)
    tasks.append(Task(WEIGHTS[6], rf'Представьте ${decimal}_{{10}}$ в IEEE 754 \texttt{{float32}} (округление к ближайшему, при равенстве расстояний --- к чётному). Ответ запишите в 16-ричной форме: восемь цифр, включая ведущие нули.',
                      rf'$\texttt{{{base(word, 16, 8)}}}_{{16}}$.',
                      rf'Бит знака~--- {sign}; хранимый порядок~--- \texttt{{{exp}}}. После округления значащей части получаем \texttt{{{bits}}}; полное слово ${base(word, 16, 8)}_{{16}}$.' + (' При округлении единица переносится в следующий порядок.' if level == 3 else ''),
                      dict(decimal=decimal, word=base(word, 16, 8), sign=sign, exponent=exp, fraction_bits=bits)))

    circuit = logic(level, rng)
    alphabetical = sorted(circuit['labels'])
    sorted_truth = []
    for number in range(2 ** circuit['inputs']):
        bits = {label: (number >> (circuit['inputs'] - 1 - i)) & 1
                for i, label in enumerate(alphabetical)}
        original_index = sum(bits[label] << (circuit['inputs'] - 1 - i)
                             for i, label in enumerate(circuit['labels']))
        sorted_truth.append(circuit['truth'][original_index])
    circuit['truth_alphabetical'] = sorted_truth
    tasks.append(Task(WEIGHTS[7],
                      'Постройте таблицу истинности функции, реализуемой схемой ниже: заполните столбец $F$ в шаблоне. Пересечение проводов без точки не означает соединения.',
                      rf'Значения $F$ по строкам шаблона: \texttt{{{"".join(map(str, sorted_truth))}}}.',
                      rf'Последовательно вычисляем выходы элементов схемы. Выражение $F={circuit["formula"]}$ даёт значения из заполненного столбца таблицы.',
                      circuit))
    fingerprint = hashlib.sha256(json.dumps([t.data for t in tasks], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return Variant(level, student_seed, fingerprint, tuple(tasks))
