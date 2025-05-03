import re
from math_objects import Simplifier

numerator = 'l+1'
factors_pattern = re.compile(r'(?:\d+\*)?[a-z][\+\-]\d+')
factors_num = factors_pattern.findall(numerator)
print(factors_num)