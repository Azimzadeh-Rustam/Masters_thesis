from .math_object import MathObject

class Fraction(MathObject):
    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator

    def __repr__(self):
        return f'F({self.numerator})({self.denominator})'

    def __str__(self):
        return f'F({self.numerator})({self.denominator})'
