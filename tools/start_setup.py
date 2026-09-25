#!/usr/bin/env python3
"""Write 2026 starting setup: history extras, OOBs, staff, basing, loc, flags.

Deterministic. Country-scoped. No random.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from start_audit import (
    ADJ,
    COMMANDERS,
    DEBT_OVERRIDES,
    ELECTIONS,
    EXTRA_TECH,
    FORCES,
    GULF,
    JIHAD,
    JUNTA,
    NORDIC,
    HOME_NAVY,
    HOME_STATIONS,
    OVERSEAS_AIR,
    OVERSEAS_LAND,
    OVERSEAS_NAVY,
    PIES,
    SLOTS_3,
    SLOTS_4,
    SLOTS_5,
    THEOCRACY,
    TIER_1,
    TIER_2,
    TIER_3,
    VANGUARD,
)
from ideology_map import KIND_OF, PARENTS, TYPE_OF, resolve

ROOT = Path(__file__).resolve().parents[1]
STATES_DIR = ROOT / "history" / "states"
COUNTRIES_DIR = ROOT / "history" / "countries"
UNITS_DIR = ROOT / "history" / "units"
CHARS_DIR = ROOT / "common" / "characters"
DATA_DIR = ROOT / "tools" / "data"
CSV_COUNTRIES = ROOT / "tools" / "doomsday_countries.csv"
TAG_MAP = ROOT / "tools" / "doomsday_tag_map.csv"
MUST_NOT_START = {
    "dd_inf_7", "dd_inf_8", "dd_ftr_6", "dd_cv_4", "dd_cv_5", "dd_cvf_5",
    "dd_sam_3", "dd_dew_1", "dd_dew_2", "dd_rkt_5", "dd_rad_4",
    "dd_cyb_3", "dd_tol_8", "dd_cpu_8", "dd_uav_5",
}

TEMPLATES = '''division_template = {
	name = "Infantry Division"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
		infantry = { x = 2 y = 0 }
		infantry = { x = 2 y = 1 }
		infantry = { x = 2 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
	is_locked = yes
}
division_template = {
	name = "Garrison Brigade"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
	}
	support = {
		engineer = { x = 0 y = 0 }
	}
	is_locked = yes
}
division_template = {
	name = "Armored Division"
	regiments = {
		modern_armor = { x = 0 y = 0 }
		modern_armor = { x = 0 y = 1 }
		modern_armor = { x = 0 y = 2 }
		mechanized = { x = 1 y = 0 }
		mechanized = { x = 1 y = 1 }
		mechanized = { x = 1 y = 2 }
		mechanized = { x = 2 y = 0 }
		mechanized = { x = 2 y = 1 }
		mechanized = { x = 2 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
	is_locked = yes
}
division_template = {
	name = "Mechanized Brigade"
	regiments = {
		mechanized = { x = 0 y = 0 }
		mechanized = { x = 0 y = 1 }
		mechanized = { x = 0 y = 2 }
		mechanized = { x = 1 y = 0 }
		mechanized = { x = 1 y = 1 }
		mechanized = { x = 1 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
	is_locked = yes
}
division_template = {
	name = "Mountain Division"
	regiments = {
		mountaineers = { x = 0 y = 0 }
		mountaineers = { x = 0 y = 1 }
		mountaineers = { x = 0 y = 2 }
		mountaineers = { x = 1 y = 0 }
		mountaineers = { x = 1 y = 1 }
		mountaineers = { x = 1 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
	is_locked = yes
}
division_template = {
	name = "Marine Division"
	regiments = {
		marine = { x = 0 y = 0 }
		marine = { x = 0 y = 1 }
		marine = { x = 0 y = 2 }
		marine = { x = 1 y = 0 }
		marine = { x = 1 y = 1 }
		marine = { x = 1 y = 2 }
	}
	support = {
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
	is_locked = yes
}
division_template = {
	name = "Militia Brigade"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
	}
	is_locked = yes
}
'''

NEED = {
    "Infantry Division": {"infantry_equipment": 900, "support_equipment": 30, "artillery_equipment": 12},
    "Garrison Brigade": {"infantry_equipment": 400, "support_equipment": 10},
    "Armored Division": {
        "modern_tank_chassis": 150, "mechanized_equipment": 600,
        "infantry_equipment": 600, "support_equipment": 40, "artillery_equipment": 12,
    },
    "Mechanized Brigade": {
        "mechanized_equipment": 600, "infantry_equipment": 600,
        "support_equipment": 30, "artillery_equipment": 12,
    },
    "Mountain Division": {"infantry_equipment": 600, "support_equipment": 30, "artillery_equipment": 12},
    "Marine Division": {"infantry_equipment": 600, "support_equipment": 30, "artillery_equipment": 12},
    "Militia Brigade": {"infantry_equipment": 600},
}

_LOCS: dict | None = None
_ACCESS: dict[str, list[str]] | None = None
_PAIRS: list[tuple[str, str]] | None = None

TMPL_KEY = {
    "Infantry Division": "inf",
    "Armored Division": "arm",
    "Mechanized Brigade": "mech",
    "Marine Division": "mar",
    "Mountain Division": "mtn",
    "Militia Brigade": "mil",
    "Garrison Brigade": "gar",
}
_ON_MAP: set[str] | None = None
_TAG_NAMES: dict[str, str] | None = None
_BITS: dict = {}
_OOB: dict = {}
_OOB_LOG: dict = {}


def on_map_tags() -> set[str]:
    global _ON_MAP
    if _ON_MAP is not None:
        return _ON_MAP
    out = set()
    with TAG_MAP.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("status") or "") == "on_map":
                out.add(row["tag"])
    _ON_MAP = out
    return out


def tag_display_name(tag: str) -> str:
    global _TAG_NAMES
    if _TAG_NAMES is None:
        names = {}
        with TAG_MAP.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                t = (row.get("tag") or "").strip()
                n = (row.get("doomsday_name") or row.get("vanilla_file_name") or t).strip()
                if t:
                    names[t] = n
        _TAG_NAMES = names
    return _TAG_NAMES.get(tag, tag)


def read_countries() -> dict[str, dict]:
    out = {}
    with CSV_COUNTRIES.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            tag = (row.get("tag") or "").strip()
            if tag:
                out[tag] = row
    return out


def build_locations() -> dict:
    global _LOCS
    if _LOCS is not None:
        return _LOCS
    by_tag: dict[str, dict] = defaultdict(lambda: {
        "states": [], "vps": [], "ports": [], "air_states": [],
    })
    state_meta: dict[int, dict] = {}
    vp_re = re.compile(r"victory_points\s*=\s*\{\s*(\d+)\s+(\d+)", re.S)
    owner_re = re.compile(r"owner\s*=\s*([A-Z0-9]{3})")
    id_re = re.compile(r"\bid\s*=\s*(\d+)")
    air_re = re.compile(r"air_base\s*=\s*(\d+)")
    port_re = re.compile(r"(\d+)\s*=\s*\{[^}]*naval_base\s*=\s*(\d+)", re.S)
    prov_re = re.compile(r"provinces\s*=\s*\{([^}]+)\}", re.S)
    for path in STATES_DIR.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        im = id_re.search(text)
        om = owner_re.search(text)
        if not im or not om:
            continue
        sid = int(im.group(1))
        owner = om.group(1)
        vps = [(int(a), int(b)) for a, b in vp_re.findall(text)]
        vps.sort(key=lambda x: -x[1])
        ports = [int(a) for a, _ in port_re.findall(text)]
        air = 0
        am = air_re.search(text)
        if am:
            air = int(am.group(1))
        provs = []
        pm = prov_re.search(text)
        if pm:
            provs = [int(x) for x in pm.group(1).split() if x.isdigit()]
        home = vps[0][0] if vps else (ports[0] if ports else (provs[0] if provs else 0))
        rec = {
            "id": sid, "owner": owner, "vps": vps, "ports": ports,
            "air": air, "provinces": provs, "home": home,
        }
        state_meta[sid] = rec
        by_tag[owner]["states"].append(rec)
        by_tag[owner]["vps"].extend(vps)
        by_tag[owner]["ports"].extend(ports)
        if air:
            by_tag[owner]["air_states"].append(rec)
    for tag, pack in by_tag.items():
        pack["vps"].sort(key=lambda x: -x[1])
        pack["states"].sort(key=lambda s: -(s["vps"][0][1] if s["vps"] else 0))
        pack["capital_prov"] = pack["vps"][0][0] if pack["vps"] else (
            pack["ports"][0] if pack["ports"] else 0
        )
    _LOCS = {"tags": dict(by_tag), "states": state_meta}
    return _LOCS


def loc_of(tag: str) -> dict:
    return build_locations()["tags"].get(tag, {
        "states": [], "vps": [], "ports": [], "air_states": [], "capital_prov": 0,
    })


def province_in_state(state_id: int, prefer: str = "vp") -> int:
    rec = build_locations()["states"].get(state_id)
    if not rec:
        return 0
    if prefer == "port" and rec["ports"]:
        return rec["ports"][0]
    if rec["vps"]:
        return rec["vps"][0][0]
    if rec["ports"]:
        return rec["ports"][0]
    return rec["home"]


def cycle_provs(tag: str) -> list[int]:
    pack = loc_of(tag)
    out = [p for p, _ in pack["vps"]]
    if not out:
        out = list(pack["ports"])
    if not out:
        for s in pack["states"]:
            out.extend(s["provinces"][:1])
    return out or [1]


def tech_tier(tag: str) -> int:
    if tag in TIER_3:
        return 3
    if tag in TIER_2:
        return 2
    if tag in TIER_1:
        return 1
    return 0


def extra_techs(tag: str) -> list[str]:
    if tag not in on_map_tags():
        return []
    ids = list(EXTRA_TECH.get(tech_tier(tag), []))
    if tag in {"USA", "SOV"}:
        ids += ["dd_str_3", "dd_str_4"]
    elif tag == "CHI":
        ids += ["dd_str_3"]
    out = [t for t in ids if t not in MUST_NOT_START]
    seen = set()
    uniq = []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def research_slots(tag: str, row: dict | None) -> int:
    if tag in SLOTS_5:
        return 5
    if tag in SLOTS_4:
        return 4
    if tag in SLOTS_3:
        return 3
    if tag not in on_map_tags():
        return 1
    gdp = float((row or {}).get("gdp_b") or 0)
    if gdp >= 200:
        return 3
    if gdp >= 20:
        return 2
    return 1


def debt_treasury(tag: str, row: dict | None) -> tuple[float, float]:
    gdp = 0.0
    ratio = 0.0
    try:
        gdp = float((row or {}).get("gdp_b") or 0)
        ratio = float((row or {}).get("debt_gdp") or 0)
    except (TypeError, ValueError):
        pass
    ov = DEBT_OVERRIDES.get(tag, {})
    if "debt_gdp" in ov:
        ratio = ov["debt_gdp"]
    elif tag in on_map_tags() and ratio <= 0:
        ratio = 0.08
    treasury_ratio = ov.get("treasury_gdp", 0.02)
    debt = gdp * ratio
    treasury = max(1.0, gdp * treasury_ratio)
    if tag in on_map_tags() and gdp <= 0:
        debt = max(debt, 0.05)
        treasury = max(treasury, 0.05)
    return debt, treasury


def _normalize_pie(pie: dict[str, int], ruling: str) -> dict[str, int]:
    pie = {k: int(v) for k, v in pie.items() if int(v) > 0}
    if ruling not in pie:
        pie[ruling] = 1
    total = sum(pie.values())
    if total != 100:
        pie[ruling] += 100 - total
    if pie[ruling] <= 0:
        others = [k for k in pie if k != ruling]
        others.sort(key=lambda k: pie[k], reverse=True)
        need = 1 - pie[ruling]
        pie[ruling] = 1
        for k in others:
            take = min(pie[k] - 1, need) if pie[k] > 1 else 0
            if take <= 0:
                continue
            pie[k] -= take
            need -= take
            if need <= 0:
                break
    return {k: v for k, v in pie.items() if v > 0}


def ideology_pie(tag: str, ruling: str, row: dict | None) -> dict[str, int]:
    if tag in PIES:
        pie = {k: v for k, v in PIES[tag].items() if v > 0}
        if pie:
            if ruling not in pie:
                pie[ruling] = 0
            pie[ruling] = pie.get(ruling, 0) + (100 - sum(pie.values()))
            pie = {k: v for k, v in pie.items() if v > 0}
            if pie.get(ruling, 0) > 0:
                return _normalize_pie(pie, ruling)
    dem = int(float((row or {}).get("dem") or 25))
    com = int(float((row or {}).get("com") or 10))
    fas = int(float((row or {}).get("fas") or 5))
    neu = int(float((row or {}).get("neu") or 60))
    kind = KIND_OF.get(ruling, "authoritarian")
    pie: dict[str, int] = {}
    if kind in {"elected", "illiberal"}:
        pie[ruling] = max(dem, 35)
        rest = 100 - pie[ruling]
        others = []
        if ruling != "liberal_conservatism":
            others.append(("liberal_conservatism", max(8, dem // 3)))
        if ruling != "social_democracy":
            others.append(("social_democracy", max(6, dem // 4)))
        if ruling != "social_liberalism":
            others.append(("social_liberalism", max(4, dem // 5)))
        if ruling != "national_populism":
            others.append(("national_populism", max(4, fas + 4)))
        others.append(("communism", max(1, com // 2)))
        if fas >= 6:
            others.append(("fascism", max(1, fas // 3)))
        weights = [w for _, w in others]
        total_w = sum(weights) or 1
        acc = 0
        for i, (tok, w) in enumerate(others):
            share = rest * w // total_w if i < len(others) - 1 else rest - acc
            if share > 0:
                pie[tok] = pie.get(tok, 0) + share
                acc += share
    elif kind == "far_left":
        pie[ruling] = max(70, com if com > 40 else 75)
        pie["communism"] = pie.get("communism", 0) + max(3, com // 8)
        pie["liberal_conservatism"] = max(4, dem // 6)
        pie["social_democracy"] = max(3, dem // 8)
        leftover = 100 - sum(pie.values())
        pie[ruling] += leftover
    elif kind == "far_right":
        pie[ruling] = 70
        pie["islamic_democracy"] = 12 if ruling.startswith("jihad") or ruling.startswith("theo") else 0
        pie["sovereign_democracy"] = 10
        pie["liberal_conservatism"] = 5
        pie["communism"] = 3
        pie = {k: v for k, v in pie.items() if v > 0}
        leftover = 100 - sum(pie.values())
        pie[ruling] += leftover
    else:
        pie[ruling] = max(neu, 65)
        pie["liberal_conservatism"] = max(6, dem // 4)
        pie["social_democracy"] = max(4, dem // 6)
        pie["communism"] = max(2, com // 4)
        leftover = 100 - sum(pie.values())
        pie[ruling] += leftover
    pie = {k: v for k, v in pie.items() if v > 0}
    return _normalize_pie(pie, ruling)


def election_fields(tag: str, row: dict | None, ruling: str) -> tuple[str, int, bool]:
    if tag in ELECTIONS:
        return ELECTIONS[tag]
    kind = KIND_OF.get(ruling, "authoritarian")
    csv_yes = str((row or {}).get("elections") or "no").lower() in {"yes", "1", "true"}
    allowed = csv_yes and kind in {"elected", "illiberal"}
    if tag not in on_map_tags():
        return "2024.1.1", 48, False
    return "2024.1.1", 48, allowed


def policies_for(tag: str, ruling: str, row: dict | None) -> list[str]:
    if tag not in on_map_tags():
        return []
    from start_policies import ideas_for, POLICIES
    researched = ideas_for(tag)
    if researched:
        return researched
    # Fallback only if a new on-map tag is missing from the 2026 table.
    welf = edu = imm = tax = wom = mino = inv = sec = health = labor = fert = aid = rel = med = cm = 3
    tax = 2
    cons = "volunteer_only"
    trade = "export_focus"
    econ = "civilian_economy"
    gdp = float((row or {}).get("gdp_b") or 0)
    wartime = str((row or {}).get("wartime") or "0") in {"1", "yes"}
    kind = KIND_OF.get(ruling, "authoritarian")
    if tag in NORDIC:
        welf, edu, health, tax, labor, aid = 4, 5, 5, 4, 4, 4
        imm, fert = 3, 3
    elif tag in {"USA"}:
        welf, tax, health, imm, labor, med = 3, 2, 2, 4, 2, 4
        sec, aid, cm = 4, 4, 1
    elif tag in GULF:
        welf, rel, wom, med, imm, mino, aid = 4, 2, 2, 2, 2, 2, 3
        tax, sec = 1, 4
    elif tag in VANGUARD:
        med, sec, cm, edu, rel = 2, 5, 2, 4, 4
        trade = "limited_exports"
        cons = "limited_conscription" if tag != "DPK" else "extensive_conscription"
        if tag == "DPK":
            econ = "partial_economic_mobilisation"
            sec, med, welf = 5, 1, 1
    elif tag in THEOCRACY:
        rel, wom, med, sec = 1, 1, 2, 4
        imm, mino = 2, 2
    elif tag in JIHAD:
        rel, wom, med, sec, cm = 1, 1, 2, 5, 2
        welf, edu, imm, mino = 1, 1, 1, 1
        cons = "extensive_conscription"
        econ = "war_economy" if wartime else "partial_economic_mobilisation"
        trade = "closed_economy"
    elif ruling == "military_junta" or tag in JUNTA:
        sec, cm, med, cons = 5, 2, 2, "limited_conscription"
        econ = "partial_economic_mobilisation" if wartime else "early_mobilization"
    elif ruling == "absolute_monarchy":
        rel, med = 2, 2
    elif kind in {"elected", "illiberal"}:
        if gdp >= 400:
            welf, edu, health = 4, 5, 4
            tax = 3 if tag in {"FRA", "BEL", "ITA", "SPR"} else 2
    if wartime:
        cons = "limited_conscription" if cons == "volunteer_only" else cons
        econ = "war_economy" if tag in {"UKR", "SOV", "ISR", "HAM", "HEZ", "HOU"} else "partial_economic_mobilisation"
        sec = max(sec, 4)
    if gdp < 15 and tag in on_map_tags():
        trade = "free_trade"
        welf = min(welf, 3)
        tax = min(tax, 2)
    ideas = [
        f"dd_welfare_{welf}", f"dd_education_{edu}", f"dd_immigration_{imm}",
        f"dd_taxes_{tax}", f"dd_women_{wom}", f"dd_minority_{mino}",
        f"dd_investment_{inv}", f"dd_security_{sec}", f"dd_healthcare_{health}",
        f"dd_labor_{labor}", f"dd_fertility_{fert}", f"dd_aid_{aid}",
        f"dd_religion_{rel}", f"dd_media_{med}", f"dd_civil_military_{cm}",
        cons, trade, econ,
    ]
    return ideas


def estimate_force(tag: str, row: dict | None) -> tuple[int, ...]:
    if tag in FORCES:
        return FORCES[tag]
    sipri = float((row or {}).get("sipri_b") or 0)
    pop_m = float((row or {}).get("pop") or 0) / 1_000_000
    docks = int(float((row or {}).get("docks") or 0))
    wartime = str((row or {}).get("wartime") or "0") in {"1", "yes"}
    personnel_k = sipri * 6.0 + min(pop_m, 180) * 0.35
    if wartime:
        personnel_k *= 1.35
    if tag not in on_map_tags():
        return (0,) * 14
    inf = max(0, int(round(personnel_k / 14)))
    if pop_m < 0.3 and sipri < 0.3:
        inf = 1 if pop_m >= 0.05 else 0
        gar = 1 if inf == 0 else 0
        return (inf, 0, 0, 0, 0, 0, gar, 0, 0, 0, 0, 0, 0, 0)
    arm = max(0, inf // 6) if sipri >= 1.5 else 0
    mech = max(0, inf // 5) if sipri >= 1 else 0
    mar = 1 if docks >= 2 and sipri >= 3 else 0
    mtn = 1 if inf >= 4 else 0
    mil = 2 if wartime and sipri < 5 else 0
    gar = max(1, inf // 3) if inf else (1 if pop_m >= 0.2 else 0)
    inf = max(0, inf - mech // 2)
    cv = 0
    dd = min(12, docks + int(sipri)) if docks else 0
    cl = min(4, docks // 3) if docks >= 3 else 0
    ss = min(8, docks) if sipri >= 2 and docks else 0
    ftr = min(24, int(sipri * 0.8) + (2 if sipri >= 1 else 0))
    cas = min(10, ftr // 3)
    hel = min(12, 1 + int(sipri * 0.4))
    if sipri < 0.2:
        ftr = cas = hel = 0
        dd = cl = ss = cv = 0
    return (inf, arm, mech, mar, mtn, mil, gar, cv, dd, cl, ss, ftr, cas, hel)


def inf_eq(tag: str) -> str:
    t = tech_tier(tag)
    return {0: "infantry_equipment_cw1", 1: "infantry_equipment_cw2", 2: "infantry_equipment_cw4", 3: "infantry_equipment_cw6"}[t]


def tank_eq(tag: str) -> str:
    t = tech_tier(tag)
    return {0: "mbt_equipment_2", 1: "mbt_equipment_2", 2: "mbt_equipment_3", 3: "mbt_equipment_4"}[t]


def ftr_eq(tag: str) -> str:
    t = tech_tier(tag)
    return {0: "fighter_equipment_cw3", 1: "fighter_equipment_cw4", 2: "fighter_equipment_cw45", 3: "fighter_equipment_cw5a"}[t]


def cas_eq(tag: str) -> str:
    t = tech_tier(tag)
    return {0: "cas_equipment_cw1", 1: "cas_equipment_cw2", 2: "cas_equipment_cw3", 3: "cas_equipment_cw4"}[t]


def hel_eq(tag: str) -> str:
    return "transport_heli_equipment_2" if tech_tier(tag) >= 2 else "transport_heli_equipment_1"


def aew_eq(tag: str) -> str:
    return "aew_equipment_2" if tech_tier(tag) >= 3 else "aew_equipment_1"


def sam_eq(tag: str) -> str:
    return "sam_missile_equipment_2" if tech_tier(tag) >= 3 else "sam_missile_equipment_1"


def mpa_eq(tag: str) -> str:
    return "mpa_equipment_cw2" if tech_tier(tag) >= 3 else "mpa_equipment_cw1"


def strat_eq(tag: str) -> str:
    if tag == "USA":
        return "strat_bomber_equipment_cw4"
    if tag in {"SOV", "CHI"}:
        return "strat_bomber_equipment_cw3"
    return "strat_bomber_equipment_cw2"


def hull_dd(tag: str) -> str:
    t = tech_tier(tag)
    return {0: "ship_hull_light_cw1", 1: "ship_hull_light_cw2", 2: "ship_hull_light_cw3", 3: "ship_hull_light_cw4"}[t]


def hull_cv(tag: str) -> str:
    return "ship_hull_carrier_cw2" if tech_tier(tag) >= 3 else "ship_hull_carrier_cw1"


def hull_ss(tag: str) -> str:
    return "ship_hull_submarine_cw2" if tech_tier(tag) >= 3 else "ship_hull_submarine_cw1"


def hull_cl(tag: str) -> str:
    return "ship_hull_cruiser_cw2" if tech_tier(tag) >= 2 else "ship_hull_cruiser_cw1"


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def xp_for(tag: str, row: dict | None, militia: bool = False) -> float:
    if militia:
        return 0.15
    if str((row or {}).get("wartime") or "0") in {"1", "yes"}:
        return 0.4
    if tech_tier(tag) >= 2:
        return 0.3
    return 0.2


def force_counts(force: tuple[int, ...]) -> dict[str, int]:
    keys = ("inf", "arm", "mech", "mar", "mtn", "mil", "gar", "cv", "dd", "cl", "ss", "ftr", "cas", "hel")
    return dict(zip(keys, force))


def state_owner(state_id: int) -> str:
    rec = build_locations()["states"].get(state_id)
    return rec["owner"] if rec else ""


def state_has_air(state_id: int) -> bool:
    rec = build_locations()["states"].get(state_id)
    return bool(rec and rec["air"])


def state_port(state_id: int) -> int:
    rec = build_locations()["states"].get(state_id)
    if not rec or not rec["ports"]:
        return 0
    return rec["ports"][0]


def foreign_pairs() -> list[tuple[str, str]]:
    """Host, guest. Every foreign land, air, or naval spawn. No self, no duplicates."""
    global _PAIRS
    if _PAIRS is not None:
        return _PAIRS
    found: set[tuple[str, str]] = set()
    for guest, _tmpl, _name, host, sid in OVERSEAS_LAND:
        owner = state_owner(sid) or host
        if owner and owner != guest:
            found.add((owner, guest))
    for guest, host, sid, fighters, cas_n, hel in OVERSEAS_AIR:
        if fighters + cas_n + hel <= 0 or not state_has_air(sid):
            continue
        owner = state_owner(sid) or host
        if owner and owner != guest:
            found.add((owner, guest))
    for guest, host, sid, cv, dd, cl, ss in OVERSEAS_NAVY:
        if cv + dd + cl + ss <= 0:
            continue
        owner = state_owner(sid) or host
        if owner and owner != guest:
            found.add((owner, guest))
    _PAIRS = sorted(found)
    return _PAIRS


def prepare_access() -> dict[str, list[str]]:
    global _ACCESS
    by_guest: dict[str, list[str]] = defaultdict(list)
    for host, guest in foreign_pairs():
        by_guest[guest].append(host)
    _ACCESS = {guest: sorted(set(hosts)) for guest, hosts in by_guest.items()}
    return _ACCESS


def hosts_for(tag: str) -> list[str]:
    if _ACCESS is None:
        prepare_access()
    return (_ACCESS or {}).get(tag, [])


def write_land_units(tag: str, row: dict | None, force: tuple[int, ...]) -> tuple[str, dict[str, int], int]:
    pool = force_counts(force)
    provs = cycle_provs(tag)
    if not provs:
        provs = [1]
    xp = xp_for(tag, row)
    mxp = xp_for(tag, row, True)
    bits = []
    deployed = defaultdict(int)
    n = 0
    seq = {"Infantry Division": 0, "Armored Division": 0, "Mechanized Brigade": 0,
           "Marine Division": 0, "Mountain Division": 0, "Militia Brigade": 0,
           "Garrison Brigade": 0}

    def add(tmpl: str, name: str, loc: int, exp: float):
        nonlocal n
        if loc <= 0:
            loc = provs[0]
        bits.append(
            "	division = {\n"
            f'		name = "{name}"\n'
            f"		location = {loc}\n"
            f'		division_template = "{tmpl}"\n'
            f"		start_experience_factor = {exp:.2f}\n"
            "		start_equipment_factor = 1.0\n"
            "	}"
        )
        n += 1
        for k, v in NEED[tmpl].items():
            deployed[k] += v

    def take(tmpl: str) -> None:
        key = TMPL_KEY[tmpl]
        if pool[key] > 0:
            pool[key] -= 1

    for guest, tmpl, name, sid in HOME_STATIONS:
        if guest != tag:
            continue
        loc = province_in_state(sid)
        if loc and state_owner(sid) == tag:
            add(tmpl, name, loc, xp)
            take(tmpl)
    for guest, tmpl, name, host, sid in OVERSEAS_LAND:
        if guest != tag:
            continue
        loc = province_in_state(sid)
        owner = state_owner(sid)
        if loc and owner == host:
            add(tmpl, name, loc, xp)
            take(tmpl)
    mapping = [
        ("inf", "Infantry Division", "Infantry Division", xp),
        ("arm", "Armored Division", "Armored Division", xp),
        ("mech", "Mechanized Brigade", "Mechanized Brigade", xp),
        ("mar", "Marine Division", "Marine Division", xp),
        ("mtn", "Mountain Division", "Mountain Division", xp),
        ("mil", "Militia Brigade", "Militia Brigade", mxp),
        ("gar", "Garrison Brigade", "Garrison Brigade", xp * 0.7),
    ]
    i = 0
    for key, tmpl, label, exp in mapping:
        for _ in range(pool[key]):
            seq[tmpl] += 1
            loc = provs[i % len(provs)]
            i += 1
            add(tmpl, f"{ordinal(seq[tmpl])} {label}", loc, exp)
    body = "units = {\n" + "\n".join(bits) + "\n}\n" if bits else "units = {\n}\n"
    return body, dict(deployed), n


def write_air(tag: str, row: dict | None, force: tuple[int, ...]) -> str:
    c = force_counts(force)
    pack = loc_of(tag)
    homes = [s["id"] for s in pack["air_states"]] or [s["id"] for s in pack["states"][:1]]
    if not homes:
        return ""
    t = tech_tier(tag)
    ftr = ftr_eq(tag)
    cas = cas_eq(tag)
    heli = hel_eq(tag)
    by_state: dict[int, list[tuple[str, int]]] = defaultdict(list)

    def wing(state, eq, amount):
        if amount <= 0 or not state:
            return
        by_state[int(state)].append((eq, amount))

    home = homes[0]
    second = homes[min(1, len(homes) - 1)]
    third = homes[min(2, len(homes) - 1)] if len(homes) > 1 else home
    ftr_left = c["ftr"] * 20
    cas_left = c["cas"] * 16
    hel_left = c["hel"] * 12
    for guest, host, sid, fighters, cas_n, hel in OVERSEAS_AIR:
        if guest != tag or not state_has_air(sid):
            continue
        owner = state_owner(sid)
        if owner not in {tag, host}:
            continue
        take_f = min(fighters, ftr_left)
        take_c = min(cas_n, cas_left)
        take_h = min(hel, hel_left)
        wing(sid, ftr, take_f)
        wing(sid, cas, take_c)
        wing(sid, heli, take_h)
        ftr_left -= take_f
        cas_left -= take_c
        hel_left -= take_h
    wing(home, ftr, ftr_left)
    wing(second, cas, cas_left)
    wing(third, heli, hel_left)
    if c["ftr"] or c["cas"]:
        wing(home, "recon_uav_equipment_2", max(8, c["ftr"] * 2))
    if t >= 2:
        wing(home, "recon_uav_equipment_1", max(12, c["ftr"] * 2))
        wing(home, aew_eq(tag), 4 if t == 2 else 8)
        wing(home, mpa_eq(tag), 4 if t == 2 else 8)
        wing(home, sam_eq(tag), 16 if t == 2 else 32)
    if t >= 3:
        wing(home, "strike_uav_equipment_1", max(12, c["cas"] * 8))
        wing(home, "hale_uav_equipment_1", 4)
        wing(home, "tac_bomber_equipment_cw3", 16 if c["cas"] >= 6 else 0)
    if tag in {"USA", "SOV", "CHI"}:
        wing(home, strat_eq(tag), 16 if tag == "USA" else 8)
    if not by_state:
        return ""
    lines = ["air_wings = {"]
    for state in sorted(by_state):
        lines.append(f"	{state} = {{")
        merged: dict[str, int] = defaultdict(int)
        for eq, amount in by_state[state]:
            merged[eq] += amount
        for eq, amount in merged.items():
            lines.append(f'		{eq} = {{ owner = "{tag}" amount = {amount} }}')
        lines.append("	}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def ship_variant_name(eq: str) -> str:
    return {
        "ship_hull_light_cw1": "Cold War Escort",
        "ship_hull_light_cw2": "Cold War Frigate",
        "ship_hull_light_cw3": "Cold War Destroyer",
        "ship_hull_light_cw4": "Modern Destroyer",
        "ship_hull_cruiser_cw1": "Cold War Cruiser",
        "ship_hull_cruiser_cw2": "Missile Cruiser",
        "ship_hull_carrier_cw1": "Cold War Carrier",
        "ship_hull_carrier_cw2": "Fleet Carrier",
        "ship_hull_submarine_cw1": "Cold War Submarine",
        "ship_hull_submarine_cw2": "Attack Submarine",
    }.get(eq, "Doomsday Hull")


def naval_aa_module(tag: str) -> str:
    t = tech_tier(tag)
    if t >= 3:
        return "ship_vls_1"
    if t >= 2:
        return "ship_sam_battery_2"
    return "ship_sam_battery_1"


def naval_variants(tag: str) -> list[str]:
    """MTG ship designs so OOBs can spawn. Deterministic modules only."""
    aa = naval_aa_module(tag)
    hulls = {
        hull_dd(tag): (
            "fixed_ship_battery_slot = ship_light_battery_4\n"
            "\t\tfixed_ship_anti_air_slot = " + aa + "\n"
            "\t\tfixed_ship_fire_control_system_slot = ship_fire_control_system_3\n"
            "\t\tfixed_ship_radar_slot = ship_radar_2\n"
            "\t\tfixed_ship_engine_slot = light_ship_engine_3\n"
            "\t\tfixed_ship_torpedo_slot = ship_torpedo_2\n"
            "\t\tmid_1_custom_slot = ship_torpedo_2\n"
            "\t\trear_1_custom_slot = ship_depth_charge_3"
        ),
        hull_cl(tag): (
            "fixed_ship_battery_slot = ship_light_medium_battery_2\n"
            "\t\tfixed_ship_anti_air_slot = " + aa + "\n"
            "\t\tfixed_ship_fire_control_system_slot = ship_fire_control_system_3\n"
            "\t\tfixed_ship_radar_slot = ship_radar_2\n"
            "\t\tfixed_ship_engine_slot = cruiser_ship_engine_3\n"
            "\t\tfixed_ship_armor_slot = ship_armor_cruiser_2\n"
            "\t\tfixed_ship_secondaries_slot = dp_ship_secondaries_2\n"
            "\t\tmid_1_custom_slot = ship_torpedo_2\n"
            "\t\trear_1_custom_slot = " + aa
        ),
        hull_cv(tag): (
            "fixed_ship_deck_slot_1 = ship_deck_space\n"
            "\t\tfixed_ship_deck_slot_2 = ship_deck_space\n"
            "\t\tfixed_ship_anti_air_slot = " + aa + "\n"
            "\t\tfixed_ship_radar_slot = ship_radar_2\n"
            "\t\tfixed_ship_engine_slot = carrier_ship_engine_3\n"
            "\t\tfixed_ship_secondaries_slot = dp_ship_secondaries_2\n"
            "\t\tfront_1_custom_slot = empty"
        ),
        hull_ss(tag): (
            "fixed_ship_torpedo_slot = ship_torpedo_sub_2\n"
            "\t\tfixed_ship_engine_slot = sub_ship_engine_2\n"
            "\t\trear_1_custom_slot = ship_torpedo_sub_2"
        ),
    }
    lines = []
    for eq, modules in hulls.items():
        name = ship_variant_name(eq)
        lines.append(
            "create_equipment_variant = {\n"
            f'\tname = "{name}"\n'
            f"\ttype = {eq}\n"
            "\tparent_version = 0\n"
            "\tmodules = {\n"
            f"\t\t{modules}\n"
            "\t}\n"
            "}"
        )
    return lines


def _ship_line(tag: str, kind: str, eq: str, name: str) -> str:
    vname = ship_variant_name(eq)
    return (
        "			ship = {\n"
        f'				name = "{name}"\n'
        f"				definition = {kind}\n"
        "				start_experience_factor = 0.25\n"
        "				equipment = {\n"
        f'					{eq} = {{ amount = 1 owner = {tag} version_name = "{vname}" }}\n'
        "				}\n"
        "			}"
    )


def write_navy(tag: str, row: dict | None, force: tuple[int, ...]) -> str | None:
    c = force_counts(force)
    if tech_tier(tag) < 2:
        c["cv"] = 0
        c["cl"] = 0
    ports = loc_of(tag)["ports"]
    home = ports[0] if ports else 0
    if not home:
        for g, host, sid, *_rest in OVERSEAS_NAVY:
            if g == tag:
                home = province_in_state(sid, "port") if sid else (loc_of(host)["ports"] or [0])[0]
                break
    if not home and c["cv"] + c["dd"] + c["cl"] + c["ss"] <= 0:
        if not any(g == tag for g, *_ in OVERSEAS_NAVY):
            return None

    pool = {"cv": c["cv"], "dd": c["dd"], "cl": c["cl"], "ss": c["ss"]}
    name_i = {"cv": 0, "dd": 0, "cl": 0, "ss": 0}

    def take(cv: int, dd: int, cl: int, ss: int) -> tuple[int, int, int, int]:
        got = []
        for key, n in (("cv", cv), ("dd", dd), ("cl", cl), ("ss", ss)):
            n = min(max(0, n), pool[key])
            pool[key] -= n
            got.append(n)
        return got[0], got[1], got[2], got[3]

    def block(loc: int, cv: int, dd: int, cl: int, ss: int, title: str) -> str:
        if cv + dd + cl + ss <= 0 or loc <= 0:
            return ""
        inner = []
        for _ in range(cv):
            name_i["cv"] += 1
            inner.append(_ship_line(tag, "carrier", hull_cv(tag), f"{tag} CV-{name_i['cv']}"))
        for _ in range(dd):
            name_i["dd"] += 1
            inner.append(_ship_line(tag, "destroyer", hull_dd(tag), f"{tag} DD-{name_i['dd']}"))
        for _ in range(cl):
            name_i["cl"] += 1
            inner.append(_ship_line(tag, "light_cruiser", hull_cl(tag), f"{tag} CL-{name_i['cl']}"))
        for _ in range(ss):
            name_i["ss"] += 1
            inner.append(_ship_line(tag, "submarine", hull_ss(tag), f"{tag} SS-{name_i['ss']}"))
        body = "\n".join(inner)
        return (
            f'	fleet = {{\n		name = "{title}"\n		naval_base = {loc}\n'
            f'		task_force = {{\n			name = "{title} TF"\n			location = {loc}\n'
            f"{body}\n		}}\n	}}\n"
        )

    chunks = []
    for guest, sid, cv, dd, cl, ss, title in HOME_NAVY:
        if guest != tag or state_owner(sid) != tag:
            continue
        loc = state_port(sid)
        if loc <= 0:
            continue
        cv, dd, cl, ss = take(cv, dd, cl, ss)
        chunks.append(block(loc, cv, dd, cl, ss, title))
    for guest, host, sid, cv, dd, cl, ss in OVERSEAS_NAVY:
        if guest != tag or state_owner(sid) != host:
            continue
        loc = state_port(sid)
        if loc <= 0:
            continue
        cv, dd, cl, ss = take(cv, dd, cl, ss)
        chunks.append(block(loc, cv, dd, cl, ss, f"{tag} {host} Station"))
    cv, dd, cl, ss = take(pool["cv"], pool["dd"], pool["cl"], pool["ss"])
    chunks.append(block(home, cv, dd, cl, ss, f"{tag} Home Fleet"))
    body = "".join(x for x in chunks if x)
    if not body:
        return None
    return f"units = {{\n{body}}}\n"


def surplus_lines(tag: str, deployed: dict[str, int], force: tuple[int, ...]) -> list[str]:
    ratio = 0.22 if tag in {"USA", "CHI"} else 0.15
    c = force_counts(force)
    lines = []
    inf = inf_eq(tag)
    qty = int(round(deployed.get("infantry_equipment", 0) * ratio))
    if qty:
        lines.append(f"add_equipment_to_stockpile = {{ type = {inf} amount = {qty} producer = {tag} }}")
    for arche, specific in (
        ("support_equipment", "support_equipment"),
        ("artillery_equipment", "artillery_equipment"),
        ("mechanized_equipment", "mechanized_equipment"),
        ("modern_tank_chassis", tank_eq(tag)),
    ):
        q = int(round(deployed.get(arche, 0) * ratio))
        if q:
            lines.append(f"add_equipment_to_stockpile = {{ type = {specific} amount = {q} producer = {tag} }}")
    sipri = 0.0
    # SAM ammo stays munitions, not army double-count; keep existing sipri rule in write_country
    ftr_q = int(round(c["ftr"] * 20 * ratio))
    if ftr_q:
        lines.append(f"add_equipment_to_stockpile = {{ type = {ftr_eq(tag)} amount = {ftr_q} producer = {tag} }}")
    return lines


def write_oob_files(tag: str, row: dict | None) -> tuple[str, str | None, list[str], int]:
    if tag not in on_map_tags():
        return "DOOMSDAY_EMPTY", None, [], 0
    force = estimate_force(tag, row)
    land, deployed, ndiv = write_land_units(tag, row, force)
    air = write_air(tag, row, force)
    text = "# Doomsday 2026 OOB. Generated. Locked templates match ai_templates.\n" + TEMPLATES + land
    if air:
        text += air
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    (UNITS_DIR / f"{tag}_2026.txt").write_text(text, encoding="utf-8")
    naval = write_navy(tag, row, force)
    naval_name = None
    if naval:
        (UNITS_DIR / f"{tag}_2026_naval.txt").write_text(
            "# Doomsday 2026 naval OOB. Generated.\n" + naval, encoding="utf-8"
        )
        naval_name = f"{tag}_2026_naval"
    extra = surplus_lines(tag, deployed, force)
    _OOB_LOG[tag] = {
        "force": list(force),
        "ndiv": ndiv,
        "oob": f"{tag}_2026",
        "naval_oob": naval_name,
        "source": "public OOB / IISS-summary / SIPRI-scaled discretion",
        "surplus": extra,
    }
    return f"{tag}_2026", naval_name, extra, ndiv


def staff_ids(tag: str) -> list[str]:
    return [f"{tag}_john_army", f"{tag}_john_airforce", f"{tag}_john_navy"]


def commander_list(tag: str, ndiv: int, force: tuple[int, ...]) -> list[tuple]:
    named = COMMANDERS.get(tag)
    if named:
        return list(named)
    if tag not in on_map_tags():
        return []
    out = []
    if ndiv >= 6:
        out.append(("Army Command", "fm", 2, 2, 2, 2, 3, "organizer"))
    if ndiv >= 1:
        out.append(("Field Command", "gen", 2, 2, 2, 2, 2, "infantry_officer"))
    if ndiv >= 8:
        out.append(("Corps Command", "gen", 2, 2, 2, 2, 2, "career_officer"))
    c = force_counts(force) if force else {}
    if c.get("dd", 0) + c.get("cv", 0) + c.get("ss", 0) > 0:
        out.append(("Fleet Command", "nav", 2, 2, 2, 2, 2, "spotter"))
    return out


def character_block(tag: str, ndiv: int, force: tuple[int, ...]) -> str:
    parts = []
    for slot, trait, label in (
        ("army_chief", "dd_john_army", "John Army"),
        ("air_chief", "dd_john_airforce", "John Airforce"),
        ("navy_chief", "dd_john_navy", "John Navy"),
    ):
        cid = {
            "dd_john_army": f"{tag}_john_army",
            "dd_john_airforce": f"{tag}_john_airforce",
            "dd_john_navy": f"{tag}_john_navy",
        }[trait]
        parts.append(
            f"	{cid} = {{\n"
            f'		name = "{label}"\n'
            "		portraits = {\n"
            "			army = { large = GFX_portrait_john_staff small = GFX_portrait_john_staff }\n"
            "			navy = { large = GFX_portrait_john_staff small = GFX_portrait_john_staff }\n"
            "			civilian = { large = GFX_portrait_john_staff small = GFX_portrait_john_staff }\n"
            "		}\n"
            "		advisor = {\n"
            f"			slot = {slot}\n"
            f"			idea_token = {cid}\n"
            "			cost = 100\n"
            f"			allowed = {{ original_tag = {tag} }}\n"
            "			traits = { " + trait + " }\n"
            "			ai_will_do = { factor = 1 }\n"
            "		}\n"
            "	}"
        )
    for i, row in enumerate(commander_list(tag, ndiv, force)):
        name, role, skill, atk, dfn, pln, log, traits = row
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:24]
        cid = f"{tag}_{role}_{slug}"[:40]
        skill = max(1, min(5, int(skill)))
        atk = max(1, min(5, int(atk)))
        dfn = max(1, min(5, int(dfn)))
        pln = max(1, min(5, int(pln)))
        log = max(1, min(5, int(log)))
        key = {"fm": "field_marshal", "gen": "corps_commander", "nav": "navy_leader"}[role]
        portraits = "army" if role != "nav" else "navy"
        if role == "nav":
            skill_lines = (
                f"			skill = {skill}\n"
                f"			attack_skill = {atk}\n"
                f"			defense_skill = {dfn}\n"
                f"			maneuvering_skill = {pln}\n"
                f"			coordination_skill = {log}\n"
            )
        else:
            skill_lines = (
                f"			skill = {skill}\n"
                f"			attack_skill = {atk}\n"
                f"			defense_skill = {dfn}\n"
                f"			planning_skill = {pln}\n"
                f"			logistics_skill = {log}\n"
            )
        parts.append(
            f"	{cid} = {{\n"
            f'		name = "{name}"\n'
            "		portraits = {\n"
            f"			{portraits} = {{ large = GFX_portrait_unknown small = GFX_portrait_unknown }}\n"
            "		}\n"
            f"		{key} = {{\n"
            f"			traits = {{ {traits} }}\n"
            f"{skill_lines}"
            "			legacy_id = 0\n"
            "		}\n"
            "	}"
        )
    return "\n".join(parts)


def write_characters(tags: list[str], countries: dict, divs: dict[str, int], forces: dict[str, tuple]) -> dict[str, list[str]]:
    CHARS_DIR.mkdir(parents=True, exist_ok=True)
    # wipe previous generated staff
    for p in CHARS_DIR.glob("doomsday_*.txt"):
        p.unlink()
    recruited: dict[str, list[str]] = {}
    chunk: list[str] = []
    n = 0
    file_i = 0

    def flush():
        nonlocal chunk, file_i, n
        if not chunk:
            return
        (CHARS_DIR / f"doomsday_staff_{file_i:02d}.txt").write_text(
            "characters = {\n" + "\n".join(chunk) + "\n}\n", encoding="utf-8"
        )
        chunk = []
        file_i += 1
        n = 0

    for tag in tags:
        force = forces.get(tag, (0,) * 14)
        ndiv = divs.get(tag, 0)
        block = character_block(tag, ndiv, force)
        ids = re.findall(r"^\t([A-Z0-9]{3}_[a-z0-9_]+) = \{", block, re.M)
        recruited[tag] = ids
        chunk.append(block)
        n += 1
        if n >= 25:
            flush()
    flush()
    return recruited


def write_basing() -> None:
    lines = [
        "# Foreign basing access. Deterministic. Flag-guarded. Country-scoped.",
        "on_actions = {",
        "	on_startup = {",
        "		effect = {",
        "			if = {",
        "				limit = { NOT = { has_global_flag = dd_basing_init } }",
        "				set_global_flag = dd_basing_init",
    ]
    for host, guest in foreign_pairs():
        if host == guest:
            continue
        lines.append(f"				{host} = {{")
        lines.append(f"					give_military_access = {guest}")
        lines.append(f"					give_docking_rights = {guest}")
        lines.append("				}")
    lines += ["			}", "		}", "	}", "}"]
    path = ROOT / "common" / "on_actions" / "doomsday_basing.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "start_basing.json").write_text(
        json.dumps({"pairs": [{"host": h, "guest": g} for h, g in foreign_pairs()]}, indent=2),
        encoding="utf-8",
    )


def write_tga(path: Path, w: int, h: int, rgb: tuple[int, int, int]) -> None:
    header = bytes([
        0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        w & 255, (w >> 8) & 255, h & 255, (h >> 8) & 255, 24, 32,
    ])
    px = bytes((rgb[2], rgb[1], rgb[0])) * w
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + px * h)


def _flag_rgb(tag: str) -> tuple[int, int, int]:
    n = 2166136261
    for ch in tag.encode("ascii"):
        n ^= ch
        n = (n * 16777619) & 0xFFFFFFFF
    r = 40 + (n & 127)
    g = 40 + ((n >> 8) & 127)
    b = 40 + ((n >> 16) & 127)
    return r, g, b


def write_new_flags() -> None:
    path = ROOT / "common" / "country_tags" / "doomsday_countries.txt"
    tags = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Z0-9]{3})\s*=", line)
        if m:
            tags.append(m.group(1))
    flag_root = ROOT / "gfx" / "flags"
    for tag in tags:
        rgb = _flag_rgb(tag)
        write_tga(flag_root / f"{tag}.tga", 82, 52, rgb)
        write_tga(flag_root / "medium" / f"{tag}.tga", 41, 26, rgb)
        write_tga(flag_root / "small" / f"{tag}.tga", 10, 7, rgb)


def country_names(tag: str, row: dict | None) -> tuple[str, str, str]:
    name = (row or {}).get("name") or tag_display_name(tag)
    adj = ADJ.get(tag)
    if not adj:
        adj = name + ("n" if not name.endswith("n") else "")
    the = name if name.lower().startswith("the ") else name
    return name, the, adj


def write_name_loc(countries: dict[str, dict], tags: list[str]) -> None:
    lines = ["l_english:"]
    for tag in tags:
        name, the, adj = country_names(tag, countries.get(tag))
        lines.append(f' {tag}:0 "{name}"')
        lines.append(f' {tag}_DEF:0 "{the}"')
        lines.append(f' {tag}_ADJ:0 "{adj}"')
        lines.append(f' {tag}_john_army:0 "John Army"')
        lines.append(f' {tag}_john_airforce:0 "John Airforce"')
        lines.append(f' {tag}_john_navy:0 "John Navy"')
    loc = ROOT / "localisation" / "replace"
    loc.mkdir(parents=True, exist_ok=True)
    (loc / "doomsday_country_names_l_english.yml").write_bytes(
        b"\xef\xbb\xbf" + ("\n".join(lines) + "\n").encode("utf-8")
    )
    staff = ["l_english:", ' JOHN_ARMY:0 "John Army"', ' JOHN_AIRFORCE:0 "John Airforce"', ' JOHN_NAVY:0 "John Navy"']
    (ROOT / "localisation" / "english" / "doomsday_staff_l_english.yml").write_bytes(
        b"\xef\xbb\xbf" + ("\n".join(staff) + "\n").encode("utf-8")
    )


def write_sidecars(countries: dict, tags: list[str], bits: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pol_rows = []
    for tag in tags:
        b = bits[tag]
        row = {"tag": tag, "ruling": b["ruling"], "last_election": b["last_election"],
               "election_frequency": b["freq"], "elections_allowed": int(b["elections"]),
               "research_slots": b["slots"], "tech_tier": b["tier"]}
        for p in PARENTS:
            row[p] = b["pops"].get(p, 0)
        pol_rows.append(row)
    if pol_rows:
        with (DATA_DIR / "start_politics.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(pol_rows[0].keys()))
            w.writeheader()
            w.writerows(pol_rows)
    with (DATA_DIR / "start_tech_tiers.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tag", "tier", "research_slots"])
        for tag in tags:
            w.writerow([tag, bits[tag]["tier"], bits[tag]["slots"]])
    with (DATA_DIR / "start_policies.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tag", "ideas"])
        for tag in tags:
            w.writerow([tag, " ".join(bits[tag]["ideas"])])
    with (DATA_DIR / "start_debt_overrides.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tag", "debt", "treasury"])
        for tag in tags:
            w.writerow([tag, f"{bits[tag]['debt']:.4f}", f"{bits[tag]['treasury']:.4f}"])
    (DATA_DIR / "start_oob.json").write_text(
        json.dumps(_OOB_LOG, indent=2), encoding="utf-8"
    )
    cmd = {}
    for tag in tags:
        named = COMMANDERS.get(tag)
        if named:
            cmd[tag] = [
                {
                    "name": r[0], "role": r[1], "skill": r[2],
                    "attack": r[3], "defense": r[4], "planning": r[5],
                    "logistics": r[6], "traits": r[7],
                    "source": "public 2026 command list",
                }
                for r in named
            ]
    (DATA_DIR / "start_commanders.json").write_text(
        json.dumps(cmd, indent=2), encoding="utf-8"
    )
    sources = (DATA_DIR / "SOURCES.md").read_text(encoding="utf-8") if (DATA_DIR / "SOURCES.md").exists() else ""
    extra = """
