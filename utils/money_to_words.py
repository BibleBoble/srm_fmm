from decimal import Decimal, ROUND_HALF_UP


_ONES_MASCULINE = (
    "ноль", "один", "два", "три", "четыре", "пять", "шесть",
    "семь", "восемь", "девять", "десять", "одиннадцать",
    "двенадцать", "тринадцать", "четырнадцать", "пятнадцать",
    "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"
)
_ONES_FEMININE = (
    "ноль", "одна", "две", "три", "четыре", "пять", "шесть",
    "семь", "восемь", "девять", "десять", "одиннадцать",
    "двенадцать", "тринадцать", "четырнадцать", "пятнадцать",
    "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"
)
_TENS = (
    "", "", "двадцать", "тридцать", "сорок", "пятьдесят",
    "шестьдесят", "семьдесят", "восемьдесят", "девяносто"
)
_HUNDREDS = (
    "", "сто", "двести", "триста", "четыреста", "пятьсот",
    "шестьсот", "семьсот", "восемьсот", "девятьсот"
)
_GROUPS = (
    ("", "", "", False),
    ("тысяча", "тысячи", "тысяч", True),
    ("миллион", "миллиона", "миллионов", False),
    ("миллиард", "миллиарда", "миллиардов", False),
)


def _noun_form(number, forms):
    last_two = number % 100
    if 11 <= last_two <= 14:
        return forms[2]
    last_digit = number % 10
    if last_digit == 1:
        return forms[0]
    if last_digit in (2, 3, 4):
        return forms[1]
    return forms[2]


def _spell_group(number, feminine=False):
    words = []
    hundreds = number // 100
    tens = number % 100
    if hundreds:
        words.append(_HUNDREDS[hundreds])
    if tens >= 20:
        words.append(_TENS[tens // 10])
        tens %= 10
    if tens:
        ones = _ONES_FEMININE if feminine else _ONES_MASCULINE
        words.append(ones[tens])
    return words


def _integer_to_russian_words(number):
    if number == 0:
        return _ONES_MASCULINE[0]

    groups = []
    while number:
        groups.append(number % 1000)
        number //= 1000
    if len(groups) > len(_GROUPS):
        raise ValueError("Сумма превышает поддерживаемый предел в 999 миллиардов рублей.")

    words = []
    for index in range(len(groups) - 1, -1, -1):
        group_value = groups[index]
        if not group_value:
            continue
        singular, paucal, plural, feminine = _GROUPS[index]
        words.extend(_spell_group(group_value, feminine))
        if singular:
            words.append(_noun_form(group_value, (singular, paucal, plural)))
    return " ".join(words)


def amount_to_russian_words(amount):
    """Форматирует сумму в рублях прописью с копейками."""
    value = Decimal(amount)
    if not value.is_finite() or value < 0:
        raise ValueError("Сумма должна быть конечным неотрицательным числом.")
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rubles = int(rounded)
    kopecks = int((rounded - rubles) * 100)
    if rubles > 999_999_999_999:
        raise ValueError("Сумма превышает поддерживаемый предел в 999 миллиардов рублей.")

    ruble_words = _integer_to_russian_words(rubles)
    ruble_form = _noun_form(rubles, ("рубль", "рубля", "рублей"))
    kopeck_form = _noun_form(kopecks, ("копейка", "копейки", "копеек"))
    words = f"{ruble_words} {ruble_form} {kopecks:02d} {kopeck_form}"
    return words[0].upper() + words[1:]
