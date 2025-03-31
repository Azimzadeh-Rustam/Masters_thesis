import re
from math_objects import Simplifier

simplifier = Simplifier()
string = 'SUM{A}*SUM{B}*SUM{C}*DELTA_ln*DELTA_n0'
print(simplifier.delta_convolution(string))