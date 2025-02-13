import re

class Simplifier:
    def __init__(self):
        pass

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
