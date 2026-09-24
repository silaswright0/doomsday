#!/usr/bin/env python3
"""Dry-run monthly treasury close: auto-loan then optional auto-repay."""
from __future__ import annotations


def month(treasury: float, debt: float, income: float, expense: float, auto_repay: bool) -> tuple[float, float]:
    treasury = treasury + income - expense
    loan_small = max(income, 0.1)
    if treasury < 0:
        cover = max(-treasury, loan_small)
        treasury += cover
        debt += cover
    if auto_repay and debt > 0.01 and treasury > 0.01:
        pay = min(treasury, debt)
        treasury -= pay
        debt -= pay
    return round(treasury, 4), round(debt, 4)


def main() -> None:
    cases = [
        ("deficit, no repay", 5, 0, 2, 10, False),
        ("deficit, auto repay", 5, 20, 2, 10, True),
        ("surplus + debt, auto repay", 1, 50, 12, 4, True),
        ("zero income overdraft", 0, 0, 0, 3, False),
        ("huge deficit", 0, 0, 1, 25, False),
        ("exact zero after expense", 8, 0, 2, 10, False),
    ]
    for name, t0, d0, inc, exp, repay in cases:
        t1, d1 = month(t0, d0, inc, exp, repay)
        print(f"{name}: treasury {t0}->{t1} debt {d0}->{d1} neg={t1 < 0}")
        assert t1 >= -1e-9, (name, t1)

    assert month(5, 0, 2, 10, False) == (0.0, 3.0)
    assert month(0, 0, 0, 3, False) == (0.0, 3.0)
    assert month(1, 50, 12, 4, True) == (0.0, 41.0)
    print("PASS")


if __name__ == "__main__":
    main()
