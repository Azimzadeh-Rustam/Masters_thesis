from .math_object import MathObject

class CombinedExpression(MathObject):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return f"{self.left}{self.right}"
