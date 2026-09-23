#!/usr/bin/env python3
"""Audit live Doomsday ledger vs real-world fiscal ratios, then fit clean rates.

Matches common/scripted_effects/doomsday_economy.txt exactly:
  finance = level * (civs + services + fin_floor) * rate_finance
  services = level * (civs + srv_floor) * rate_services
  tax_base = pop_m * tax_pop + civs * tax_civ   (then tax-law multiplier)
  admin = pop_m * admin_pop + civs * admin_civ
  policy = admin * (admin_factor - 1)
  interest = debt * 0.03 / 12

Hard rules: free policy tiers stay 0; paid tiers stay >0. Factors ≤2 decimals.
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
from start_policies import POLICIES  # noqa: E402

# Central/federal-scale targets (share of GDP). The building stock cannot
# reproduce OECD general-government takes (FRA GG ~52% with only ~17 civs).
# These are playable central-budget ratios informed by IMF WEO / federal shares.
REAL = {
    # Majors — federal / consolidated-central scale
    "USA": {"rev": 0.18, "exp": 0.24, "w": 5.0},   # low tax law (2)
    "CHI": {"rev": 0.26, "exp": 0.32, "w": 4.5},
    "JAP": {"rev": 0.24, "exp": 0.30, "w": 3.5},
    "GER": {"rev": 0.26, "exp": 0.36, "w": 3.5},   # high policy
    "ENG": {"rev": 0.22, "exp": 0.28, "w": 3.0},
    "FRA": {"rev": 0.28, "exp": 0.40, "w": 3.0},   # tax 4 + high policy
    "ITA": {"rev": 0.26, "exp": 0.34, "w": 2.5},
    "CAN": {"rev": 0.24, "exp": 0.30, "w": 2.5},
    "KOR": {"rev": 0.24, "exp": 0.28, "w": 2.5},
    "SOV": {"rev": 0.24, "exp": 0.30, "w": 2.5},
    "RAJ": {"rev": 0.16, "exp": 0.22, "w": 3.5},
    "BRA": {"rev": 0.22, "exp": 0.28, "w": 2.0},
    "AUS": {"rev": 0.24, "exp": 0.28, "w": 1.5},
    "SPR": {"rev": 0.24, "exp": 0.30, "w": 1.5},
    # Mid / emerging
    "MEX": {"rev": 0.18, "exp": 0.22, "w": 1.5},
    "INS": {"rev": 0.14, "exp": 0.18, "w": 1.5},
    "TUR": {"rev": 0.18, "exp": 0.24, "w": 1.5},
    "SAU": {"rev": 0.24, "exp": 0.28, "w": 1.0},
    "POL": {"rev": 0.24, "exp": 0.30, "w": 1.0},
    "ARG": {"rev": 0.22, "exp": 0.28, "w": 1.0},
    "VIN": {"rev": 0.18, "exp": 0.22, "w": 1.0},
    "SIA": {"rev": 0.16, "exp": 0.20, "w": 1.0},
    "PHI": {"rev": 0.14, "exp": 0.18, "w": 1.0},
    "PAK": {"rev": 0.12, "exp": 0.18, "w": 1.5},
    "BAN": {"rev": 0.10, "exp": 0.14, "w": 1.0},
    "EGY": {"rev": 0.16, "exp": 0.24, "w": 1.0},
    "ISR": {"rev": 0.26, "exp": 0.32, "w": 1.0},
    "PER": {"rev": 0.14, "exp": 0.18, "w": 1.0},
    "IRQ": {"rev": 0.24, "exp": 0.28, "w": 0.8},
    "CHL": {"rev": 0.20, "exp": 0.24, "w": 0.8},
    "COL": {"rev": 0.18, "exp": 0.24, "w": 0.8},
    # Rich small / finance hubs
    "HOL": {"rev": 0.26, "exp": 0.30, "w": 1.5},
    "SWE": {"rev": 0.28, "exp": 0.32, "w": 1.5},
    "SWI": {"rev": 0.22, "exp": 0.22, "w": 1.0},
    "SNG": {"rev": 0.20, "exp": 0.16, "w": 1.5},
    "IRE": {"rev": 0.20, "exp": 0.20, "w": 1.0},
    "NOR": {"rev": 0.30, "exp": 0.30, "w": 1.0},
    "BEL": {"rev": 0.30, "exp": 0.34, "w": 1.0},
    "FOR": {"rev": 0.16, "exp": 0.18, "w": 1.0},
    # Low-income / fragile — must not print cash from population alone
    "NGA": {"rev": 0.08, "exp": 0.12, "w": 2.5},
    "ETH": {"rev": 0.08, "exp": 0.12, "w": 2.0},
    "KEN": {"rev": 0.12, "exp": 0.16, "w": 1.0},
    "GHA": {"rev": 0.12, "exp": 0.18, "w": 0.8},
    "COG": {"rev": 0.08, "exp": 0.12, "w": 1.5},
    "AFG": {"rev": 0.06, "exp": 0.10, "w": 1.5},
    "CUB": {"rev": 0.28, "exp": 0.36, "w": 0.5},
    "VEN": {"rev": 0.14, "exp": 0.22, "w": 0.5},
    "DPK": {"rev": 0.30, "exp": 0.40, "w": 0.5},
}

# Paid-tier policy surcharge amounts (must stay >0). Free tiers omitted (=0).
# Maps (slot, tier) -> surcharge. Tunable values only on these keys.
POLICY_PAID_DEFAULT = {
    ("welf", 3): 0.05, ("welf", 4): 0.25, ("welf", 5): 0.50,
    ("edu", 3): 0.05, ("edu", 4): 0.25, ("edu", 5): 0.50,
    ("imm", 4): 0.05, ("imm", 5): 0.25,
    ("mino", 4): 0.25, ("mino", 5): 0.50,
    ("inv", 2): 0.05, ("inv", 3): 0.10, ("inv", 4): 0.25, ("inv", 5): 0.50,
    ("sec", 5): 0.25,
    ("health", 3): 0.05, ("health", 4): 0.25, ("health", 5): 0.50,
    ("fert", 1): 0.10, ("fert", 2): 0.05,
    ("aid", 3): 0.05, ("aid", 4): 0.25, ("aid", 5): 0.50,
}

TAX_MULT = {1: 0.0, 2: 0.50, 3: 1.00, 4: 1.50, 5: 2.00}

SLOT_IDX = {
    "welf": 0, "edu": 1, "imm": 2, "tax": 3, "wom": 4, "mino": 5,
    "inv": 6, "sec": 7, "health": 8, "labor": 9, "fert": 10, "aid": 11,
}


def pop_m(manpower: float) -> float:
    return round(manpower / 100_000.0) / 10.0


def policy_factor(tag: str, paid: dict) -> tuple[float, float]:
    """Return (admin_factor, tax_mult) from starting laws."""
    pol = POLICIES.get(tag)
    if not pol:
        # Fallback default-ish
        return 1.48, 1.00
    af = 1.0
    for (slot, tier), amt in paid.items():
        idx = SLOT_IDX[slot]
        if int(pol[idx]) == tier:
            af += amt
    tax_tier = int(pol[SLOT_IDX["tax"]])
    return af, TAX_MULT.get(tax_tier, 1.0)


def load() -> tuple[dict, dict]:
    countries = {}
    with COUNTRIES_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            countries[row["tag"]] = row
    bases: dict[str, dict] = defaultdict(lambda: {
        "pop_m": 0.0, "civs": 0.0, "fin_n": 0.0, "srv_n": 0.0,
        "fin_mkt": 0.0, "srv_mkt": 0.0,
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
            # Live floors: fin +4, srv +2
            b["fin_mkt"] += fin * (civs + srv + 4.0)
            b["srv_mkt"] += srv * (civs + 2.0)
    return countries, bases


def sim(b, r, af: float, tax_mult: float, debt: float = 0.0):
    income_civ = b["civs"] * r["civ"]
    income_fin = b["fin_mkt"] * r["finance"]
    income_srv = b["srv_mkt"] * r["services"]
    tax_base = b["pop_m"] * r["tax_pop"] + b["civs"] * r["tax_civ"]
    tax = tax_base * tax_mult
    admin = b["pop_m"] * r["admin_pop"] + b["civs"] * r["admin_civ"]
    policy = admin * (af - 1.0)
    interest = debt * (r.get("interest_annual", 0.03) / 12.0)
    income = income_civ + income_fin + income_srv + tax
    expense = admin + policy + interest
    return {
        "civ": income_civ, "fin": income_fin, "srv": income_srv, "tax": tax,
        "income": income, "admin": admin, "policy": policy, "interest": interest,
        "expense": expense, "net": income - expense,
    }


def pct(month_b: float, gdp: float) -> float:
    if gdp <= 0:
        return 0.0
    return month_b * 12.0 / gdp


CURRENT = {
    "civ": 1.00,
    "finance": 0.30,
    "services": 0.20,
    "tax_pop": 0.01,
    "tax_civ": 1.00,
    "admin_pop": 0.01,
    "admin_civ": 1.00,
    "interest_annual": 0.03,
}


def evaluate(rates, countries, bases, paid, sample_tags=None):
    loss = 0.0
    wsum = 0.0
    rows = []
    tags = sample_tags or list(REAL.keys())
    for tag in tags:
        if tag not in REAL or tag not in bases or tag not in countries:
            continue
        tgt = REAL[tag]
        gdp = float(countries[tag]["gdp_b"] or 0)
        if gdp < 5:
            continue
        debt_gdp = float(countries[tag]["debt_gdp"] or 0)
        debt = gdp * debt_gdp
        af, tm = policy_factor(tag, paid)
        s = sim(bases[tag], rates, af, tm, debt)
        inc_p = pct(s["income"], gdp)
        exp_p = pct(s["expense"], gdp)
        net_p = pct(s["net"], gdp)
        tgt_net = tgt["rev"] - tgt["exp"]
        w = tgt["w"]
        loss += w * abs(inc_p - tgt["rev"])
        loss += w * abs(exp_p - tgt["exp"])
        loss += w * 0.6 * abs(net_p - tgt_net)
        # Soft caps: no hyperinflation of cash, no total collapse
        if inc_p > 0.55:
            loss += w * 12.0 * (inc_p - 0.55)
        if exp_p > 0.65:
            loss += w * 12.0 * (exp_p - 0.65)
        if net_p > 0.12:
            loss += w * 6.0 * (net_p - 0.12)
        if net_p < -0.20:
            loss += w * 6.0 * (-0.20 - net_p)
        # Populous poor must not print (gdp_b / pop_m under ~$3k)
        pop_m_v = bases[tag]["pop_m"]
        if pop_m_v > 0.1:
            gdp_pc = gdp / pop_m_v
            if gdp_pc < 3.0 and inc_p > 0.25:
                loss += w * 8.0 * (inc_p - 0.25)
        wsum += w
        rows.append({
            "tag": tag, "gdp": gdp, "af": af, "tm": tm, "s": s,
            "inc_p": inc_p, "exp_p": exp_p, "net_p": net_p, "tgt": tgt,
        })
    # Building income must matter in USA
    usa = next((r for r in rows if r["tag"] == "USA"), None)
    if usa:
        if usa["s"]["fin"] < 3.0:
            loss += 4.0 * (3.0 - usa["s"]["fin"])
        if usa["s"]["srv"] < 6.0:
            loss += 3.0 * (6.0 - usa["s"]["srv"])
        if usa["s"]["tax"] < 20.0:
            loss += 2.0 * (20.0 - usa["s"]["tax"]) / 20.0
    return loss / max(wsum, 1e-9), rows


def print_table(title: str, rows: list) -> None:
    print(f"\n=== {title} ===")
    print(
        f"{'tag':4} {'gdp':>8} {'pf':>4} {'tm':>4} "
        f"{'tax':>6} {'fin':>6} {'srv':>6} {'civ':>6} "
        f"{'inc$':>7} {'i%':>6} {'tgtI':>5} "
        f"{'exp$':>7} {'e%':>6} {'tgtE':>5} "
        f"{'net%':>6} {'di':>6} {'de':>6}"
    )
    for r in sorted(rows, key=lambda x: -x["gdp"]):
        s = r["s"]
        di = (r["inc_p"] - r["tgt"]["rev"]) * 100
        de = (r["exp_p"] - r["tgt"]["exp"]) * 100
        print(
            f"{r['tag']:4} {r['gdp']:8.0f} {r['af']:4.2f} {r['tm']:4.2f} "
            f"{s['tax']:6.1f} {s['fin']:6.1f} {s['srv']:6.1f} {s['civ']:6.1f} "
            f"{s['income']:7.1f} {r['inc_p']:6.1%} {r['tgt']['rev']:5.0%} "
            f"{s['expense']:7.1f} {r['exp_p']:6.1%} {r['tgt']['exp']:5.0%} "
            f"{r['net_p']:6.1%} {di:+5.1f} {de:+5.1f}"
        )


def main() -> int:
    countries, bases = load()
    paid = dict(POLICY_PAID_DEFAULT)

    print("State bases (live floors fin+4 / srv+2):")
    for tag in ("USA", "CHI", "JAP", "GER", "ENG", "FRA", "RAJ", "BRA", "NGA", "SNG", "ETH", "SOV"):
        b = bases[tag]
        print(
            f"  {tag:4} pop {b['pop_m']:7.1f} civs {b['civs']:5.0f} "
            f"finN {b['fin_n']:4.0f} srvN {b['srv_n']:4.0f} "
            f"fin_mkt {b['fin_mkt']:7.1f} srv_mkt {b['srv_mkt']:7.1f}"
        )

    loss0, rows0 = evaluate(CURRENT, countries, bases, paid)
    print_table(f"CURRENT rates (loss {loss0:.4f})", rows0)

    # Grid search — keep civ=1.00, interest=3%. Clean 2-decimal steps.
    grid = {
        "finance": [0.15, 0.20, 0.25, 0.30, 0.35],
        "services": [0.10, 0.12, 0.15, 0.18, 0.20, 0.25],
        "tax_pop": [0.01, 0.02, 0.03],
        "tax_civ": [0.50, 0.60, 0.80, 1.00, 1.20, 1.40],
        "admin_pop": [0.01, 0.02, 0.03],
        "admin_civ": [0.80, 1.00, 1.20, 1.40, 1.60, 1.80],
    }
    keys = list(grid)
    best = dict(CURRENT)
    best_loss = loss0
    n = 0
    for vals in product(*(grid[k] for k in keys)):
        rates = dict(CURRENT)
        rates.update(dict(zip(keys, vals)))
        n += 1
        loss, _ = evaluate(rates, countries, bases, paid)
        if loss < best_loss:
            best_loss = loss
            best = rates
    print(f"\nGrid {n} combos. Best loss {best_loss:.4f}")
    print(json.dumps({k: best[k] for k in ["civ", "finance", "services", "tax_pop", "tax_civ", "admin_pop", "admin_civ"]}, indent=2))

    # Neighborhood polish ±0.02 / ±0.01 on tax_pop/admin_pop
    current = dict(best)
    for _ in range(6):
        improved = False
        for k in keys:
            base = current[k]
            step = 0.01 if k in ("tax_pop", "admin_pop") else 0.02
            cands = []
            for d in (-2 * step, -step, 0, step, 2 * step):
                floor = 0.01 if k in ("tax_pop", "admin_pop") else 0.0
                cands.append(round(max(floor, base + d) + 1e-12, 2))
            for cand in cands:
                trial = dict(current)
                trial[k] = cand
                loss, _ = evaluate(trial, countries, bases, paid)
                if loss < best_loss - 1e-9:
                    best_loss = loss
                    current = trial
                    best = trial
                    improved = True
        if not improved:
            break

    # Optional policy ladder: keep free free, paid >0, clean 2-decimal steps.
    # Shipped ladder small/med/large/extreme = 0.05/0.10/0.25/0.50
    ladders = [
        {0.05: 0.05, 0.10: 0.10, 0.25: 0.25, 0.50: 0.50},
        {0.05: 0.06, 0.10: 0.12, 0.25: 0.30, 0.50: 0.60},
        {0.05: 0.04, 0.10: 0.08, 0.25: 0.20, 0.50: 0.40},
        {0.05: 0.08, 0.10: 0.16, 0.25: 0.32, 0.50: 0.64},
    ]
    best_paid = dict(paid)
    for remap in ladders:
        trial_paid = {k: remap.get(v, v) for k, v in POLICY_PAID_DEFAULT.items()}
        trial_paid = {k: round(max(0.01, v) + 1e-12, 2) for k, v in trial_paid.items()}
        loss, _ = evaluate(best, countries, bases, trial_paid)
        if loss < best_loss - 1e-9:
            best_loss = loss
            best_paid = trial_paid

    # Also try uniform scale on default ladder
    for scale in (0.75, 0.85, 0.90, 1.00, 1.10, 1.25):
        trial_paid = {k: round(max(0.01, v * scale) + 1e-12, 2) for k, v in POLICY_PAID_DEFAULT.items()}
        loss, _ = evaluate(best, countries, bases, trial_paid)
        if loss < best_loss - 1e-9:
            best_loss = loss
            best_paid = trial_paid

    # Re-polish rates with best paid scale
    current = dict(best)
    for _ in range(4):
        improved = False
        for k in keys:
            base = current[k]
            step = 0.01 if k in ("tax_pop", "admin_pop") else 0.02
            for d in (-step, 0, step):
                floor = 0.01 if k in ("tax_pop", "admin_pop") else 0.0
                cand = round(max(floor, base + d) + 1e-12, 2)
                trial = dict(current)
                trial[k] = cand
                loss, _ = evaluate(trial, countries, bases, best_paid)
                if loss < best_loss - 1e-9:
                    best_loss = loss
                    current = trial
                    best = trial
                    improved = True
        if not improved:
            break

    print(f"\nPolished loss {best_loss:.4f}")
    print("Rates:", json.dumps({k: best[k] for k in ["civ", "finance", "services", "tax_pop", "tax_civ", "admin_pop", "admin_civ"]}, indent=2))
    if best_paid != paid:
        print("Policy paid surcharges changed:")
        for k in sorted(POLICY_PAID_DEFAULT.keys()):
            old, new = POLICY_PAID_DEFAULT[k], best_paid[k]
            if abs(old - new) > 1e-9:
                print(f"  {k}: {old} -> {new}")
    else:
        print("Policy paid surcharges unchanged.")

    _, rows1 = evaluate(best, countries, bases, best_paid)
    print_table(f"FITTED rates (loss {best_loss:.4f})", rows1)

    # MAE summary
    def mae(rows, key_game, key_tgt):
        return sum(abs(r[key_game] - r["tgt"][key_tgt]) for r in rows) / len(rows)

    print(f"\nMAE income%: current {mae(rows0,'inc_p','rev'):.1%}  fitted {mae(rows1,'inc_p','rev'):.1%}")
    print(f"MAE expense%: current {mae(rows0,'exp_p','exp'):.1%}  fitted {mae(rows1,'exp_p','exp'):.1%}")

    usa = next(r for r in rows1 if r["tag"] == "USA")
    out = {
        "rates": {k: best[k] for k in ["civ", "finance", "services", "tax_pop", "tax_civ", "admin_pop", "admin_civ"]},
        "fin_floor": 4,
        "srv_floor": 2,
        "policy_paid": {f"{a}_{b}": v for (a, b), v in best_paid.items()},
        "loss": best_loss,
        "usa_yearly_revenue": usa["s"]["income"] * 12.0,
        "usa_income_pct_gdp": usa["inc_p"],
        "usa_expense_pct_gdp": usa["exp_p"],
        "sample": [
            {
                "tag": r["tag"], "inc_pct": round(r["inc_p"], 3), "exp_pct": round(r["exp_p"], 3),
                "tgt_rev": r["tgt"]["rev"], "tgt_exp": r["tgt"]["exp"],
            }
            for r in rows1
        ],
    }
    path = DATA / "economy_audit_fit.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote {path}")
    print(f"USA yearly revenue ${out['usa_yearly_revenue']:.0f}B ({out['usa_income_pct_gdp']:.1%} GDP)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
