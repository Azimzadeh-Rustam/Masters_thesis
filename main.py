from math_objects import Fraction, Integral, Polinom, Simplifier

def main():
    simplifier = Simplifier()

    expression = Integral(Fraction(Polinom('QL', 'm') + Polinom('LQ', 'n'), '2*PI^2'), r"OMEGA")

    expression = str(expression)
    print('Start: ' + expression)

    processed_expression = simplifier.simplify_polinom(expression)
    print('Processed: ' + processed_expression)


    input_string = '3*INT{F{dS^Q_mu}{(2*pi)^4}INT{ F{d^4K}{(2*pi)^4}F{d^4L}{(2*pi)^4}F{Q_mu}{K^2*Q^2*L^2*(K-Q)^2*(L-Q)^2*(K_L)^2} }}'


if __name__ == '__main__':
    main()
