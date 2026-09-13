#!/usr/bin/env python3
"""Freeze OurAirports into country air-base control totals.

Raw CSV is gitignored (tools/data/_ourairports.csv). Re-download:
  https://davidmegginson.github.io/ourairports-data/airports.csv

1 HOI4 air_base = two military medium/large fields, or eight large
scheduled civilian fields (dual-use). Heliports and closed fields omitted.
Same formula for every ISO2. Does not use fighter inventories.
"""
from __future__ import annotations

import csv
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"
RAW = DATA / "_ourairports.csv"
OUT = DATA / "dib_air.json"
URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
MIL_PER_LEVEL = 2.0
LARGE_CIV_PER_LEVEL = 8.0

MIL_RE = re.compile(
    r"air force|\bafb\b|naval air|marine corps air|air national guard|"
    r"air base|airbase|raf |rnzaf|luchtmacht|armee de l.air|"
    r"voen|aviabaza|plaaf|jasdf|rokaf|iaf\b",
    re.I,
)
FLOORS = {
    "KOR": 12,
    "JAP": 18,
    "FOR": 8,
    "CAN": 8,
    "AST": 8,
    "ISR": 6,
    "DPK": 8,
    "SNG": 2,
}

from state_stats_geo import TAG_META  # noqa: E402

ISO3_TO_ISO2 = {
    "USA": "US", "CHN": "CN", "RUS": "RU", "GBR": "GB", "DEU": "DE",
    "KOR": "KR", "PRK": "KP", "TWN": "TW", "CZE": "CZ", "SVK": "SK",
    "ROU": "RO", "DNK": "DK", "GRC": "GR", "CHE": "CH", "AUT": "AT",
    "NLD": "NL", "IRL": "IE", "HRV": "HR", "SVN": "SI", "BIH": "BA",
    "MKD": "MK", "MNE": "ME", "SRB": "RS", "UKR": "UA", "BLR": "BY",
    "EST": "EE", "LVA": "LV", "LTU": "LT", "MDA": "MD", "AZE": "AZ",
    "KAZ": "KZ", "TKM": "TM", "KGZ": "KG", "TJK": "TJ", "ARM": "AM",
    "GEO": "GE", "SAU": "SA", "ARE": "AE", "OMN": "OM", "QAT": "QA",
    "BHR": "BH", "KWT": "KW", "YEM": "YE", "IRQ": "IQ", "IRN": "IR",
    "ISR": "IL", "PSE": "PS", "JOR": "JO", "LBN": "LB", "SYR": "SY",
    "EGY": "EG", "LBY": "LY", "TUN": "TN", "DZA": "DZ", "MAR": "MA",
    "SDN": "SD", "SSD": "SS", "ETH": "ET", "ERI": "ER", "DJI": "DJ",
    "SOM": "SO", "KEN": "KE", "UGA": "UG", "TZA": "TZ", "RWA": "RW",
    "BDI": "BI", "COD": "CD", "COG": "CG", "GAB": "GA", "CMR": "CM",
    "NGA": "NG", "GHA": "GH", "CIV": "CI", "SEN": "SN", "MLI": "ML",
    "BFA": "BF", "NER": "NE", "TCD": "TD", "CAF": "CF", "AGO": "AO",
    "ZMB": "ZM", "ZWE": "ZW", "MOZ": "MZ", "MWI": "MW", "MDG": "MG",
    "ZAF": "ZA", "NAM": "NA", "BWA": "BW", "LSO": "LS", "SWZ": "SZ",
    "IND": "IN", "PAK": "PK", "BGD": "BD", "LKA": "LK", "NPL": "NP",
    "BTN": "BT", "MMR": "MM", "THA": "TH", "LAO": "LA", "KHM": "KH",
    "VNM": "VN", "MYS": "MY", "SGP": "SG", "IDN": "ID", "PHL": "PH",
    "PNG": "PG", "AUS": "AU", "NZL": "NZ", "FJI": "FJ", "JPN": "JP",
    "MNG": "MN", "AFG": "AF", "TUR": "TR", "CYP": "CY", "MLT": "MT",
    "ISL": "IS", "NOR": "NO", "SWE": "SE", "FIN": "FI", "POL": "PL",
    "HUN": "HU", "BGR": "BG", "ALB": "AL", "ESP": "ES", "PRT": "PT",
    "ITA": "IT", "FRA": "FR", "BEL": "BE", "LUX": "LU", "CAN": "CA",
    "MEX": "MX", "GTM": "GT", "HND": "HN", "SLV": "SV", "NIC": "NI",
    "CRI": "CR", "PAN": "PA", "CUB": "CU", "HTI": "HT", "DOM": "DO",
    "JAM": "JM", "TTO": "TT", "BHS": "BS", "BRB": "BB", "COL": "CO",
    "VEN": "VE", "GUY": "GY", "SUR": "SR", "BRA": "BR", "ECU": "EC",
    "PER": "PE", "BOL": "BO", "PRY": "PY", "CHL": "CL", "ARG": "AR",
    "URY": "UY", "GRL": "GL", "XKX": "XK", "TWN": "TW",
}


