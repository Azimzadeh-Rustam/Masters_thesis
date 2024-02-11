import numpy as np


class Integral:

    def __init__(self, function=str(), differential=str(), limits=tuple()):
        if isinstance(function, str) and isinstance(differential, str):
            self._function = function
            self._differential = differential
        self._limits = limits

    def get_func(self):
        return self._function

    def get_diff(self):
        return self._differential

    def get_lims(self):
        return self._limits

    def set_func(self, function):
        if isinstance(function, str):
            self._function = function
        else:
            raise ValueError("The function must be a string")

    def set_diff(self, differential):
        if isinstance(differential, str):
            self._differential = differential
        else:
            raise ValueError("The differential must be a string")

    def set_lims(self, limits):
        self._limits = limits


function = r"x^2"
differential = r"dx"
limits = (2, -2)
loopIntegral = Integral(function, differential, limits)
print(loopIntegral.__dict__)