import re
from math_objects import Simplifier

input_string = '2*PI^2*2*PI^2*(2*PI)^-4*(2*PI)^-4*(2*PI)^-4*3*2*PI^2*Q^4*INT_0^Q{K^{-1}*dK}*INT_0^K{L^{2*n+1}*dL}*Q^-2*Q^-2*Q^-n*Q^-2*SUM{Q^-n}'
integral_pattern = re.compile(r'INT_([0A-Z])\^([A-Z])\{([A-Z])\^?(?:\{(.*?)\})\*d([A-Z])\}')
matches = list(re.finditer(integral_pattern, input_string))
from sympy import symbols, Rational
import sympy as smp
n = symbols('n')
expr = (-0**(2*n + 2)) / (2*n + 2)
result = smp.cancel(expr)
print(result)
result = smp.expand(result)
print(result)
result = smp.simplify(result)
print(result)
