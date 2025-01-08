class MathObject:
    def __str__(self):
        raise NotImplementedError("Subclasses must implement the __str__ method.")

    def __add__(self, other):
        if not isinstance(other, MathObject):
            raise ValueError("You can only add MathObject instances.")
        from .combined_expression import CombinedExpression
        return CombinedExpression(self, other)
