import re
from typing import Tuple

from torch.distributed import group


class Simplifier:
    def __init__(self):
        pass

    largest_pulse = 'Q'

    def simplify(self, input_string: str) -> str:
        input_string = self.clean_string(input_string)
        print(f'Input         : {input_string}')
        input_string = self.decompose_pulses(input_string)
        print(f'Decompose     : {input_string}')
        input_string = self.extract_constants_fractions(input_string)
        print(f'Fractions     : {input_string}')
        input_string = self.combine_constants(input_string)
        print(f'Constants     : {input_string}')
        input_string = self.apply_gaussian_integration(input_string)
        print(f'Gauss         : {input_string}')
        terms = self.expand_into_hyperspherical_functions(input_string)
        print(f'Hyperspherical: {"+".join(terms)}')
        #terms = [self.redistribute_terms_to_integrals(term) for term in terms]
        terms = [self.set_limits(term) for term in terms]
        terms = [term for term in terms if term] # remove empty string elements
        print(f'Limits        : {"+".join(terms)}')
        return input_string


    def clean_string(self, input_string: str) -> str:
        return "".join(input_string.split())


    def separate_constants(self,expression: str) -> tuple[str, str]:
        constants_pattern = re.compile(
            r'PI'  # "PI"
            r'|\(2\*PI\)\^\d+'  # "(2*PI)^число"
            r'|(?<!\^)\d+'  # просто число, которое не является степенью какой-то другой переменной или выражения
        )
        constants = constants_pattern.findall(expression)
        expression_constants = '*'.join(constants)

        cleaned_expression = re.sub(constants_pattern, '', expression)
        # Убираем лишние символы умножения: если * повторяется два или более раз
        cleaned_expression = re.sub(r'\*+', '*', cleaned_expression)
        # Убираем * в начале и в конце строки
        cleaned_expression = cleaned_expression.strip('*')

        return cleaned_expression, expression_constants

    def extract_constants_fractions(self, input_string: str) -> str:
        def fraction_replacer(fraction_match: re.Match) -> str:
            numerator, denominator = fraction_match.group(1), fraction_match.group(2)
            cleaned_numerator, numerator_consts = self.separate_constants(numerator)
            cleaned_denominator, denominator_consts = self.separate_constants(denominator)

            if not numerator_consts and not denominator_consts:
                return fraction_match.group(0)  # Возвращаем оригинальную дробь без изменений

            # Формирование замены для дроби без констант
            fraction_replacement = ''
            if cleaned_numerator and cleaned_denominator:
                fraction_replacement = f'F{{{cleaned_numerator}}}{{{cleaned_denominator}}}'
            elif cleaned_numerator:
                fraction_replacement = f'{cleaned_numerator}'
            elif cleaned_denominator:
                fraction_replacement = f'F{{}}{{{cleaned_denominator}}}'

            # Формирование выражения с константами
            constants_expression = ''
            if numerator_consts and denominator_consts:
                constants_expression += f'F{{{numerator_consts}}}{{{denominator_consts}}}'
            elif numerator_consts:
                constants_expression += f'{numerator_consts}'
            elif denominator_consts:
                constants_expression += f'F{{}}{{{denominator_consts}}}'

            # Заменяем старую дробь на обработанную
            replacement = f'{constants_expression}*{fraction_replacement}'.rstrip('*')
            return replacement

        # Unify extra constants in a single factors from the entire expression. Применение рекурсивной обработки дробей ко всему выражению
        fraction_pattern = re.compile(r'F\{(.*?)\}\{(.*?)\}')
        input_string = fraction_pattern.sub(fraction_replacer, input_string)

        return input_string


    def combine_constants(self, input_string: str) -> str:
        combined_numerator = ''
        combined_denominator = ''
        combined_fraction = ''
        ######################## COMBINE CONSTANTS FROM FRACTIONS ##########################
        fraction_pattern = re.compile(r'F\{(.*?)\}\{(.*?)\}')
        fractions = fraction_pattern.findall(input_string)

        for fraction in fractions:
            numerator, denominator = fraction
            cleaned_numerator, numerator_consts = self.separate_constants(numerator)
            cleaned_denominator, denominator_consts = self.separate_constants(denominator)

            # Проверяем, состоит ли дробь только из констант
            if not cleaned_numerator and not cleaned_denominator:
                # Создаем общий числитель
                if not combined_numerator and numerator_consts:
                    combined_numerator = numerator_consts
                elif combined_numerator and numerator_consts:
                    combined_numerator += f'*{numerator_consts}'

                # Создаем общий знаменатель
                if not combined_denominator and denominator_consts:
                    combined_denominator = denominator_consts
                elif combined_denominator and denominator_consts:
                    combined_denominator += f'*{denominator_consts}'

                # Удаление дроби и очистка лишних символов '*'
                pattern = rf'(\*?)F\{{{re.escape(numerator)}}}\{{{re.escape(denominator)}}}(\*?)'
                matches = re.findall(pattern, input_string)
                for left_star, right_star in matches:
                    if left_star and right_star:  # Дробь окружена '*'
                        input_string = re.sub(pattern, '*', input_string, count=1)
                    elif left_star or right_star:  # Либо слева, либо справа есть '*'
                        input_string = re.sub(pattern, '', input_string, count=1)
                    else:  # Обычное удаление без лишних '*'
                        input_string = re.sub(pattern, '', input_string, count=1)

        combined_numerator = combined_numerator.strip('*')
        combined_denominator = combined_denominator.strip('*')
        ######################## COMBINE CONSTANTS ################################

        ######################## CREATE FINAL EXPRESSION WITH CONSTANTS ################################
        if combined_numerator and combined_denominator:
            combined_fraction = f'F{{{combined_numerator}}}{{{combined_denominator}}}'
        elif combined_numerator and not combined_denominator:
            combined_fraction = f'{combined_numerator}'
        elif not combined_numerator and combined_denominator:
            combined_fraction = f'F{{}}{{{combined_denominator}}}'
        ######################## PUSHING CONSTANTS TO THE BEGINNING OF THE EXPRESSION #########################
        input_string = f'{combined_fraction}*{input_string}'
        return input_string


    def decompose_pulses(self, input_string: str) -> str:
        pattern = re.compile(r'd\^4\{([A-Z])\}')

        def replace_pulse(match):
            pulse = match.group(1)

            if pulse == 'G':  # Исключаем G (он зарезервирован под омегу)
                return match.group(0)
            return f'd{pulse}*{pulse}^3*INT{{dG_{pulse}}}'

        # Замена найденных выражений
        input_string = pattern.sub(replace_pulse, input_string)
        return input_string


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


    def expand_into_hyperspherical_functions(self, input_string):
        terms = [input_string]
        indices = ['n', 'l', 'm', 'p', 'q', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        index_number = 0
        while any(re.search(r'F\{.*?\}\{.*?\(([A-Z])-([A-Z])\)\^2.*?\}', term) for term in terms):
            expanded_terms = []
            for term in terms:
                if match := re.search(r'F\{(.*?)\}\{(.*?)\*?\(([A-Z])-([A-Z])\)\^2\*?(.*?)\}', term):
                    numerator, part1, pulse1, pulse2, part2 = match.groups()
                    denominator = ''
                    if part1 and part2:
                        denominator = f'{part1}*{part2}'
                    if part1 and not part2:
                        denominator = part1
                    if not part1 and part2:
                        denominator = part2

                    index = indices[index_number]

                    expanded_terms.append(term.replace(match.group(0), f'F{{{numerator}}}{{{denominator}}}*F{{}}{{{pulse1}^2}}*SUM{{(F{{{pulse2}}}{{{pulse1}}})^{index}*C_{index}({pulse1 + pulse2})}}', 1))
                    expanded_terms.append(term.replace(match.group(0), f'F{{{numerator}}}{{{denominator}}}*F{{}}{{{pulse2}^2}}*SUM{{(F{{{pulse1}}}{{{pulse2}}})^{index}*C_{index}({pulse1 + pulse2})}}', 1))
                else:
                    expanded_terms.append(term)
            index_number += 1
            terms = expanded_terms
        return terms


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


    def redistribute_terms_to_integrals(self, input_string: str):
        diff_var = 'K'
        integral_search_pattern = re.compile(
            rf'INT{{(.*)d{diff_var}\*{diff_var}\^3\*INT{{dG_{diff_var}}}(.*)}}'
        )
        match = re.search(integral_search_pattern, input_string)
        part1, part2 = match.groups()
        print(part1)
        print(part2)
        return input_string


    def set_limits(self, input_string: str):
        pulse_sequence = list()
        pulse_sequence.append(self.largest_pulse)

        pattern = re.compile(r'\(F\{([A-Z])\}\{([A-Z])\}\)\^[a-z]')
        pair_pulses = pattern.findall(input_string)

        for numerator, denominator in pair_pulses:
            if numerator == self.largest_pulse:
                return '' # Such expression cannot exist

            if denominator == self.largest_pulse:
                continue

            if denominator not in pulse_sequence:
                pulse_sequence.append(denominator)
                pulse_sequence.append(numerator)

        ############### FIRST PULSE
        diff_pulse = pulse_sequence[2]
        integral_search_pattern = re.compile(
            rf'INT{{(.*?)d{diff_pulse}(.*)}}'
        )
        match = re.search(integral_search_pattern, input_string)
        if match:
            upper_limit = pulse_sequence[1]
            lower_limit = '0'
            definite_integral = f'INT_{lower_limit}^{upper_limit}{{{match.group(1)}d{diff_pulse}{match.group(2)}}}'
            input_string = re.sub(integral_search_pattern, definite_integral, input_string)

        ############### SECOND PULSE
        diff_pulse = pulse_sequence[1]
        integral_search_pattern = re.compile(
            rf'INT{{(.*)d{diff_pulse}(.*)}}'
        )
        if match:
            upper_limit = pulse_sequence[0]
            lower_limit = '0'
            definite_integral = f'INT_{lower_limit}^{upper_limit}{{{match.group(1)}d{diff_pulse}{match.group(2)}}}'
            input_string = re.sub(integral_search_pattern, definite_integral, input_string)

        return input_string