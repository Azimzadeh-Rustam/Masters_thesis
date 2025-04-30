import re
from dataclasses import replace
from typing import Tuple
from collections import defaultdict
from torch.distributed import group
import sympy as sp


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
        terms = [self.set_limits(term) for term in terms]
        terms = [term for term in terms if term] # remove empty string elements
        print(f'Limits        : {"+".join(terms)}')
        terms = [self.integrate_polinoms(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Polinoms      : {"+".join(terms)}')
        terms = [self.delta_convolution(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Delta conv.   : {"+".join(terms)}')
        terms = [self.decompose_fractions(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Decompose frac: {"+".join(terms)}')
        terms = [self.simplify_fractions(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Simplify frac : {"+".join(terms)}')
        terms = [self.unify_powers(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Unify powers  : {"+".join(terms)}')
        terms = [self.redistribute_terms_to_integrals(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Redistribution: {"+".join(terms)}')
        terms = [self.integrate(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Integrate     : {"+".join(terms)}')
        terms = [self.simplify_fractions(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Simplify frac : {"+".join(terms)}')
        terms = [self.take_dzetta(term) for term in terms]
        terms = [self.clean_stars(term) for term in terms]
        print(f'Dzetta func   : {"+".join(terms)}')
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


    def clean_stars(self, input_string: str) -> str:
        # 1. Заменяем подряд идущие звёздочки на одну
        input_string = re.sub(r'\*{2,}', '*', input_string)

        # 2. Удаляем звёздочку после {
        input_string = re.sub(r'\{\*', '{', input_string)

        # 3. Удаляем звёздочку перед }
        input_string = re.sub(r'\*\}', '}', input_string)

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


    def integrate_polinoms(self, expression: str) -> str:
        polynomial_pattern = re.compile(r'C_([a-z])\(([A-Z])([A-Z])\)')

        # Взятие интеграла по двум разным полиномам Чебышева
        while True:
            polynomials = re.findall(polynomial_pattern, expression)
            found = False

            for (index1, pulse11, pulse12) in polynomials:
                for (index2, pulse21, pulse22) in polynomials:
                    if index1 == index2:
                        continue
                    if {pulse11, pulse12} == {pulse21, pulse22}:
                        continue
                    polynomial_pulses_1 = {pulse11, pulse12}
                    polynomial_pulses_2 = {pulse21, pulse22}
                    common_pulse = polynomial_pulses_1.intersection(polynomial_pulses_2)
                    if common_pulse:
                        common_pulse = common_pulse.pop()
                        angle_pattern = re.compile(rf'INT{{dG_{common_pulse}}}')
                        if re.search(angle_pattern, expression):
                            unique_pulses_in_polynomial1 = (polynomial_pulses_1 - polynomial_pulses_2).pop()
                            unique_pulses_in_polynomial2 = (polynomial_pulses_2 - polynomial_pulses_1).pop()
                            replacement = f'F{{}}{{{index2}+1}}*DELTA_{index1}{index2}*C_{index2}({unique_pulses_in_polynomial1}{unique_pulses_in_polynomial2})'

                            expression = re.sub(angle_pattern, '', expression, 1)
                            expression = re.sub(rf'C_{index1}\({pulse11}{pulse12}\)', '', expression, 1)
                            expression = re.sub(rf'C_{index2}\({pulse21}{pulse22}\)', replacement, expression, 1)
                            expression = '2*PI^2*' + expression
                            found = True
                            break
                if found:
                    break
            if not found:
                break

        # Взятие интеграла по двум одинаковым полиномам Чебышева
        while True:
            polynomials = re.findall(polynomial_pattern, expression)
            found = False

            for (index1, pulse11, pulse12) in polynomials:
                for (index2, pulse21, pulse22) in polynomials:
                    if index1 == index2:
                        continue
                    if {pulse11, pulse12} == {pulse21, pulse22}:
                        angle_pattern = re.compile(rf'INT{{dG_[{pulse11}{pulse12}]}}')
                        if re.search(angle_pattern, expression):
                            replacement = f'DELTA_{index1}{index2}'

                            expression = re.sub(angle_pattern, '', expression, 1)
                            expression = re.sub(rf'C_{index1}\({pulse11}{pulse12}\)', '', expression, 1)
                            expression = re.sub(rf'C_{index2}\({pulse21}{pulse22}\)', replacement, expression, 1)
                            expression = '2*PI^2*' + expression
                            found = True
                            break
                if found:
                    break
            if not found:
                break

        # Поиск одиночных полиномов C_n(XY), интегрируемых как DELTA_n0
        while True:
            polynomial_match = re.search(polynomial_pattern, expression)
            if not polynomial_match:
                break
            index, pulse1, pulse2 = polynomial_match.groups()
            angle_pattern = re.compile(rf'INT{{dG_[{pulse1}{pulse2}]}}')
            if re.search(angle_pattern, expression):
                replacement = f'DELTA_{index}0'

                expression = re.sub(angle_pattern, '', expression, 1)
                expression = re.sub(rf'C_{index}\({pulse1}{pulse2}\)', replacement, expression, 1)
                expression = '2*PI^2*' + expression
            else:
                break

        return expression


    def delta_convolution(self, input_expression):
        sum_pattern = re.compile(r'SUM\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}')
        delta_pattern = re.compile(r'DELTA_[a-z][0a-z]')

        def process_sum(match):
            sum_content = match.group(1)
            return sum_content

        while True:
            sum_match = re.search(sum_pattern, input_expression)
            delta_match = re.search(delta_pattern, input_expression)
            if not sum_match or not delta_match:
                break
            input_expression = re.sub(delta_pattern, '', input_expression, 1)
            input_expression = re.sub(sum_pattern, process_sum, input_expression, 1)

        return input_expression


    def split_terms(self, input_string: str):
        return input_string.split("+")


    def decompose_fractions(self, input_string: str):
        fraction_pattern = re.compile(r'\(F\{([A-Z])\}\{([A-Z])\}\)\^([a-z])')
        while match:=re.search(fraction_pattern, input_string):
            pulse1 = match.group(1)
            pulse2 = match.group(2)
            power = match.group(3)
            replacement = f'{pulse1}^{power}*{pulse2}^-{power}'
            input_string = re.sub(re.escape(match.group(0)), replacement, input_string, count=1)
        return input_string


    def simplify_fractions(self, input_string: str):
        fraction_pattern = re.compile(r'F\{(.*?)\}\{(.*?)\}')

        # уточнить что перед и после этих выражений не может стоять знак плюс либо минус
        factors_pattern = re.compile(
            r'\([^\(\)]+\)(?:\^\-?\d+)?'
            r'|[A-Z]\^\{\d+\*n[\+\-]\d+\}'
            r'|[A-Z](?:\^\-?\d+)?'
            r'|^\+\d+(?:\^\-?\d+)?' 
            r'|PI(?:\^\d+)?'
            r'|\d+\*n[\+\-]\d+'
        )

        def process_fraction(match):
            numerator = match.group(1).strip()
            denominator = match.group(2).strip()

            processed_factors = []
            factors_num = factors_pattern.findall(numerator)
            if factors_num:
                for factor in factors_num:
                    factor = factor.strip()
                    if not factor:
                        continue
                    processed_factors.append(factor)

            factors_den = factors_pattern.findall(denominator)
            if factors_den:
                for factor in factors_den:
                    factor = factor.strip()
                    if not factor:
                        continue
                    if '^' in factor:
                        base, power = factor.split('^', 1)
                        #new_power = f'-{{{power}}}' if len(power) > 1 else f'-{power}'
                        new_power = f'-{power}'
                        processed_factors.append(f'{base}^{new_power}')
                    else:
                        if len(factor) > 1:
                            processed_factors.append(f'{{{factor}}}^-1')
                        else:
                            processed_factors.append(f'{factor}^-1')
            return '*'.join(processed_factors)

        input_string = fraction_pattern.sub(process_fraction, input_string)

        return input_string


    def unify_powers(self, input_string: str) -> str:
        pulse_pattern = re.compile(r'([A-Z])\^(-?[a-z])')
        matches = re.findall(pulse_pattern, input_string)
        if matches:
            for pulse, power in matches:
                search = re.compile(rf'{pulse}\^{power}')
                if power.startswith('-'):
                    replacement = f'{pulse}^-n'
                else:
                    replacement = f'{pulse}^n'
                input_string = re.sub(search, replacement, input_string)
        return input_string


    #def unify_powers(self, input_string: str) -> str:
    #    pulse_pattern = re.compile(r'([A-Z])\^(-?[a-z])')
    #    matches = re.findall(pulse_pattern, input_string)
    #    if matches:
    #        unique_pulses = list()
    #        unique_pulses.append(matches[0][0])
    #        for pulse, _ in matches:
    #            if pulse not in unique_pulses:
    #                unique_pulses.append(pulse)
    #
    #        for unique_pulse in unique_pulses:
    #            unique_pulse_powers = list()
    #            is_negative_power = list()
    #            for pulse, power in matches:
    #                if unique_pulse == pulse:
    #                    if power.startswith('-'):
    #                        is_negative_power.append(True)
    #                        power = power.lstrip('-')
    #                    else:
    #                        is_negative_power.append(False)
    #                    if power not in unique_pulse_powers:
    #                        unique_pulse_powers.append(power)
    #
    #            if len(unique_pulse_powers) > 1:
    #                for number, unique_pulse_power in enumerate(unique_pulse_powers):
    #                    if is_negative_power[number]:
    #                        search = re.compile(rf'{unique_pulse}\^-{unique_pulse_power}')
    #                        replacement = f'{unique_pulse}^-{unique_pulse_powers[0]}'
    #                    else:
    #                        search = re.compile(rf'{unique_pulse}\^{unique_pulse_power}')
    #                        replacement = f'{unique_pulse}^{unique_pulse_powers[0]}'
    #                    input_string = re.sub(search, replacement, input_string)
    #    return input_string


    def redistribute_terms_to_integrals(self, input_string: str):
        DIFFS = ['Q', 'K', 'L']
        for diff in DIFFS:
            # Шаблон для поиска одного интеграла
            integral_search_pattern = re.compile(
                rf'(INT_[0A-Z]\^[A-Z]){{d{diff}\*{diff}\^3}}'
            )
            integral_match = re.search(integral_search_pattern, input_string)

            if integral_match:
                integral = integral_match.group(0)
                variable_pattern = re.compile(rf'(?<!d)(?<!\^)(?<!_){diff}\^?([-\da-z]+)?')
                variable_matches = re.findall(variable_pattern, input_string)
                if variable_matches:
                    powers = [sp.sympify(power) for power in variable_matches]
                    total_power = sp.Add(*powers)
                    total_power = str(total_power).strip().replace(' ', '')
                    total_power = f'{{{total_power}}}'

                    # Удаляем импульсы
                    input_string = re.sub(variable_pattern, '', input_string)

                    # Формируем итоговый импульс
                    final_pulse = f"{diff}^{total_power}" if total_power else diff
                    replacement = f'{integral_match.group(1)}{{{final_pulse}*d{diff}}}'
                    # Заменяем интеграл
                    integral_pattern_replace = re.compile(
                        rf'(INT_[0A-Z]\^[A-Z]){{d{diff}\*}}'
                    )
                    input_string = re.sub(integral_pattern_replace, replacement, input_string, count=1)

        return input_string


    def redistribute_terms_to_integrals2(self, input_string: str):
        DIFFS = ['Q', 'K', 'L']
        for diff in DIFFS:
            integral_search_pattern = re.compile(
                rf'(INT_[0A-Z]\^[A-Z]){{(.*?)\*d{diff}}}'
            )
            integral_match = re.search(integral_search_pattern, input_string)
            if integral_match:
                integral = integral_match.group(0)
                variable_pattern = re.compile(rf'(?<!d)(?<!\^)(?<!_){diff}\^?{{?(-?\d*\*?n(?:[+-]\d+)?|-?\d+|[a-z])?}}?')
                variable_matches = re.findall(variable_pattern, input_string)
                if variable_matches:
                    powers = [sp.sympify(power) for power in variable_matches]
                    total_power = sp.Add(*powers)
                    total_power = str(total_power).strip().replace(' ', '')
                    total_power = f'{{{total_power}}}'
                    # Удаляем импульсы
                    input_string = re.sub(variable_pattern, '', input_string)
                    # Формируем итоговый импульс
                    final_pulse = f"{diff}^{total_power}" if total_power else diff
                    replacement = f'{integral_match.group(1)}{{{final_pulse}*d{diff}}}'
                    # Заменяем интеграл
                    integral_pattern_replace = re.compile(
                        rf'(INT_[0A-Z]\^[A-Z]){{\*d{diff}}}'
                    )
                    input_string = re.sub(integral_pattern_replace, replacement, input_string, count=1)
        return input_string


    def process_single_integral(self, integral_match, input_string: str) -> str:
        integral_var = integral_match.group(0).strip()
        lower_limit_var = integral_match.group(1).strip()
        upper_limit_var = integral_match.group(2).strip()
        pulse_var = integral_match.group(3).strip()
        power_var = integral_match.group(4).strip() if integral_match.group(4) else '1'
        diff_var = integral_match.group(5).strip()

        try:
            var_names = set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b',
                                       f"{lower_limit_var} {upper_limit_var} {power_var} {diff_var}"))
            local_syms = {name: sp.Symbol(name, real=True, positive=True) for name in var_names}

            diff_sym = local_syms[diff_var]
            power_sym = sp.sympify(str(power_var), locals=local_syms)
            lower_limit_sym = sp.sympify(str(lower_limit_var), locals=local_syms)
            upper_limit_sym = sp.sympify(str(upper_limit_var), locals=local_syms)

            integrand = diff_sym ** power_sym

            result = sp.integrate( integrand, (diff_sym, lower_limit_sym, upper_limit_sym), risch=False)
            result = sp.simplify(result)
            result = sp.expand(result, deep=True)
            result = sp.simplify(result)

            if isinstance(result, sp.Piecewise):
                result = result.args[0][0]
                result = sp.expand(result, deep=True)

            if isinstance(result, sp.Add):
                terms = result.as_ordered_terms()
                terms = [str(sp.simplify(term)) for term in terms]
                cleaned_terms = []
                for term in terms:
                    term = re.sub(r'-?0\*\*\(.*?\)', '0', term)
                    term = sp.simplify(term)
                    cleaned_terms.append(term)
                result = sum(cleaned_terms)
                result = sp.simplify(result)

            # Представим как дробь
            num, den = sp.fraction(result)
            num = sp.simplify(num)
            den = sp.simplify(den)

            num = str(num).replace(' ', '')
            den = str(den).replace(' ', '')

            power_pattern = re.compile(r'([A-Z])\*\*\(([^()]+)\)')
            num = re.sub(power_pattern, r'\1^{\2}', num)
            den = re.sub(power_pattern, r'\1^{\2}', den)
            output = None
            if den == '1':
                output = num
            else:
                output = f'F{{{num}}}{{{den}}}'
            input_string = input_string.replace(integral_var, output, 1)
        except Exception as e:
            print(f"[ERROR] during integration {repr(integral_var)}:")
            print(f"    Exception: {e}")
        return input_string


    def integrate(self, input_string: str) -> str:
        integral_pattern = re.compile(
            r'INT_([0A-Z])\^([A-Z])\{([A-Z])\^?(?:\{(.*?)\})\*d([A-Z])\}'
        )

        matches = list(re.finditer(integral_pattern, input_string))

        integral_match1 = matches[0]
        diff1 = integral_match1.group(5)
        pulse1 = integral_match1.group(3)
        upper_limit1 = integral_match1.group(2)

        integral_match2 = matches[1]
        diff2 = integral_match2.group(5)
        pulse2 = integral_match2.group(3)
        upper_limit2 = integral_match2.group(2)

        if upper_limit2 == diff1:
            input_string = self.process_single_integral(integral_match=integral_match2, input_string=input_string)
            input_string = self.simplify_fractions(input_string)
            input_string = self.redistribute_terms_to_integrals2(input_string)
            matches_new = list(re.finditer(integral_pattern, input_string))
            input_string = self.process_single_integral(integral_match=matches_new[0], input_string=input_string)
        else:
            input_string = self.process_single_integral(integral_match=integral_match1, input_string=input_string)
            input_string = self.simplify_fractions(input_string)
            input_string = self.redistribute_terms_to_integrals2(input_string)
            matches_new = list(re.finditer(integral_pattern, input_string))
            input_string = self.process_single_integral(integral_match=matches_new[0], input_string=input_string)
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
        diff_pulse = pulse_sequence[1]
        integral_search_pattern = re.compile(
            rf'INT\{{d{diff_pulse}\*{diff_pulse}\^3\*([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*)\}}'
        )
        match = re.search(integral_search_pattern, input_string)
        if match:
            upper_limit = pulse_sequence[0]
            lower_limit = '0'
            definite_integral = f'INT_{lower_limit}^{upper_limit}{{d{diff_pulse}*{diff_pulse}^3*{match.group(1)}}}'
            input_string = re.sub(integral_search_pattern, definite_integral, input_string)

        ############### SECOND PULSE
        diff_pulse = pulse_sequence[2]
        integral_search_pattern = re.compile(
            rf'INT\{{d{diff_pulse}\*{diff_pulse}\^3\*([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*)\}}'
        )
        match = re.search(integral_search_pattern, input_string)
        if match:
            upper_limit = pulse_sequence[1]
            lower_limit = '0'
            definite_integral = f'INT_{lower_limit}^{upper_limit}{{d{diff_pulse}*{diff_pulse}^3*{match.group(1)}}}'
            input_string = re.sub(integral_search_pattern, definite_integral, input_string)

        return input_string

    def take_dzetta(self, input_string: str) -> str:
        return input_string