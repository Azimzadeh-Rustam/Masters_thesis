class Integral:
    def __init__(self, function, differential, limits):
        self.function = function
        self.differential = differential
        self.limits = limits

    def __getattribute__(self, item):
        if item in ("_function", "_differential", "_limits"):
            raise ValueError(f"Access to attribute {item} denied")
        else:
            return object.__getattribute__(self, item)

    @classmethod
    def verify_function(cls, function):
        if type(function) != str():
            raise TypeError('The function must be a string')

    @classmethod
    def verify_differential(cls, differential):
        if type(differential) != str():
            raise TypeError('The differential must be a string')

    @property
    def func(self):
        return self._function

    @func.setter
    def func(self, function):
        self.verify_function(function)
        self._function = function

    @property
    def diff(self):
        return self._differential

    @diff.setter
    def diff(self, differential):
        self.verify_function(differential)
        self._differential = differential

    @property
    def lims(self):
        return self._limits

    @lims.setter
    def lims(self, limits):
        self._limits = limits

    @lims.deleter
    def lims(self):
        del self._limits
