import re
from typing import Tuple

class Simplifier:
    def __init__(self):
        pass

    #def simplify(self, input_string: str) -> str:
    #    input_string = self.clean_string(input_string)
    #
    #    while True:
    #        match = self.find_polynomial_expression(input_string)
    #        if not match:
    #            break
    #        input_string = self.expand_polynomial(input_string, match)
    #        print(f'Expanded expression: {input_string}')
    #
    #    terms = self.split_terms(input_string)
    #    terms = [self.set_limits(term.strip()) for term in terms]
    #    input_string = "+".join(terms)
    #    return input_string

    def simplify(self, input_string: str) -> str:
        input_string = self.clean_string(input_string)
        print('Input:     ' + input_string)
        input_string = self.simplify_fractions(input_string)
        print('Fractions: ' + input_string)
        input_string = self.apply_gaussian_integration(input_string)
        print('Gauss:     ' + input_string)
        terms = [input_string]
        while any(re.search(r'\(([A-Z])-([A-Z])\)\^2', term) for term in terms):
            expanded_terms = []
            for term in terms:
                if match := re.search(r'\(([A-Z])-([A-Z])\)\^2', term):
                    pulse1, pulse2 = match.groups()
                    expanded_terms.append(term.replace(match.group(0),
                                                       f'F{{1}}{{{pulse1}^2}}*SUM{{(F{{{pulse2}}}{{{pulse1}}})^n*C_n({pulse1 + pulse2})}}',
                                                       1))
                    expanded_terms.append(term.replace(match.group(0),
                                                       f'F{{1}}{{{pulse2}^2}}*SUM{{(F{{{pulse1}}}{{{pulse2}}})^n*C_n({pulse1 + pulse2})}}',
                                                       1))
                else:
                    expanded_terms.append(term)
            terms = expanded_terms
        terms = [self.set_limits(term) for term in terms]
        input_string = "+".join(terms)
        print('Decompose: ' + input_string)
        return input_string


    def clean_string(self, input_string: str) -> str:
        return "".join(input_string.split())


    def separate_constants(self, factors: list[str]) -> Tuple[list[str], list[str]]:
        """
        Разделяет множители на числовые/константные и переменные.
        """
        constants = []
        variables = []

        for factor in factors:
            if re.match(r'^[0-9PI\^\(\)]+$', factor):  # Константы типа '2', 'PI', '2*PI^4'
                constants.append(factor)
            else:  # Остальные множители считаются переменными
                variables.append(factor)
        return constants, variables


    def simplify_fractions(self, input_string: str) -> str:
        gauss_integral_pattern = re.compile(r'INT#\{F\{(.*)(dS\^\{[A-Z]\}_\{mu\})([^}]*)\}\{([^}]+)\}\}')
        gauss_integral_match = gauss_integral_pattern.search(input_string)

        numerator_multiplier1 = gauss_integral_match.group(1)
        numerator_multiplier2 = gauss_integral_match.group(3)
        denominator = gauss_integral_match.group(4)

        if numerator_multiplier1 or numerator_multiplier2 or denominator:
            fraction = 'F{' + numerator_multiplier1 + numerator_multiplier2 + '}{' + denominator + '}'
            modified_expression = 'INT#{' + gauss_integral_match.group(2) + '}'
            input_string = gauss_integral_pattern.sub(modified_expression, input_string)
            input_string = f'{fraction}*{input_string}'
        return input_string
        #def process_fraction(match: re.Match) -> str:
        #    numerator, denominator = match.groups()
        #
        #    # Разделяем числитель и знаменатель на множители
        #    numerator_multipliers = numerator.split('*')
        #    denominator_multipliers = denominator.split('*')
        #
        #    # Фильтруем числовые и буквенные множители
        #    numerator_constants, numerator_variables = self.separate_constants(numerator_multipliers)
        #    denominator_constants, denominator_variables = self.separate_constants(denominator_multipliers)
        #
        #    # Формируем обновленную строку с вынесенными множителями
        #    const_part = f"F{{{''.join(numerator_constants)}}}{{{''.join(denominator_constants)}}}" if numerator_constants or denominator_constants else ""
        #    var_part = f"F{{{'*'.join(numerator_variables)}}}{{{'*'.join(denominator_variables)}}}" if numerator_variables or denominator_variables else ""
        #
        #    # Формируем итоговую строку
        #    if const_part and var_part:
        #        return f"{const_part}*{var_part}"
        #    return const_part or var_part
        #
        #fraction_pattern = re.compile(r'F\{([^}]*)\}\{([^}]*)\}')

        # Замена всех найденных дробей с использованием process_fraction
        #result = fraction_pattern.sub(process_fraction, input_string)
        #return result


    def apply_gaussian_integration(self, input_string: str) -> str:
        #pulse_pattern = re.compile(r'(F\{.*?)([A-Z]_\{mu\})(.*?\}\{.*?\})')
        pulse_pattern = re.compile(r'(F\{[^F]*)([A-Z])_\{mu\}([^}]*\}\{.*?[^}]+\})')

        pulse_match = pulse_pattern.search(input_string)
        if pulse_match:
            pulse = pulse_match.group(2)
            #integral_pattern = re.compile(fr'INT#\{{dS\^\{{{pulse}\}}\}}')
            integral_pattern = re.compile(rf'INT#\{{dS\^\{{{pulse}\}}_\{{mu\}}\}}')
            integral_match = integral_pattern.search(input_string)
            if integral_match:
                # remove pulse from denominator
                fraction_replace = pulse_match.group(1) + pulse_match.group(3)
                input_string = pulse_pattern.sub(fraction_replace, input_string, count=1)
                # Take integral
                result = f'2*PI^2*{pulse}^4'
                input_string = integral_pattern.sub(result, input_string, count=1)
        return input_string


        #if match:
            #result = f'2*PI^2*{pulse}^4'
            #input_string = integral_match.sub(modified_integral, input_string, count=1)
        #    input_string = pattern.sub('', input_string, count=1)  # Удаляем выражение из строки
        #    input_string = result + '*' + input_string  # Переносим в начало
        #return input_string

    def find_polynomial_expression(self, input_string: str):
        pattern = re.compile(r'\(([A-Z])-([A-Z])\)\^2')
        return pattern.search(input_string)

    #def find_the_last_polynomial(self, input_string: str) -> str:
    #    search_pattern = re.compile(
    #        r'.*F\{.*\}\{.*(\(([A-Z])-([A-Z])\)\^2)\}.*'
    #    )
    #
    #    match = re.search(search_pattern, input_string)
    #    polinom = match.group(1)
    #    print(polinom)
    #    pulse1 = match.group(2)
    #    print(pulse1)
    #    pulse2 = match.group(3)
    #    print(pulse2)

    def expand_polynomial(self, input_string: str, match) -> str:
        pulse1, pulse2 = match.groups()

        first_term = f'F{{1}}{{{pulse1}^2}} * SUM{{(F{{{pulse2}}}{{{pulse1}}})^n * C_n({pulse1 + pulse2})}}'
        second_term = f'F{{1}}{{{pulse2}^2}} * SUM{{(F{{{pulse1}}}{{{pulse2}}})^n * C_n({pulse1 + pulse2})}}'

        expanded_expression = first_term + ' + ' + second_term

        return input_string[:match.start()] + expanded_expression + input_string[match.end():]

    #def expand_into_polynomials(self, input_string: str) -> str:
    #    search_pattern = re.compile(
    #        r'.*F\{.*\}\{.*(\(([A-Z])-([A-Z])\)\^2)\}.*'
    #    )
    #
    #    match = re.search(search_pattern, input_string)
    #    if not match:
    #        raise ValueError("Не удалось найти подходящее выражение в строке.")
    #
    #    full_expression = match.group(1)
    #    pulse1 = match.group(2)
    #    pulse2 = match.group(3)
    #
    #    first_member = input_string.replace(full_expression, f'F{{1}}{{{pulse1}^2}}*SUM{{(F{{{pulse2}}}{{{pulse1}}})^n*C_n({pulse1 + pulse2})}}')
    #    second_member = input_string.replace(full_expression, f'F{{1}}{{{pulse2}^2}}*SUM{{(F{{{pulse1}}}{{{pulse2}}})^n*C_n({pulse1 + pulse2})}}')
    #
    #    modified_string = first_member + '+' + second_member
    #    return modified_string

    def find_polinoms(self, expression: str) -> str:
        search_pattern = r"INT\(C_(\d+)\(([A-Z][A-Z])\)C_(\d+)\(([A-Z][A-Z])\)domega\)"

        # Поиск всех совпадений
        matches = re.findall(search_pattern, expression)

        if matches:
            print("Найденные совпадения:")
            for match in matches:
                print(match)  # Выводит кортежи групп, например: ('1', 'QL', '2', 'LQ')
        else:
            pass # Придумать что-то

        return expression

    def simplify_polinom(self, expression: str) -> str:
        search_pattern = re.compile(
            r'INT\(F\(C_(\w+)\(([A-Z])([A-Z])\)C_(\w+)\(([A-Z])([A-Z])\)\)\(2\*PI\^2\)dOMEGA\)'
        )

        def create_replacement(match):
            index1 = match.group(1)
            pulse1 = match.group(2)
            pulse2 = match.group(3)
            index2 = match.group(4)
            pulse3 = match.group(5)
            pulse4 = match.group(6)

            if {pulse1, pulse2} == {pulse3, pulse4}:
                return f'delta_{index1}{index2}'
            return match.group(0)

        return re.sub(search_pattern, create_replacement, expression)

    def split_terms(self, input_string: str):
        return input_string.split("+")

    def define_limits(self, input_string: str):
        pass

    def set_limits(self, input_string: str):
        search_pattern = re.compile(r'\bINT\b')
        upper_limit = 'b'
        lower_limit = 'a'

        definite_integral = f'INT_{lower_limit}^{upper_limit}'
        modified_string = re.sub(search_pattern, definite_integral, input_string)
        return modified_string