#!/usr/bin/env python3
"""Независимая проверка чисел лекции №3: точные дроби и IEEE-слова."""
from fractions import Fraction as F
import math
import struct


def power(exponent):
    return F(2) ** exponent


def rn(value, precision=24, emin=-126):
    """Ближайшее двоичное значение, ties-to-even, с gradual underflow.

    Переполнение здесь не моделируется: для него отдельно проверяем
    границу binary32 и результат в C-демонстрации.
    """
    value = F(value)
    if not value:
        return F(0)
    sign = -1 if value < 0 else 1
    value = abs(value)
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < power(exponent):
        exponent -= 1
    step = power(max(exponent, emin) - precision + 1)
    scaled = value / step
    integer, remainder = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * remainder
    if twice > scaled.denominator or (twice == scaled.denominator and integer % 2):
        integer += 1
    return sign * integer * step


def word(value):
    return struct.unpack('>I', struct.pack('>f', value))[0]


def from_word(value):
    return F(struct.unpack('>f', struct.pack('>I', value))[0])


checks = 0


def check(name, actual, expected):
    global checks
    assert actual == expected, f'{name}: {actual!r} != {expected!r}'
    checks += 1
    print(f'OK: {name}')


check('точное сложение 6.5 + 0.75', rn(F(13, 2) + F(3, 4)), F(29, 4))
check('слово 7.25', word(7.25), 0x40E80000)
check('нормализация 1.5 + 1.5', rn(F(3, 2) * 2), F(3))
check('GRS ниже середины: 1.01001 -> 1.010', rn(F(41, 32), 4), F(5, 4))
check('GRS ровно середина, чётный: 1.0101', rn(F(21, 16), 4), F(5, 4))
check('GRS sticky меняет решение: 1.010101', rn(F(85, 64), 4), F(11, 8))
check('GRS ровно середина, нечётный: 1.0111', rn(F(23, 16), 4), F(3, 2))
check('перенос округления: 1.1111 -> 10.000', rn(F(31, 16), 4), F(2))
check('старый пример: округление точной суммы 1.140625', rn(F(73, 64), 3), F(5, 4))
check('binary32 середина у 1', rn(1 + power(-24)), F(1))
check('binary32 выше середины', rn(1 + power(-24) + power(-26)), 1 + power(-23))
check('слово малого слагаемого 1.01 * 2^-24', word(float(5 * power(-26))), 0x33A00000)
check('слово суммы 1 + 2^-23', word(float(1 + power(-23))), 0x3F800001)
check('точное вычитание 1.125 - 1', rn(F(9, 8) - 1), F(1, 8))
check('слово разности 0.125', word(.125), 0x3E000000)
a, b = F('1.23456789'), F('1.23456780')
check('точная десятичная разность', a - b, F(9, 10**8))
check('слово первого приближения', word(float(a)), 0x3F9E0652)
check('слово второго приближения', word(float(b)), 0x3F9E0651)
check('разность приближений точна', rn(rn(a)-rn(b)), power(-23))
check('ошибка разности около 32.45 процентов', round(float(abs(rn(a)-rn(b)-(a-b))/(a-b))*100, 2), 32.45)
check('точное умножение 1.5 * 2.5', rn(F(3, 2) * F(5, 2)), F(15, 4))
check('нормализация 1.5 * 1.5', rn(F(9, 4)), F(9, 4))
check('точное деление 3 / 1.5', rn(F(3) / F(3, 2)), F(2))
third = rn(F(1, 3))
check('округление 1/3', third, F(11184811, 33554432))
check('слово 1/3', word(float(third)), 0x3EAAAAAB)
check('абсолютная ошибка 1/3', third - F(1, 3), F(1, 100663296))
check('относительная ошибка 1/3', (third - F(1, 3)) * 3, power(-25))
check('поглощение 2^24 + 1', rn(2**24 + 1), F(2**24))
a, b, c = F(2**24), F(1), -F(2**24)
check('(a+b)+c', rn(rn(a+b)+c), F(0))
check('a+(b+c)', rn(a+rn(b+c)), F(1))
check('минимальное нормальное', from_word(0x00800000), power(-126))
check('максимальное субнормальное', from_word(0x007FFFFF), power(-126)-power(-149))
check('разность на границе normal/subnormal', rn(from_word(0x00800000)-from_word(0x007FFFFF)), power(-149))
check('точный субнормальный результат', rn(power(-126)/2), power(-127))
check('половина минимального -> ноль', rn(power(-150)), F(0))
check('полтора минимальных -> два', rn(3*power(-150)), power(-148))
check('максимальное конечное', from_word(0x7F7FFFFF), (2-power(-23))*power(127))
check('binary64 0.1 + 0.2 != 0.3', .1 + .2 == .3, False)
check('binary32 0.1f + 0.2f == 0.3f', rn(rn(F(1, 10))+rn(F(1, 5))), rn(F(3, 10)))
check('ошибка исходного примера binary64: один шаг', (.1 + .2) - .3, math.ulp(.3))
check('допуск измерения температуры', abs(F('20.004')-20) <= F('0.01'), True)
check('относительный допуск большого масштаба', F(5) <= F('0.000001')*F(100000005), True)
check('только относительный допуск у нуля не помогает', F('1e-10') <= F('1e-6')*F('1e-10'), False)
check('сначала округление входа, затем суммы при p=3', rn(1+rn(F(9, 64), 3), 3), F(1))
check('FMA: отдельное умножение и сложение', rn(rn((1+power(-23))*(1-power(-23)))-1), F(0))
check('FMA: одно округление', rn((1+power(-23))*(1-power(-23))-1), -power(-46))
check('слово 6.5', word(6.5), 0x40D00000)
check('слово 0.75', word(.75), 0x3F400000)
check('слово 1.125', word(1.125), 0x3F900000)
print(f'Лекция №3: все {checks} числовых проверок пройдены.')
