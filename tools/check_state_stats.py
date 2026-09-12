#!/usr/bin/env python3
"""Checksum allocated state stats against country control totals and building caps."""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import COUNTRIES_CSV, STATES_CSV, load_all_states, load_dib_mils  # noqa: E402


def main() -> int:
    countries = {}
    with COUNTRIES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            countries[row["tag"]] = row
    by_tag: dict[str, list[dict]] = defaultdict(list)
    errors: list[str] = []
    with STATES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_tag[row["owner_2026"]].append(row)
            sid = row["state_id"]
            infra = int(row["infra"])
            if infra < 1 or infra > 5:
                errors.append(f"state {sid} infra {infra} not in 1-5")
            for key, cap in (("civs", 40), ("mils", 40), ("docks", 40), ("renewable", 10),
                             ("finance", 20), ("services", 20), ("refinery", 3),
                             ("fuel_silo", 3), ("energy_grid", 1)):
                val = int(row.get(key) or 0)
                if val < 0 or val > cap:
                    errors.append(f"state {sid} {key}={val} exceeds cap {cap}")
            if int(row["extra_slots"]) > 50:
                errors.append(f"state {sid} extra_slots {row['extra_slots']} > 50")
            if int(row["manpower"]) < 1000:
                errors.append(f"state {sid} manpower {row['manpower']} < 1000")

    world_mils = sum(int(r["mils"]) for rows in by_tag.values() for r in rows)
    dib_mils = sum(load_dib_mils().values())
    print(f"states {sum(len(v) for v in by_tag.values())} tags {len(by_tag)} world_mils={world_mils}")
    if world_mils != dib_mils:
        errors.append(f"world mils {world_mils} != DIB {dib_mils}")
    for tag, rows in sorted(by_tag.items()):
        pop = sum(int(r["manpower"]) for r in rows)
        target = int(float((countries.get(tag) or {}).get("pop") or 0))
        if target and abs(pop - target) > max(5, target * 0.002):
            errors.append(f"{tag} manpower {pop} != target {target}")
        civs = sum(int(r["civs"]) for r in rows)
        mils = sum(int(r["mils"]) for r in rows)
        docks = sum(int(r["docks"]) for r in rows)
        parks = sum(int(r["renewable"]) for r in rows)
        want_docks = int(float((countries.get(tag) or {}).get("docks") or 0))
        if docks != want_docks:
            errors.append(f"{tag} docks {docks} != target {want_docks}")
        print(f"  {tag}: pop={pop} civs={civs} mils={mils} docks={docks} parks={parks} states={len(rows)}")

    # Spot checks from the plan
    want = {
        "378": ("California", 30_000_000, 45_000_000),
        "375": ("Texas", 25_000_000, 38_000_000),
        "126": ("London", 6_000_000, 18_000_000),
    }
    by_id = {}
    with STATES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_id[row["state_id"]] = row
    for sid, (label, lo, hi) in want.items():
        rec = by_id.get(sid)
        if not rec:
            errors.append(f"missing spot-check state {sid} {label}")
            continue
        pop = int(rec["manpower"])
        if not lo <= pop <= hi:
            errors.append(f"{label} ({sid}) manpower {pop} not in [{lo}, {hi}]")
        print(f"spot {sid} {rec['loc_name']} pop={pop} civs={rec['civs']} parks={rec['renewable']} docks={rec['docks']}")

    korea = by_id.get("1030")
    if korea:
        print(f"spot 1030 {korea['loc_name']} docks={korea['docks']} civs={korea['civs']}")
        if int(korea["docks"]) < 5:
            errors.append(f"Gyeongsang docks {korea['docks']} expected major UNCTAD yard")

    shanghai = by_id.get("613")
    if shanghai:
        print(f"spot 613 {shanghai['loc_name']} pop={shanghai['manpower']} parks={shanghai['renewable']}")

    corsica = by_id.get("1")
    idf = by_id.get("16")
    if corsica and idf:
        print(f"spot 1 {corsica['loc_name']} infra={corsica['infra']} srv={corsica.get('services')}")
        print(f"spot 16 {idf['loc_name']} infra={idf['infra']} fin={idf.get('finance')} srv={idf.get('services')}")
        if int(corsica["infra"]) >= int(idf["infra"]):
            errors.append(
                f"Corsica infra {corsica['infra']} should be below Ile-de-France {idf['infra']}"
            )
    nyc = by_id.get("358")
    if nyc and int(nyc.get("finance") or 0) < 2:
        errors.append(f"New York finance {nyc.get('finance')} expected GFCI mega-centre")
    london = by_id.get("126")
    if london and int(london.get("finance") or 0) < 2:
        errors.append(f"London finance {london.get('finance')} expected GFCI mega-centre")
    sng = by_id.get("1021")
    if sng and int(sng["infra"]) < 5:
        errors.append(f"Singapore infra {sng['infra']} expected city-state lights 5")
    hk = by_id.get("326")
    if hk and int(hk["infra"]) < 5:
        errors.append(f"Hong Kong infra {hk['infra']} expected HKG district lights 5")

    for s in load_all_states():
        hist_docks = int(s["buildings"].get("dockyard") or 0)
        if hist_docks and not s["coastal"]:
            errors.append(
                f"state {s['id']} {s['pretty']} docks={hist_docks} not sea-coastal"
            )

    if errors:
        print("FAIL", len(errors))
        for e in errors[:40]:
            print(" ", e)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
