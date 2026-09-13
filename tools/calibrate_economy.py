#!/usr/bin/env python3
"""Fit treasury rates to IMF-like fiscal ratios after the 2026 state rebuild.

Everyone starts on the same tax/policy laws, so the fit targets a *standard*
OECD-ish budget, not each country's real tax/GDP (France is High Taxes +
Expanded Welfare, not default). Hard caps stop India/Nigeria minting cash
from mega-state pop × buildings.

Ledger unit: US$ billions / month. Deterministic. No random.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import COUNTRIES_CSV, DATA, STATES_CSV  # noqa: E402

# Additive extras at default laws (tier 3 on five-tier slots, standard tax).
# small 0.08 / medium 0.16 / large 0.32 / extreme 0.64
POLICY_DEFAULT = {
    "welfare": 0.08,
    "education": 0.08,
    "healthcare": 0.08,
    "investment": 0.16,
    "aid": 0.08,
}
POLICY_FACTOR_DEFAULT = 1.0 + sum(POLICY_DEFAULT.values())

# Monthly $B / year-GDP targets at default laws. Same-law world, not France-at-rest.
# net is income - (admin+policy), before interest.
ARCHETYPE = {
    "USA": {"spend": 0.28, "income": 0.24, "net": -0.04, "w": 5.0},
    "CHI": {"spend": 0.36, "income": 0.34, "net": -0.02, "w": 4.0},
    "JAP": {"spend": 0.30, "income": 0.26, "net": -0.04, "w": 3.0},
    "GER": {"spend": 0.32, "income": 0.28, "net": -0.04, "w": 3.0},
    "ENG": {"spend": 0.30, "income": 0.26, "net": -0.04, "w": 3.0},
    "FRA": {"spend": 0.30, "income": 0.26, "net": -0.04, "w": 3.0},
    "ITA": {"spend": 0.30, "income": 0.26, "net": -0.04, "w": 2.0},
    "RAJ": {"spend": 0.26, "income": 0.22, "net": -0.04, "w": 4.0},
    "BRA": {"spend": 0.28, "income": 0.24, "net": -0.04, "w": 2.0},
    "MEX": {"spend": 0.24, "income": 0.20, "net": -0.04, "w": 1.5},
    "KOR": {"spend": 0.26, "income": 0.26, "net": 0.00, "w": 2.0},
    "CAN": {"spend": 0.30, "income": 0.28, "net": -0.02, "w": 2.0},
    "SOV": {"spend": 0.28, "income": 0.26, "net": -0.02, "w": 2.0},
    "INS": {"spend": 0.20, "income": 0.18, "net": -0.02, "w": 1.5},
    "TUR": {"spend": 0.24, "income": 0.20, "net": -0.04, "w": 1.5},
    "SAU": {"spend": 0.26, "income": 0.28, "net": 0.02, "w": 1.0},
    "AST": {"spend": 0.28, "income": 0.26, "net": -0.02, "w": 1.5},
    "HOL": {"spend": 0.32, "income": 0.30, "net": -0.02, "w": 1.5},
    "SWE": {"spend": 0.32, "income": 0.30, "net": -0.02, "w": 1.5},
    "SWI": {"spend": 0.26, "income": 0.26, "net": 0.00, "w": 1.0},
    "SNG": {"spend": 0.18, "income": 0.22, "net": 0.04, "w": 1.0},
    "IRE": {"spend": 0.22, "income": 0.24, "net": 0.02, "w": 1.0},
    "NGA": {"spend": 0.18, "income": 0.14, "net": -0.04, "w": 2.0},
    "PAK": {"spend": 0.20, "income": 0.16, "net": -0.04, "w": 1.5},
    "VIN": {"spend": 0.22, "income": 0.20, "net": -0.02, "w": 1.0},
    "ARG": {"spend": 0.28, "income": 0.24, "net": -0.04, "w": 1.0},
    "POL": {"spend": 0.30, "income": 0.26, "net": -0.04, "w": 1.0},
}


def pop_m(manpower: float) -> float:
    return round(manpower / 100_000.0) / 10.0


def load() -> tuple[dict, dict]:
    countries = {}
    with COUNTRIES_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            countries[row["tag"]] = row
    bases: dict[str, dict] = defaultdict(lambda: {
        "pop_m": 0.0, "civs": 0.0, "fin_n": 0.0, "srv_n": 0.0,
        "fin_mkt": 0.0, "srv_mkt": 0.0, "fin_w": 0.0, "srv_w": 0.0,
    })
    with STATES_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row["owner_2026"]
            pm = pop_m(float(row["manpower"] or 0))
            civs = float(row["civs"] or 0)
            fin = float(row["finance"] or 0)
            srv = float(row["services"] or 0)
            b = bases[tag]
            b["pop_m"] += pm
            b["civs"] += civs
            b["fin_n"] += fin
            b["srv_n"] += srv
            b["fin_w"] += fin * pm
            b["srv_w"] += srv * pm
            b["fin_mkt"] += fin * (civs + srv + 1.0)
            b["srv_mkt"] += srv * (civs + 1.0)
    return countries, bases


def sim(b, r, pf=POLICY_FACTOR_DEFAULT, tax_mult=1.0):
    income_civ = b["civs"] * r["civ"]
    income_fin = b["fin_mkt"] * r["finance"]
    income_srv = b["srv_mkt"] * r["services"]
    tax = tax_mult * (
        b["pop_m"] * r["tax_pop"]
        + b["civs"] * r["tax_civ"]
        + b["srv_mkt"] * r["tax_srv"]
        + b["fin_mkt"] * r["tax_fin"]
    )
    admin = (
        b["pop_m"] * r["admin_pop"]
        + b["civs"] * r["admin_civ"]
        + b["srv_mkt"] * r["admin_srv"]
        + b["fin_mkt"] * r["admin_fin"]
    )
    policy = admin * (pf - 1.0)
    income = income_civ + income_fin + income_srv + tax
    expense = admin + policy
    return {
        "civ": income_civ, "fin": income_fin, "srv": income_srv, "tax": tax,
        "income": income, "admin": admin, "policy": policy, "expense": expense,
        "net": income - expense,
    }


def pct(month_b: float, gdp: float) -> float:
    if gdp <= 0:
        return 0.0
    return month_b * 12.0 / gdp


def loss_of(rates, countries, bases) -> tuple[float, list]:
    loss = 0.0
    wsum = 0.0
    rows = []
    for tag, tgt in ARCHETYPE.items():
        if tag not in bases or tag not in countries:
            continue
        gdp = float(countries[tag]["gdp_b"] or 0)
        if gdp < 20:
            continue
        s = sim(bases[tag], rates)
        inc_p = pct(s["income"], gdp)
        exp_p = pct(s["expense"], gdp)
        net_p = pct(s["net"], gdp)
        w = tgt["w"]
        loss += w * abs(inc_p - tgt["income"])
        loss += w * abs(exp_p - tgt["spend"])
        loss += w * 0.8 * abs(net_p - tgt["net"])
        # Hard-ish penalties: populous countries must not print or implode.
        if inc_p > 0.70:
            loss += w * 8.0 * (inc_p - 0.70)
        if exp_p > 0.70:
            loss += w * 8.0 * (exp_p - 0.70)
        if net_p > 0.15:
            loss += w * 6.0 * (net_p - 0.15)
        if net_p < -0.20:
            loss += w * 6.0 * (-0.20 - net_p)
        wsum += w
        rows.append((tag, gdp, s, inc_p, exp_p, net_p, tgt))
    # Buildings must actually pay in the US.
    usa = next(x for x in rows if x[0] == "USA")[2]
    if usa["fin"] < 4.0:
        loss += 3.0 * (4.0 - usa["fin"])
    if usa["srv"] < 8.0:
        loss += 2.0 * (8.0 - usa["srv"])
    if usa["tax"] < 40.0:
        loss += 1.5 * (40.0 - usa["tax"]) / 40.0
    return loss / max(wsum, 1e-9), rows


def main() -> int:
    countries, bases = load()
    print(f"Default policy factor {POLICY_FACTOR_DEFAULT:.2f}")
    print("Market weights (fin_mkt = finance×(civs+services+1), srv_mkt = services×(civs+1)):")
    for tag in ("USA", "CHI", "JAP", "GER", "ENG", "FRA", "RAJ", "BRA", "KOR", "SNG", "NGA"):
        b = bases[tag]
        print(
            f"  {tag:4} pop {b['pop_m']:7.1f} civs {b['civs']:5.0f} "
            f"finN {b['fin_n']:4.0f} srvN {b['srv_n']:4.0f} "
            f"fin_mkt {b['fin_mkt']:6.1f} srv_mkt {b['srv_mkt']:6.1f} "
            f"old_fin_w {b['fin_w']:7.1f}"
        )

    old = {
        "civ": 1.00, "finance": 0.00, "services": 0.00,
        "tax_pop": 0.25, "tax_civ": 0.00, "tax_srv": 0.00, "tax_fin": 0.00,
        "admin_pop": 0.25, "admin_civ": 0.00, "admin_srv": 0.00, "admin_fin": 0.00,
    }
    # Score old pop×level finance/services too.
    old_pop = dict(old)
    old_pop["finance"] = 0.33  # will be applied to fin_mkt in sim — not comparable.
    # Manual old-formula score:
    def sim_old(b):
        tax = b["pop_m"] * 0.25
        admin = b["pop_m"] * 0.25
        pf = 1.1 ** 6
        inc = b["civs"] + b["fin_w"] * 0.33 + b["srv_w"] * 0.08 + tax
        exp = admin * pf
        return inc, exp
    print("\nOLD formula (pop×level finance/services, tax=admin=0.25×pop, ×1.1^6):")
    for tag in ("USA", "CHI", "GER", "FRA", "RAJ", "NGA"):
        gdp = float(countries[tag]["gdp_b"])
        inc, exp = sim_old(bases[tag])
        print(f"  {tag:4} inc {pct(inc,gdp):5.1%}  exp {pct(exp,gdp):5.1%}  net {pct(inc-exp,gdp):6.1%}")

    grid = {
        "civ": [1.00],
        "finance": [0.20, 0.30, 0.40, 0.50, 0.70, 1.00],
        "services": [0.08, 0.12, 0.16, 0.20, 0.28],
        "tax_pop": [0.00, 0.02, 0.04, 0.06, 0.08],
        "tax_civ": [0.40, 0.80, 1.20, 1.60, 2.00],
        "tax_srv": [0.00, 0.08, 0.16, 0.24],
        "tax_fin": [0.00, 0.10, 0.20],
        "admin_pop": [0.02, 0.04, 0.06, 0.08],
        "admin_civ": [0.40, 0.80, 1.20, 1.60, 2.00],
        "admin_srv": [0.00, 0.08, 0.16, 0.24],
        "admin_fin": [0.00, 0.10, 0.20],
    }
    keys = list(grid)
    best = None
    best_loss = 1e9
    n = 0
    for vals in product(*(grid[k] for k in keys)):
        rates = dict(zip(keys, vals))
        n += 1
        loss, _ = loss_of(rates, countries, bases)
        if loss < best_loss:
            best_loss = loss
            best = rates
    print(f"\nGrid {n} combos. Best loss {best_loss:.4f}")
    print(json.dumps(best, indent=2))

    # Two-decimal neighborhood polish (already two decimals). Nudge ±0.02.
    current = dict(best)
    for _ in range(4):
        improved = False
        for k in keys:
            if k == "civ":
                continue
            base = current[k]
            for cand in (round(max(0.0, base + d) + 1e-12, 2) for d in (-0.04, -0.02, 0.0, 0.02, 0.04)):
                trial = dict(current)
                trial[k] = cand
                loss, _ = loss_of(trial, countries, bases)
                if loss < best_loss - 1e-9:
                    best_loss = loss
                    current = trial
                    best = trial
                    improved = True
        if not improved:
            break
    print(f"Polished loss {best_loss:.4f}")
    print(json.dumps(best, indent=2))

    _, rows = loss_of(best, countries, bases)
    print(f"\n{'tag':4} {'tax':>6} {'fin':>6} {'srv':>6} {'civ':>6} {'inc':>7} {'i%':>6} {'adm':>6} {'pol':>6} {'exp':>7} {'e%':>6} {'net%':>7} {'tgtN':>6}")
    usa_year = 0.0
    for tag, gdp, s, inc_p, exp_p, net_p, tgt in rows:
        if tag == "USA":
            usa_year = s["income"] * 12.0
        print(
            f"{tag:4} {s['tax']:6.1f} {s['fin']:6.1f} {s['srv']:6.1f} {s['civ']:6.1f} "
            f"{s['income']:7.1f} {inc_p:6.1%} {s['admin']:6.1f} {s['policy']:6.1f} "
            f"{s['expense']:7.1f} {exp_p:6.1%} {net_p:7.1%} {tgt['net']:6.1%}"
        )

    usa_b = bases["USA"]
    print("\nUSA tax laws:")
    for mult, name in ((0.0, "low"), (1.0, "standard"), (2.0, "high")):
        s = sim(usa_b, best, tax_mult=mult)
        gdp = float(countries["USA"]["gdp_b"])
        print(f"  {name:8} tax {s['tax']:6.1f} inc {s['income']:6.1f} net {s['net']:6.1f} ({pct(s['net'], gdp):+.1%} GDP)")
    print("USA policy extremes (standard tax):")
    for pf, name in ((1.00, "all-min"), (POLICY_FACTOR_DEFAULT, "default"), (2.60, "max-ish")):
        s = sim(usa_b, best, pf=pf)
        gdp = float(countries["USA"]["gdp_b"])
        print(f"  {name:8} exp {s['expense']:6.1f} ({pct(s['expense'], gdp):.1%} GDP) net {pct(s['net'], gdp):+.1%}")

    out = {
        "policy_default": POLICY_DEFAULT,
        "policy_factor_default": POLICY_FACTOR_DEFAULT,
        "rates": best,
        "usa_yearly_revenue": usa_year,
        "loss": best_loss,
        "formula": {
            "finance": "level * (civs + services + 1) * rate",
            "services": "level * (civs + 1) * rate",
            "tax": "pop_m * tax_pop + civs * tax_civ + srv_mkt * tax_srv + fin_mkt * tax_fin",
            "admin": "pop_m * admin_pop + civs * admin_civ + srv_mkt * admin_srv + fin_mkt * admin_fin",
        },
    }
    path = DATA / "economy_calibration.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nUSA yearly revenue {usa_year:.0f}  wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
