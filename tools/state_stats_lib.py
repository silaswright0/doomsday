"""Shared helpers for the 2026 state manpower/buildings pipeline.

Deterministic. No random. Does not rewrite owners, cores, VPs, or province buildings.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
DATA = TOOLS / "data"
STATES_DIR = ROOT / "history" / "states"
COUNTRIES_CSV = TOOLS / "doomsday_countries.csv"
STATES_CSV = TOOLS / "doomsday_states.csv"
GAZETTEER_CSV = TOOLS / "state_gazetteer.csv"

# Goods VA = World Bank industry (mining, manufacturing, utilities, construction)
# plus agriculture. Not GDP (excludes services/finance). $35B keeps USA/China
# civs near the old manufacturing scale while oil/farm economies pick up factories.
CIV_PER_GOODS_B = 35.0
CIV_MIN_GOODS_B = 2.0
CIV_SOFT_FLOOR_B = 0.5
# When industry+agri are missing, scale manufacturing by the world IND/MANF ratio.
MVA_TO_INDUSTRY = 1.67
CIV_PER_MVA_B = CIV_PER_GOODS_B
CIV_MIN_MVA_B = CIV_MIN_GOODS_B
# Milex is no longer the mil count. Kept for ammo stockpiles / extra_buildings.
MIL_PROCUREMENT_SHARE = 0.35
MIL_PER_PROC_B = 10.0
WARTIME_MIL_MULT = 2.5
DIB_MILS_PATH = DATA / "dib_mils.json"
DIB_DOCKS_PATH = DATA / "dib_docks.json"
DIB_FINANCE_PATH = DATA / "dib_finance.json"
DIB_REFINERIES_PATH = DATA / "dib_refineries.json"
DIB_SILOS_PATH = DATA / "dib_fuel_silos.json"
DIB_GRID_PATH = DATA / "dib_grid.json"
ADMIN1_NTL_PATH = DATA / "admin1_ntl.json"
FACTORY_LEVEL_CAP = 40
SHARED_SLOTS_CAP = 50
GW_PER_RENEWABLE_PARK = 20.0
RENEWABLE_PARK_CAP = 10
DOCK_PER_MILLION_GT = 1.2  # retired GT-only formula; allocate uses docks_from_sources
DOCK_DWT_PER_DOCK = 2_000_000  # 1 merchant dock per 2 million dwt
DOCK_MIN_DWT = 800_000  # below this, merchant GT is not a dock (PHI/USA problem)
MIN_MANPOWER = 1000
SRV_PER_B = 250.0
SRV_MIN_B = 20.0

# World Bank LPI is retired as a live path. Kept so old CSV country rows still parse.
LPI_BREAKS = (2.5, 3.0, 3.5, 4.5)
# Area-weighted VIIRS nW/cm2/sr (GLocal `viirs`, 2021). Not lit-pixel custom_mean.
NTL_BREAKS = (0.08, 0.35, 1.20, 4.00)

CAT_SLOTS = {
    "megalopolis": 12,
    "metropolis": 10,
    "large_city": 8,
    "city": 6,
    "large_town": 5,
    "town": 4,
    "large_island": 3,
    "rural": 2,
    "small_island": 1,
    "pastoral": 1,
    "wasteland": 0,
    "tiny_island": 0,
    "enclave": 0,
}

ISLAND_CATS = frozenset({"tiny_island", "small_island", "large_island", "enclave"})
URBAN_CATS = frozenset({"megalopolis", "metropolis", "large_city", "city", "large_town"})
# Services offices sit in real metros, not every large_town in a rich country.
SERVICE_CATS = frozenset({"megalopolis", "metropolis", "large_city", "city"})

DENSITY_BY_CAT = {
    "megalopolis": 80,
    "metropolis": 50,
    "large_city": 35,
    "city": 22,
    "large_town": 14,
    "town": 8,
    "large_island": 6,
    "rural": 4,
    "small_island": 3,
    "pastoral": 1,
    "wasteland": 1,
    "tiny_island": 2,
    "enclave": 20,
}

STATE_RE = {
    "id": re.compile(r"\bid\s*=\s*(\d+)"),
    "name": re.compile(r'\bname\s*=\s*"([^"]+)"'),
    "manpower": re.compile(r"\bmanpower\s*=\s*(\d+)"),
    "category": re.compile(r"\bstate_category\s*=\s*\"?(\w+)\"?"),
    "owner": re.compile(r"\bowner\s*=\s*([A-Z0-9]{3})"),
}


def extract_block(text: str, start: int) -> tuple[str, int]:
    i = text.find("{", start)
    if i < 0:
        return "", start
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1], j + 1
    return text[i:], len(text)


def pretty_name_from_file(filename: str) -> str:
    stem = Path(filename).stem
    m = re.match(r"^\d+\s*-?\s*(.*)$", stem)
    name = (m.group(1) if m else stem).strip()
    name = re.sub(r"\s+", " ", name)
    return name


def lpi_to_infra(score: float) -> int:
    """Retired country LPI mapping. Allocate uses ntl_to_infra."""
    if score < LPI_BREAKS[0]:
        return 1
    if score < LPI_BREAKS[1]:
        return 2
    if score < LPI_BREAKS[2]:
        return 3
    if score < LPI_BREAKS[3]:
        return 4
    return 5


def ntl_to_infra(mean: float) -> int:
    """HOI4 1–5 from area-weighted VIIRS mean radiance. No country offset."""
    if mean < NTL_BREAKS[0]:
        return 1
    if mean < NTL_BREAKS[1]:
        return 2
    if mean < NTL_BREAKS[2]:
        return 3
    if mean < NTL_BREAKS[3]:
        return 4
    return 5


def category_infra(category: str, is_capital: bool, impassable: bool) -> int:
    """Fallback when an HOI4 state misses GADM-1 lights. Still per-state, not LPI."""
    if impassable:
        return 1
    table = {
        "wasteland": 1,
        "pastoral": 1,
        "rural": 2,
        "town": 2,
        "large_town": 3,
        "city": 3,
        "large_city": 4,
        "metropolis": 4,
        "megalopolis": 5,
        "large_island": 2,
        "small_island": 2,
        "tiny_island": 1,
        "enclave": 3,
    }
    n = table.get(category, 2)
    if is_capital:
        n = min(5, n + 1)
    return n


# Last published SNA shares × current GDP when World Bank current USD is missing.
GOODS_SHARE_FALLBACK = {
    "VEN": {"ind": 0.372, "agr": 0.050, "note": "OECD SNA 2014 shares; WB 2011 series is zeroed"},
}


def goods_va_b(industry_b: float, agriculture_b: float, mva_b: float = 0.0) -> float:
    """Primary + secondary value added in US$ billions.

    Industry (NV.IND.TOTL) already includes manufacturing, mining, utilities,
    and construction. Agriculture is added on top. Manufacturing-only is the
    fallback when industry is missing (common World Bank hole), scaled by the
    world industry/manufacturing ratio so Taiwan-style MVA-only tags stay honest.
    """
    goods = max(0.0, float(industry_b or 0)) + max(0.0, float(agriculture_b or 0))
    if goods > 0:
        return goods
    return max(0.0, float(mva_b or 0)) * MVA_TO_INDUSTRY


def factories_from_goods(goods_b: float) -> int:
    if goods_b >= CIV_MIN_GOODS_B:
        return max(1, int(round(goods_b / CIV_PER_GOODS_B)))
    if goods_b >= CIV_SOFT_FLOOR_B:
        return 1
    return 0


def factories_from_mva(mva_b: float) -> int:
    """Back-compat alias. New code should pass goods VA, not manufacturing."""
    return factories_from_goods(mva_b)


_DIB_CACHE: dict | None = None


def load_dib_mils() -> dict:
    """tag -> mils for territorial DIBs. Missing tag is 0. Landless tags are not in the file."""
    global _DIB_CACHE
    if _DIB_CACHE is None:
        payload = json.loads(DIB_MILS_PATH.read_text(encoding="utf-8"))
        _DIB_CACHE = {
            tag: int(rec.get("mils") or 0)
            for tag, rec in (payload.get("tags") or {}).items()
        }
    return _DIB_CACHE


def mils_from_dib(tag: str) -> int:
    return max(0, load_dib_mils().get(tag, 0))


def mils_from_sipri(sipri_b: float, wartime: bool) -> int:
    """Retired budget formula. Allocate uses mils_from_dib. Wartime×2.5 is not used:
    peacetime plants already operate; do not multiply the DIB because a tag is at war.
    """
    mils = int(round(sipri_b * MIL_PROCUREMENT_SHARE / MIL_PER_PROC_B))
    if wartime:
        scaled = int(round(sipri_b * MIL_PROCUREMENT_SHARE * WARTIME_MIL_MULT / MIL_PER_PROC_B))
        mils = max(mils, scaled)
    return max(0, mils)


def parks_from_gw(gw: float) -> int:
    if gw <= 0:
        return 0
    return max(0, int(round(gw / GW_PER_RENEWABLE_PARK)))


def docks_from_gt_million(gt_m: float) -> int:
    """Retired GT-only formula. Allocate uses docks_from_sources."""
    if gt_m <= 0:
        return 0
    return max(0, int(round(gt_m * DOCK_PER_MILLION_GT)))


_DOCK_CACHE: dict | None = None
_DWT_ALIASES = {
    "Vietnam": "Viet Nam",
    "South Korea": "Republic of Korea",
    "United States": "United States of America",
    "Russia": "Russian Federation",
    "Taiwan Province of China": "Taiwan",
    "UAE": "United Arab Emirates",
    "Türkiye": "Turkey",
}


def load_dib_docks() -> dict:
    """tag -> naval construction campuses. Missing tag is 0."""
    global _DOCK_CACHE
    if _DOCK_CACHE is None:
        payload = json.loads(DIB_DOCKS_PATH.read_text(encoding="utf-8"))
        _DOCK_CACHE = {
            tag: int(rec.get("docks") or 0)
            for tag, rec in (payload.get("naval") or {}).items()
        }
    return _DOCK_CACHE


def load_merchant_dwt() -> dict:
    payload = json.loads(DIB_DOCKS_PATH.read_text(encoding="utf-8"))
    merchant = payload.get("merchant") or {}
    rows = dict(merchant.get("rows_dwt") or {})
    for alias, canon in _DWT_ALIASES.items():
        if canon in rows and alias not in rows:
            rows[alias] = rows[canon]
    return rows


def merchant_docks_from_dwt(dwt: float) -> int:
    """Commercial industrial base. Tiny GT (Philippines, US Jones Act) is not a dock."""
    if dwt < DOCK_MIN_DWT:
        return 0
    return max(1, int(round(dwt / DOCK_DWT_PER_DOCK)))


def docks_from_sources(tag: str, dwt: float) -> int:
    """Merchant DWT + Janes/IISS naval campuses. NavBase fleet tons are not added."""
    return merchant_docks_from_dwt(dwt) + max(0, load_dib_docks().get(tag, 0))


def load_campus_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        tag: int(rec.get("count") or rec.get("docks") or rec.get("mils") or 0)
        for tag, rec in (payload.get("tags") or {}).items()
    }


_NTL_CACHE: dict | None = None


def load_admin1_ntl() -> dict:
    """iso3 -> {norm_name: viirs mean} plus frozen breaks."""
    global _NTL_CACHE
    if _NTL_CACHE is None:
        if not ADMIN1_NTL_PATH.exists():
            _NTL_CACHE = {"breaks": list(NTL_BREAKS), "by_iso3": {}}
        else:
            _NTL_CACHE = json.loads(ADMIN1_NTL_PATH.read_text(encoding="utf-8"))
    return _NTL_CACHE


def services_va_b(gdp_b: float, industry_b: float, agriculture_b: float, services_b: float = 0.0) -> float:
    if services_b and services_b > 0:
        return float(services_b)
    return max(0.0, float(gdp_b or 0) - float(industry_b or 0) - float(agriculture_b or 0))


def services_from_va(va_b: float) -> int:
    if va_b >= SRV_MIN_B:
        return max(1, int(round(va_b / SRV_PER_B)))
    return 0


def category_from_pop(pop: int, old_cat: str, impassable: bool = False) -> str:
    if old_cat in ISLAND_CATS:
        return old_cat
    if impassable and pop < 200_000:
        return "wasteland"
    if pop < 50_000:
        return "wasteland"
    if pop < 200_000:
        return "pastoral"
    if pop < 800_000:
        return "rural"
    if pop < 2_000_000:
        return "town"
    if pop < 5_000_000:
        return "large_town"
    if pop < 12_000_000:
        return "city"
    if pop < 25_000_000:
        return "large_city"
    if pop < 40_000_000:
        return "metropolis"
    return "megalopolis"


def extra_slots(category: str, civs: int, mils: int, docks: int, extras: dict[str, int]) -> int:
    cat_slots = CAT_SLOTS.get(category, 2)
    shared_extra = (
        extras.get("finance_center", 0)
        + extras.get("services_building", 0)
        + extras.get("renewable_park", 0)
        + extras.get("synthetic_refinery", 0)
        + extras.get("fuel_silo", 0)
        + extras.get("energy_infrastructure", 0)
    )
    needed = civs + mils + docks + shared_extra + 2
    extra_cap = max(0, SHARED_SLOTS_CAP - cat_slots)
    return min(max(0, needed - cat_slots), extra_cap)


def extra_buildings_for(gdp_b: float, is_capital: bool, category: str, civs: int) -> dict[str, int]:
    """Retired GDP smear. Allocate places finance from GFCI and services from VA."""
    return {}


def distribute(total: int, weights: list[float]) -> list[int]:
    n = len(weights)
    if total <= 0 or not weights:
        return [0] * n
    safe = [max(float(w), 0.0) for w in weights]
    s = sum(safe)
    if s <= 0:
        safe = [1.0] * n
        s = float(n)
    raw = [total * w / s for w in safe]
    out = [int(x) for x in raw]
    rem = total - sum(out)
    order = sorted(range(n), key=lambda i: raw[i] - out[i], reverse=True)
    for i in order:
        if rem <= 0:
            break
        out[i] += 1
        rem -= 1
    return out


def cap_distribute(total: int, weights: list[float], cap: int) -> list[int]:
    out = distribute(total, weights)
    leftover = 0
    for i, n in enumerate(out):
        if n > cap:
            leftover += n - cap
            out[i] = cap
    if leftover and out:
        order = sorted(range(len(out)), key=lambda i: weights[i], reverse=True)
        changed = True
        while leftover and changed:
            changed = False
            for i in order:
                if leftover <= 0:
                    break
                if out[i] < cap:
                    out[i] += 1
                    leftover -= 1
                    changed = True
    return out


def parse_state_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    sid = STATE_RE["id"].search(text)
    owner = STATE_RE["owner"].search(text)
    cat = STATE_RE["category"].search(text)
    man = STATE_RE["manpower"].search(text)
    loc = STATE_RE["name"].search(text)
    provinces = []
    mprov = re.search(r"provinces\s*=\s*\{([^}]*)\}", text)
    if mprov:
        provinces = [int(x) for x in re.findall(r"\d+", mprov.group(1))]
    resources: dict[str, int] = {}
    rm = re.search(r"\bresources\s*=", text)
    if rm:
        block, _ = extract_block(text, rm.start())
        for key, val in re.findall(r"(\w+)\s*=\s*(\d+)", block):
            resources[key] = int(val)
    buildings_state: dict[str, int] = {}
    bm = re.search(r"\bbuildings\s*=", text)
    nested = ""
    if bm:
        block, _ = extract_block(text, bm.start())
        inner = block[1:-1]
        nested_parts = []

        def keep_nested(m: re.Match) -> str:
            nested_parts.append(m.group(0))
            return " "

        stripped = re.sub(r"\d+\s*=\s*\{(?:[^{}]|\{[^{}]*\})*\}", keep_nested, inner, flags=re.S)
        nested = "\n".join(nested_parts)
        for key, val in re.findall(r"(\w+)\s*=\s*(\d+)", stripped):
            buildings_state[key] = int(val)
    return {
        "path": path,
        "file": path.name,
        "id": int(sid.group(1)) if sid else 0,
        "loc_name": loc.group(1) if loc else "",
        "pretty": pretty_name_from_file(path.name),
        "manpower": int(man.group(1) if man else 0),
        "category": cat.group(1) if cat else "rural",
        "owner": owner.group(1) if owner else "XXX",
        "impassable": bool(re.search(r"\bimpassable\s*=\s*yes", text)),
        "provinces": provinces,
        "province_count": len(provinces),
        "coastal": bool(re.search(r"\bnaval_base\s*=", text)),
        "resources": resources,
        "buildings": buildings_state,
        "nested_buildings": nested,
        "raw": text,
    }


def load_all_states() -> list[dict]:
    states = [parse_state_file(p) for p in sorted(STATES_DIR.glob("*.txt"))]
    return [s for s in states if s["id"]]


def load_countries() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with COUNTRIES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            tag = (row.get("tag") or "").strip()
            if tag:
                rows[tag] = row
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def group_by_owner(states: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for s in states:
        out[s["owner"]].append(s)
    return out