## Starting setup (2026 audit)

- Research slots: 5 USA/CHI; 4 other high-tech majors; 3 high-income industrial; 2 typical on-map; 1 micros/releasables.
- Extra starting tech is a documented overlay on the universal Cold War floor. `MUST_NOT_START` IDs are never granted.
- Land OOB: 1 locked HOI4 division ≈ one real division or a packed brigade set. Surplus stockpile is reserve-only (~15%, 22% USA/CHI), never equal to equipment already on divisions.
- Foreign bases: the host grants `give_military_access` and `give_docking_rights` in its guest's country history before the OOB loads, and again on startup. Access exists only where a division, wing, or ship actually spawns. Own-soil holdings (Guam, Guantanamo, Falklands, French overseas territories) need no access.
- Commanders: public 2026 command lists where named; generic Army/Fleet Command otherwise. Skills 1–4 (5 only wartime standouts). No random.
- Debt zeros: DPK 18% of GDP (opaque, not debt-free); Singapore 40% gross debt and high treasury (SWF). Norway/Gulf keep debt, higher treasury.
"""
    if "## Starting setup (2026 audit)" not in sources:
        (DATA_DIR / "SOURCES.md").write_text(sources.rstrip() + "\n" + extra, encoding="utf-8")


_PROD: dict[str, float] | None = None


def productivity_for(tag: str) -> float:
    global _PROD
    if _PROD is None:
        from productivity import all_productivity
        _PROD = all_productivity()
    return _PROD.get(tag, 1.0)


def history_bits(tag: str, row: dict | None) -> dict:
    ideology = resolve(tag, (row or {}).get("ideology") or "", (row or {}).get("subideology") or "")
    last, freq, allowed = election_fields(tag, row, ideology)
    debt, treasury = debt_treasury(tag, row)
    return {
        "ruling": ideology,
        "pops": ideology_pie(tag, ideology, row),
        "last_election": last,
        "freq": freq,
        "elections": allowed,
        "slots": research_slots(tag, row),
        "tier": tech_tier(tag) if tag in on_map_tags() else 0,
        "ideas": policies_for(tag, ideology, row),
        "debt": debt,
        "treasury": treasury,
        "prod": productivity_for(tag),
        "extra_techs": extra_techs(tag),
        "stab": 0.90,
        "ws": 0.70,
    }


def apply_to_write_country(tag: str, row: dict | None) -> dict:
    """Used by generate_doomsday.write_country."""
    return history_bits(tag, row)


def apply(write_country_cb=None) -> None:
    from generate_doomsday import (
        parse_tags, vanilla_history_names, vanilla_capitals, read_csv_countries, write_country,
    )
    countries = read_csv_countries()
    tags_pairs = parse_tags()
    hist_names = vanilla_history_names()
    capitals = vanilla_capitals()
    for path in COUNTRIES_DIR.glob("*.txt"):
        tag = path.name.split(" ")[0].strip()
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"capital\s*=\s*(\d+)", text)
        if m:
            capitals[tag] = int(m.group(1))
    faction_members: dict[str, list[str]] = defaultdict(list)
    for tag, row in countries.items():
        fac = (row.get("faction") or "").strip()
        if fac:
            faction_members[fac].append(tag)
    build_locations()
    prepare_access()
    tag_list = [t for t, _ in tags_pairs]
    bits = {tag: history_bits(tag, countries.get(tag)) for tag in tag_list}
    divs: dict[str, int] = {}
    forces: dict[str, tuple] = {}
    oob_info: dict[str, tuple] = {}
    for tag in tag_list:
        row = countries.get(tag)
        force = estimate_force(tag, row) if tag in on_map_tags() else (0,) * 14
        forces[tag] = force
        oob, naval, surplus, ndiv = write_oob_files(tag, row)
        oob_info[tag] = (oob, naval, surplus)
        divs[tag] = ndiv
        bits[tag]["oob"] = oob
        bits[tag]["naval_oob"] = naval
        bits[tag]["surplus"] = surplus
    recruited = write_characters(tag_list, countries, divs, forces)
    for tag in tag_list:
        bits[tag]["characters"] = recruited.get(tag, staff_ids(tag))
    global _BITS, _OOB
    _BITS = bits
    _OOB = oob_info
    apply._bits = bits  # type: ignore[attr-defined]
    apply._oob = oob_info  # type: ignore[attr-defined]
    import sys
    other = sys.modules.get("start_setup")
    if other is not None and other is not sys.modules[__name__]:
        other._BITS = bits
        other._OOB = oob_info
        other.apply._bits = bits
        other.apply._oob = oob_info
    for tag, country_file in tags_pairs:
        fname = hist_names.get(tag, f"{tag} - {country_file}")
        write_country(tag, fname, countries.get(tag), capitals.get(tag, 1), faction_members)
    write_basing()
    write_new_flags()
    write_name_loc(countries, tag_list)
    write_sidecars(countries, tag_list, bits)
    print("start setup tags", len(tag_list), "on_map", len(on_map_tags()), "oob files", len(list(UNITS_DIR.glob("*_2026*.txt"))))


# populated during apply()
apply._bits = {}  # type: ignore[attr-defined]
apply._oob = {}  # type: ignore[attr-defined]


def current_bits(tag: str, row: dict | None) -> dict:
    cache = _BITS or getattr(apply, "_bits", {})
    if tag in cache:
        return cache[tag]
    return history_bits(tag, row)


def current_oob(tag: str) -> tuple[str, str | None, list[str]]:
    cache = _OOB or getattr(apply, "_oob", {})
    if tag in cache:
        return cache[tag]
    if tag in on_map_tags():
        return f"{tag}_2026", None, []
    return "DOOMSDAY_EMPTY", None, []


if __name__ == "__main__":
    import start_setup as _ss
    _ss.apply()
