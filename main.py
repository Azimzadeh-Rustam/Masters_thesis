from math_objects import Integral, Polinom

def main():
    # function = r"x^2"
    # differential = r"dx"
    # limits = (2, -2)
    # loop_integral = Integral(function, differential, limits)
    # print(loop_integral.__dict__)

    polinom1 = Polinom('QL', 0)
    polinom2 = Polinom('LQ', 0)

    expression = polinom1 + polinom2
    print(expression)



if __name__ == '__main__':
    main()
