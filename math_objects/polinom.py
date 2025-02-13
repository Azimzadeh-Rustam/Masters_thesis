from .math_object import MathObject

class Polinom(MathObject):
    def __init__(self, angle, index):
        if isinstance(index, int) and index < 0:
            raise ValueError("The index of a polynomial must be a non-negative integer.")
        self.angle = angle
        self.index = index

    def __repr__(self):
        return f"C_{self.index}({self.angle})"

    def __str__(self):
        return f"C_{self.index}({self.angle})"
