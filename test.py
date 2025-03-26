import re
from math_objects import Simplifier

simplifier = Simplifier()
string = 'INT_0^K{dK*K^3*INT{dG_K}}*INT{dL*L^3*INT{dG_L}}C_m(KL)*C_l(LQ)*C_n(KQ)}'
print(simplifier.integrate_polinoms(string))