import numpy as np
from integral import *


def main():
    function = r"x^2"
    differential = r"dx"
    limits = (2, -2)
    loop_integral = Integral(function, differential, limits)
    print(loop_integral.__dict__)


if __name__ == '__main__':
    main()
