from math_objects import Fraction, Integral, Polinom, Simplifier

def main():
    simplifier = Simplifier()
    #angular_expression = Integral(Fraction(Polinom('QL', 'm') + Polinom('LQ', 'n'), '2*PI^2'), r"OMEGA")
    input_string = '3*INT#{F{dS^{Q}_{mu}}{(2*PI)^4}}*INT{F{d^4{K}}{(2*PI)^4}}*INT{F{d^4{L}}{(2*PI)^4}}*F{Q_{mu}}{K^2*Q^2*L^2*(K-Q)^2*(L-Q)^2*(K-L)^2}'
    processed_string = simplifier.simplify(input_string)

if __name__ == '__main__':
    main()