def iso2_for_tag(tag: str) -> str | None:
    meta = TAG_META.get(tag) or {}
    iso3 = meta.get("iso3") or ""
    if iso3 in ISO3_TO_ISO2:
        return ISO3_TO_ISO2[iso3]
    if len(iso3) == 3:
        return iso3[:2]
    return None


def ensure_raw() -> None:
    if RAW.exists() and RAW.stat().st_size > 1_000_000:
        return
    print("downloading", URL)
    urllib.request.urlretrieve(URL, RAW)


def score_row(row: dict) -> tuple[float, float]:
    typ = row.get("type") or ""
    if typ not in {"medium_airport", "large_airport"}:
        return 0.0, 0.0
    blob = f"{row.get('name') or ''} {row.get('keywords') or ''}"
    if MIL_RE.search(blob):
        return 1.0, 0.0
    if typ == "large_airport" and row.get("scheduled_service") == "yes":
        return 0.0, 1.0
    return 0.0, 0.0


def levels(mil: float, civ: float) -> int:
    raw = mil / MIL_PER_LEVEL + civ / LARGE_CIV_PER_LEVEL
    if mil + civ <= 0:
        return 0
    return max(1, int(round(raw)))


def main() -> None:
    ensure_raw()
    by_iso2: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])
    with RAW.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            iso = row.get("iso_country") or ""
            mil, civ = score_row(row)
            if mil or civ:
                by_iso2[iso][0] += mil
                by_iso2[iso][1] += civ

    tags = {}
    iso2_to_tag = {}
    for tag in TAG_META:
        iso2 = iso2_for_tag(tag)
        if iso2:
            iso2_to_tag.setdefault(iso2, tag)

    for iso2, (mil, civ) in sorted(by_iso2.items()):
        tag = iso2_to_tag.get(iso2)
        if not tag:
            continue
        n = max(levels(mil, civ), FLOORS.get(tag, 0))
        if n <= 0:
            continue
        tags[tag] = {
            "count": n,
            "military_fields": int(mil),
            "large_civilian": int(civ),
        }

    payload = {
        "note": (
            "Combat airfields, not municipal strips. Military medium/large from "
            "OurAirports name/keywords; large scheduled airports are dual-use at "
            "1/8. Heliports and closed fields omitted. Same formula every tag."
        ),
        "sources": [
            "OurAirports airports.csv (davidmegginson/ourairports-data)",
        ],
        "formula": {
            "military_fields_per_level": MIL_PER_LEVEL,
            "large_civilian_per_level": LARGE_CIV_PER_LEVEL,
        },
        "tags": tags,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    world = sum(r["count"] for r in tags.values())
    print(f"wrote {OUT.name} tags={len(tags)} world_air={world}")
    for tag in ("USA", "CHI", "SOV", "RAJ", "ENG", "JAP", "KOR", "FOR"):
        rec = tags.get(tag) or {}
        print(f"  {tag} {rec}")


if __name__ == "__main__":
    main()
