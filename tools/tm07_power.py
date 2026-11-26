"""TM07 synthetic power for the weekly marks (ledger 198). Exact binomial arithmetic, no market data.

A claim (B over A, or C over A, for one boss) passes its weekly part only if it wins all three screen
weeks and at least 16 of all 20 weeks, so at least 13 of the 17 extension weeks. Weeks are taken as
independent with one weekly win chance p. The chained-gain lines (beat the five held equally and the
90th percentile of 1,000 timing twins) are extra conditions, so these figures are upper bounds.
"""
from math import comb

SCREEN, EXT, NEED = 3, 17, 16


def tail(n, k, p):
    return sum(comb(n, j) * p**j * (1 - p)**(n - j) for j in range(k, n + 1))


def claim(p):
    return p**SCREEN * tail(EXT, NEED - SCREEN, p)


def main():
    print(f"null p=0.5: gate and mark together {claim(0.5)*100:.4f}% per claim; 16 of 20 alone {tail(20, 16, 0.5)*100:.4f}%; cap 1.25%")
    print(f"null p=0.5: any of four independent claims at most {(1-(1-claim(0.5))**4)*100:.4f}%")
    for p in (0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95):
        print(f"weekly win chance {p:.2f}: screen gate {p**3*100:6.2f}%  claim passes weekly part {claim(p)*100:6.2f}%")


if __name__ == "__main__":
    main()
