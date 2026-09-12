#!/usr/bin/env python3
"""Freeze GADM-1 VIIRS mean radiance for HOI4 state infrastructure.

Source: GLocal annualized GID1 `viirs_custom_mean` (NASA/NOAA VIIRS via
Harvard Dataverse doi:10.7910/DVN/6TUCTE), names from FAO GADM 3.6.
No country LPI. Deterministic once this JSON is frozen.
"""
from __future__ import annotations

import csv
import json
import ssl
import urllib.request
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parent / "data"
PARQUET = DATA / "_glocal_annualized_level_1.parquet"
GADM_CSV = DATA / "_gadm36_1.csv"
OUT = DATA / "admin1_ntl.json"

GL_FILE_ID = "7614128"
GADM_URL = (
    "https://data.apps.fao.org/catalog/dataset/"
    "d4c071c1-3e5a-46f7-b335-864d94cf3677/resource/"
    "e09872b4-f505-431a-8973-e8e72503d7c7/download/gadm36_1.csv"
)
UA = "DoomsdayMod/1.0 (research snapshot)"
CTX = ssl.create_default_context()
# GLocal v3 `viirs` annual series ends 2021. 2022–2023 rows exist but are empty.
YEAR = 2021
# Area-weighted radiance (nW/cm2/sr), dark pixels included. Global quintiles
# crush Europe to 5 because Siberia/Sahara dominate the left tail.
# These cuts split Corsica (~0.53) from Île-de-France (~7.8).
NTL_BREAKS = [0.08, 0.35, 1.20, 4.00]


def _norm(name: str) -> str:
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = (
        text.replace("ł", "l")
        .replace("Ł", "l")
        .replace("đ", "d")
        .replace("ø", "o")
        .replace("Ø", "o")
        .replace("ß", "ss")
        .replace("æ", "ae")
        .replace("œ", "oe")
    )
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=CTX, timeout=180) as resp:
        dest.write_bytes(resp.read())


def _ensure_inputs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if not PARQUET.exists():
        url = f"https://dataverse.harvard.edu/api/access/datafile/{GL_FILE_ID}"
        print("downloading GLocal annualized_level_1.parquet...")
        _download(url, PARQUET)
    if not GADM_CSV.exists():
        print("downloading FAO gadm36_1.csv...")
        _download(GADM_URL, GADM_CSV)


def _gadm_names() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    with GADM_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            gid = (row.get("GID_1") or "").strip()
            names = [row.get("NAME_1") or ""]
            var = row.get("VARNAME_1") or ""
            names.extend(p.strip() for p in var.split("|") if p.strip())
            out[gid] = [n for n in names if n]
    return out


def _breaks(_values: list[float]) -> list[float]:
    return list(NTL_BREAKS)


def main() -> None:
    _ensure_inputs()
    names = _gadm_names()
    # Area-weighted `viirs` (dark pixels included). Lit-pixel custom_mean
    # makes Corsica look like a metro. Series ends 2021 in GLocal v3.
    table = pq.read_table(
        PARQUET,
        columns=["GID_1", "year", "viirs"],
    )
    years = table.column("year").to_pylist()
    gids = table.column("GID_1").to_pylist()
    means = table.column("viirs").to_pylist()
    latest: dict[str, tuple[int, float]] = {}
    for gid, year, mean in zip(gids, years, means):
        if mean is None or year is None:
            continue
        year = int(year)
        if year > YEAR:
            continue
        mean = float(mean)
        if mean < 0:
            continue
        prev = latest.get(gid)
        if prev is None or year > prev[0]:
            latest[gid] = (year, mean)

    by_iso3: dict[str, dict[str, float]] = {}
    unique_means: list[float] = []
    used_year = {}
    for gid, (year, mean) in latest.items():
        iso3 = str(gid).split(".", 1)[0]
        unique_means.append(mean)
        used_year[year] = used_year.get(year, 0) + 1
        keys = {_norm(n) for n in names.get(gid, []) if _norm(n)}
        if not keys:
            keys = {_norm(gid)}
        slot = by_iso3.setdefault(iso3, {})
        for key in keys:
            slot[key] = round(mean, 4)

    breaks = _breaks(unique_means)
    payload = {
        "retrieved": date.today().isoformat(),
        "source": "GLocal annualized GID-1 area-weighted viirs (VIIRS DNB, dark pixels included). Names: FAO GADM 3.6.",
        "doi": "10.7910/DVN/6TUCTE",
        "gadm": "https://gadm.org/",
        "year_requested": YEAR,
        "year_counts": used_year,
        "metric": "viirs",
        "unit": "nW/cm2/sr",
        "breaks": breaks,
        "adm1_units": len(latest),
        "by_iso3": by_iso3,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print("adm1", len(latest), "iso3", len(by_iso3), "breaks", breaks)
    fra = by_iso3.get("FRA") or {}
    for key in ("corse", "corsica", "iledefrance", "iledefrance", "provence", "bretagne", "brittany"):
        if key in fra:
            print(f"  FRA {key}={fra[key]}")
    usa = by_iso3.get("USA") or {}
    for key in ("newyork", "california", "texas", "alaska", "wyoming"):
        if key in usa:
            print(f"  USA {key}={usa[key]}")


if __name__ == "__main__":
    main()
