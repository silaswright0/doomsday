#!/usr/bin/env python3
"""Allocate 2026 manpower, buildings, and resources onto every HOI4 state.

Country totals come from cited snapshots in tools/data/. Subnational rows only
allocate. Deterministic. Does not rewrite owners. Province naval/supply are
applied from this plan by apply_state_stats.py (existing ports are never deleted).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_geo import (  # noqa: E402
    ALUM_KEYWORDS,
    CHROME_KEYWORDS,
    CIV_KEYWORDS,
    COAL_KEYWORDS,
    COBALT_KEYWORDS,
    COPPER_KEYWORDS,
    DOCK_KEYWORDS,
    AIR_KEYWORDS,
    AA_KEYWORDS,
    RADAR_KEYWORDS,
    NAVAL_KEYWORDS,
    FINANCE_KEYWORDS,
    GRAPHITE_KEYWORDS,
    GRID_KEYWORDS,
    LITHIUM_KEYWORDS,
    MIL_KEYWORDS,
    OIL_KEYWORDS,
    REE_KEYWORDS,
    REFINERY_KEYWORDS,
    RENEW_KEYWORDS,
    RUBBER_KEYWORDS,
    SILO_KEYWORDS,
    STEEL_KEYWORDS,
    TAG_META,
    TUNGSTEN_KEYWORDS,
    WPP_GROUPS,
    keyword_bonus,
    load_state_loc_names,
    ntl_mean_for,
    official_region,
    official_weight,
)
from state_stats_lib import (  # noqa: E402
    COUNTRIES_CSV,
    DATA,
    DIB_FINANCE_PATH,
    DIB_GRID_PATH,
    DIB_NAVAL_PATH,
    DIB_REFINERIES_PATH,
    DIB_SILOS_PATH,
    GAZETTEER_CSV,
    ROOT,
    STATES_CSV,
    SERVICE_CATS,
    category_from_pop,
    category_infra,
    cap_distribute,
    distribute,
    docks_from_sources,
    extra_slots,
    factories_from_goods,
    goods_va_b,
    GOODS_SHARE_FALLBACK,
    group_by_owner,
    load_admin1_ntl,
    load_all_states,
    load_campus_counts,
    load_countries,
    load_merchant_dwt,
    mils_from_dib,
    ntl_to_infra,
    parks_from_gw,
    services_from_va,
    services_va_b,
    write_csv,
    DENSITY_BY_CAT,
)

OIL_PER_MBPD = 38.0
COAL_PER_MT = 0.08
STEEL_PER_MT = 0.18
ALUM_PER_KT = 0.012
TUNGSTEN_PER_KT = 2.0
CHROME_PER_KT = 0.012
COPPER_PER_KT = 0.025
GRAPHITE_PER_KT = 0.06
LITHIUM_PER_KT = 0.5
COBALT_PER_KT = 0.4
REE_PER_KT = 0.2
RUBBER_PER_KT = 0.025

RESOURCE_SCALE = {
    "oil": OIL_PER_MBPD,
    "coal": COAL_PER_MT,
    "steel": STEEL_PER_MT,
    "aluminium": ALUM_PER_KT,
    "tungsten": TUNGSTEN_PER_KT,
    "chromium": CHROME_PER_KT,
    "copper": COPPER_PER_KT,
    "graphite": GRAPHITE_PER_KT,
    "lithium": LITHIUM_PER_KT,
    "cobalt": COBALT_PER_KT,
    "rare_earths": REE_PER_KT,
    "rubber": RUBBER_PER_KT,
}

RESOURCE_KEYWORDS = {
    "oil": OIL_KEYWORDS,
    "coal": COAL_KEYWORDS,
    "steel": STEEL_KEYWORDS,
    "aluminium": ALUM_KEYWORDS,
    "tungsten": TUNGSTEN_KEYWORDS,
    "chromium": CHROME_KEYWORDS,
    "copper": COPPER_KEYWORDS,
    "graphite": GRAPHITE_KEYWORDS,
    "lithium": LITHIUM_KEYWORDS,
    "cobalt": COBALT_KEYWORDS,
    "rare_earths": REE_KEYWORDS,
    "rubber": RUBBER_KEYWORDS,
}


def jload(name: str) -> dict:
    path = DATA / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_named(table: dict, names: list[str]):
    for n in names:
        if n in table:
            return table[n]
    return None


def wb_value(wb: dict, iso3: str, key: str) -> float | None:
    rec = (wb.get("countries") or {}).get(iso3) or {}
    item = rec.get(key)
    if not item:
        return None
    return float(item["value"])


def main() -> None:
    states = load_all_states()
    loc_names = load_state_loc_names(ROOT)
    countries = load_countries()
    wb = jload("worldbank_by_iso3.json")
    wpp = (jload("un_wpp2026.json") or {}).get("rows") or {}
    irena = (jload("irena_renewable_gw.json") or {}).get("rows_mw") or {}
    dwt_map = load_merchant_dwt()
    ei = jload("energy_institute.json") or {}
    steel = (jload("worldsteel.json") or {}).get("rows_mt") or {}
    usgs = jload("usgs_minerals.json") or {}
    pixels = (jload("state_pixel_area.json") or {}).get("pixels_by_state") or {}

    # Merchant DWT lookup names. Naval campuses are added in docks_from_sources.

    mineral_maps = {
        "aluminium": usgs.get("aluminium_kt") or {},
        "tungsten": usgs.get("tungsten_kt") or {},
        "chromium": usgs.get("chromium_kt") or {},
        "copper": usgs.get("copper_kt") or {},
        "graphite": usgs.get("graphite_kt") or {},
        "lithium": usgs.get("lithium_kt") or {},
        "cobalt": usgs.get("cobalt_kt") or {},
        "rare_earths": usgs.get("rare_earths_kt") or {},
        "rubber": usgs.get("rubber_kt") or {},
    }

    # Attach loc names + area
    for s in states:
        s["loc_pretty"] = loc_names.get(s["id"]) or s["pretty"]
        s["pixels"] = float(pixels.get(str(s["id"])) or pixels.get(s["id"]) or s["province_count"] or 1)

    # Refresh country control totals
    group_index = {tag: parent for parent, tags in WPP_GROUPS.items() for tag in tags}
    refreshed = 0
    for tag, row in countries.items():
        meta = TAG_META.get(tag, {})
        iso3 = meta.get("iso3") or ""
        wpp_names = list(meta.get("wpp") or [])
        parent = group_index.get(tag)
        if parent:
            wpp_names = [parent]
        pop = None
        for name in wpp_names:
            if name in wpp:
                pop = int(wpp[name])
                break
        if parent and pop:
            members = WPP_GROUPS[parent]
            shares = [float(countries.get(t, {}).get("pop") or 0) for t in members]
            total_share = sum(shares) or 1.0
            idx = members.index(tag)
            pop = max(1000, int(round(pop * shares[idx] / total_share)))
        if pop:
            row["pop"] = str(pop)
            refreshed += 1
        if iso3 and wb:
            mva = wb_value(wb, iso3, "mva_usd")
            gdp = wb_value(wb, iso3, "gdp_usd")
            milex = wb_value(wb, iso3, "milex_usd")
            ind = wb_value(wb, iso3, "industry_usd")
            agr = wb_value(wb, iso3, "agriculture_usd")
            srv = wb_value(wb, iso3, "services_usd")
            if mva is not None and mva > 0:
                row["mva_b"] = f"{mva / 1e9:.3f}"
            if gdp is not None:
                row["gdp_b"] = f"{gdp / 1e9:.1f}"
            gdp_b = float(row.get("gdp_b") or 0)
            if ind is not None and ind > 0:
                row["ind_b"] = f"{ind / 1e9:.3f}"
            else:
                ind_pct = wb_value(wb, iso3, "industry_pct_gdp")
                if ind_pct is not None and ind_pct > 0 and gdp_b:
                    row["ind_b"] = f"{gdp_b * ind_pct / 100.0:.3f}"
            if agr is not None and agr > 0:
                row["agr_b"] = f"{agr / 1e9:.3f}"
            else:
                agr_pct = wb_value(wb, iso3, "agriculture_pct_gdp")
                if agr_pct is not None and agr_pct > 0 and gdp_b:
                    row["agr_b"] = f"{gdp_b * agr_pct / 100.0:.3f}"
            if srv is not None and srv > 0:
                row["srv_b"] = f"{srv / 1e9:.3f}"
            else:
                srv_pct = wb_value(wb, iso3, "services_pct_gdp")
                if srv_pct is not None and srv_pct > 0 and gdp_b:
                    row["srv_b"] = f"{gdp_b * srv_pct / 100.0:.3f}"
            if milex is not None:
                row["sipri_b"] = f"{milex / 1e9:.2f}"
        gdp_b = float(row.get("gdp_b") or 0)
        shares = GOODS_SHARE_FALLBACK.get(tag)
        if shares and gdp_b:
            if float(row.get("ind_b") or 0) <= 0:
                row["ind_b"] = f"{gdp_b * shares['ind']:.3f}"
            if float(row.get("agr_b") or 0) <= 0:
                row["agr_b"] = f"{gdp_b * shares['agr']:.3f}"
        irena_names = list(meta.get("irena") or []) + wpp_names
        mw = lookup_named(irena, irena_names)
        gw = (float(mw) / 1000.0) if mw else 0.0
        row["renewable_gw"] = f"{gw:.3f}"
        unctad_name = meta.get("unctad") or ""
        dwt = 0.0
        for n in [unctad_name, *wpp_names, *irena_names, meta.get("steel") or ""]:
            if n and n in dwt_map:
                dwt = float(dwt_map[n])
                break
        row["docks"] = str(docks_from_sources(tag, dwt))

    fieldnames = list(next(iter(countries.values())).keys()) if countries else []
    if "mva_b" in fieldnames:
        idx = fieldnames.index("mva_b") + 1
        for extra in ("ind_b", "agr_b", "srv_b"):
            if extra not in fieldnames:
                fieldnames.insert(idx, extra)
                idx += 1
    elif "ind_b" not in fieldnames:
        fieldnames.extend(["ind_b", "agr_b", "srv_b"])
    if "srv_b" not in fieldnames:
        fieldnames.append("srv_b")
    if "renewable_gw" not in fieldnames:
        fieldnames.append("renewable_gw")
    with COUNTRIES_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        seen = set()
        for tag, row in countries.items():
            if tag in seen:
                continue
            seen.add(tag)
            w.writerow(row)

    by_owner = group_by_owner(states)
    capitals = {}
    for tag, row in countries.items():
        cap = str(row.get("capital") or "").strip()
        if cap.isdigit():
            capitals[tag] = int(cap)

    finance_campus = load_campus_counts(DIB_FINANCE_PATH)
    refinery_campus = load_campus_counts(DIB_REFINERIES_PATH)
    silo_campus = load_campus_counts(DIB_SILOS_PATH)
    grid_campus = load_campus_counts(DIB_GRID_PATH)
    air_campus = load_campus_counts(DATA / "dib_air.json")
    aa_campus = load_campus_counts(DATA / "dib_aa.json")
    radar_campus = load_campus_counts(DATA / "dib_radar.json")
    naval_campus = load_campus_counts(DIB_NAVAL_PATH)
    ntl_by_iso3 = load_admin1_ntl().get("by_iso3") or {}

    mineral_country = {
        "oil": ei.get("oil_mbpd") or {},
        "coal": ei.get("coal_mt") or {},
        "steel": steel,
        **mineral_maps,
    }

    plan_rows = []
    gaz_rows = []

    for tag, owned in sorted(by_owner.items()):
        row = countries.get(tag) or {}
        target_pop = int(float(row.get("pop") or 0))
        if target_pop <= 0:
            target_pop = sum(max(s["manpower"], 1000) for s in owned) or 1000
        mva = float(row.get("mva_b") or 0)
        ind = float(row.get("ind_b") or 0)
        agr = float(row.get("agr_b") or 0)
        gdp = float(row.get("gdp_b") or 0)
        civs_total = factories_from_goods(goods_va_b(ind, agr, mva))
        mils_total = mils_from_dib(tag)
        docks_total = int(float(row.get("docks") or 0))
        parks_total = parks_from_gw(float(row.get("renewable_gw") or 0))
        finance_total = finance_campus.get(tag, 0)
        refinery_total = refinery_campus.get(tag, 0)
        silo_total = silo_campus.get(tag, 0)
        grid_total = grid_campus.get(tag, 0)
        air_total = air_campus.get(tag, 0)
        aa_total = aa_campus.get(tag, 0)
        radar_total = radar_campus.get(tag, 0)
        naval_total = naval_campus.get(tag, 0)
        srv_total = services_from_va(services_va_b(gdp, ind, agr, float(row.get("srv_b") or 0)))
        capital_id = capitals.get(tag)

        pop_w = []
        civ_w = []
        mil_w = []
        dock_w = []
        park_w = []
        air_w = []
        sources = []
        region_members: dict[str, list[int]] = defaultdict(list)
        region_pop: dict[str, float] = {}
        regions: list[tuple[str | None, float]] = []
        for i, s in enumerate(owned):
            key, pop = official_region(tag, s["loc_pretty"], s["pretty"])
            regions.append((key, pop))
            if key:
                region_members[key].append(i)
                region_pop[key] = pop
        for i, s in enumerate(owned):
            loc = s["loc_pretty"]
            key, _pop = regions[i]
            area = max(s["pixels"], 1.0) * DENSITY_BY_CAT.get(s["category"], 4)
            if key:
                members = region_members[key]
                areas = [
                    max(owned[j]["pixels"], 1.0) * DENSITY_BY_CAT.get(owned[j]["category"], 4)
                    for j in members
                ]
                share = area / (sum(areas) or 1.0)
                weight = region_pop[key] * share
                if ":man:" in (key or ""):
                    src = "manual/2026"
                elif ":wd:" in (key or "") or ":iso:" in (key or ""):
                    src = "wikidata/admin1"
                else:
                    src = "census/admin"
            else:
                weight = area
                src = "map-area*density"
            pop_w.append(weight)
            sources.append(src)
            civ_bonus = keyword_bonus(tag, loc, s["pretty"], CIV_KEYWORDS)
            mil_bonus = keyword_bonus(tag, loc, s["pretty"], MIL_KEYWORDS)
            dock_bonus = keyword_bonus(tag, loc, s["pretty"], DOCK_KEYWORDS)
            park_bonus = keyword_bonus(tag, loc, s["pretty"], RENEW_KEYWORDS)
            air_bonus = keyword_bonus(tag, loc, s["pretty"], AIR_KEYWORDS)
            civ_w.append(weight + 8_000_000 * civ_bonus)
            # Same 8e6 scale as civs: plant keywords must beat population smear.
            mil_w.append(0.05 * weight + 8_000_000 * mil_bonus)
            # HOI4 ignores dockyards in landlocked states (Great Lakes, rivers).
            if s["coastal"]:
                dock_w.append(max(0.0, 1.0 + 200.0 * dock_bonus + 5.0))
            else:
                dock_w.append(0.0)
            park_w.append(0.05 * weight + 80.0 * park_bonus)
            air_w.append(
                0.02 * weight
                + 8_000_000 * max(air_bonus, 0.0)
                + (500_000.0 if s["id"] == capital_id else 0.0)
            )

        def campus_weights(table: dict) -> list[float]:
            weights = [
                max(0.0, keyword_bonus(tag, s["loc_pretty"], s["pretty"], table))
                for s in owned
            ]
            if sum(weights) <= 0:
                weights = [1.0 if s["id"] == capital_id else 0.0 for s in owned]
            return weights

        finance_w = campus_weights(FINANCE_KEYWORDS)
        refinery_w = campus_weights(REFINERY_KEYWORDS)
        silo_w = campus_weights(SILO_KEYWORDS)
        grid_w = campus_weights(GRID_KEYWORDS)
        aa_w = campus_weights(AA_KEYWORDS)
        radar_w = campus_weights(RADAR_KEYWORDS)
        naval_w = []
        for s in owned:
            if not s.get("ports"):
                naval_w.append(0.0)
                continue
            naval_w.append(
                max(0.0, keyword_bonus(tag, s["loc_pretty"], s["pretty"], NAVAL_KEYWORDS))
            )
        if naval_total and sum(naval_w) <= 0:
            best_i = max(
                range(len(owned)),
                key=lambda i: (
                    max((owned[i].get("ports") or {}).values(), default=-1),
                    -owned[i]["id"],
                ),
            )
            naval_w = [
                1.0 if i == best_i and owned[i].get("ports") else 0.0
                for i in range(len(owned))
            ]
        if sum(air_w) <= 0:
            air_w = campus_weights(AIR_KEYWORDS)

        if len(owned) == 1 and sources[0] == "map-area*density":
            pop_w[0] = float(target_pop)
            sources[0] = "country-wpp2026"

        pops = distribute(target_pop, pop_w)
        pops = [max(1000, p) for p in pops]
        extra = sum(pops) - target_pop
        if extra > 0:
            for i in sorted(range(len(pops)), key=lambda j: pops[j], reverse=True):
                take = min(pops[i] - 1000, extra)
                if take <= 0:
                    continue
                pops[i] -= take
                extra -= take
                if extra <= 0:
                    break
        if docks_total > 0 and sum(dock_w) <= 0:
            raise SystemExit(f"{tag}: {docks_total} docks but no sea-coastal state")
        civ_d = cap_distribute(civs_total, civ_w, 40)
        mil_d = cap_distribute(mils_total, mil_w, 40)
        dock_d = cap_distribute(docks_total, dock_w, 40)
        park_d = cap_distribute(parks_total, park_w, 10)
        finance_d = cap_distribute(finance_total, finance_w, 20)
        refinery_d = cap_distribute(refinery_total, refinery_w, 3)
        silo_d = cap_distribute(silo_total, silo_w, 3)
        grid_d = cap_distribute(grid_total, grid_w, 1)
        air_d = cap_distribute(air_total, air_w, 10)
        aa_d = cap_distribute(aa_total, aa_w, 5)
        radar_d = cap_distribute(radar_total, radar_w, 6)
        if sum(naval_w) <= 0:
            naval_d = [0] * len(owned)
        else:
            naval_d = cap_distribute(naval_total, naval_w, 9)

        # Country resource totals
        meta = TAG_META.get(tag, {})
        names = list(meta.get("wpp") or []) + list(meta.get("irena") or [])
        ei_name = meta.get("ei") or (names[0] if names else "")
        steel_name = meta.get("steel") or ei_name
        res_totals: dict[str, int] = {}
        for key, cmap in mineral_country.items():
            raw = lookup_named(cmap, [ei_name, steel_name] + names) or 0
            res_totals[key] = int(round(float(raw) * RESOURCE_SCALE[key])) if raw else 0

        res_alloc: dict[str, list[int]] = {}
        for key, total in res_totals.items():
            bonuses = [
                keyword_bonus(tag, s["loc_pretty"], s["pretty"], RESOURCE_KEYWORDS[key])
                for s in owned
            ]
            if total and max(bonuses) > 0:
                weights = [1.0 + 100.0 * b for b in bonuses]
            else:
                weights = pop_w
            res_alloc[key] = distribute(total, weights)

        cats = [
            category_from_pop(pops[i], owned[i]["category"], owned[i]["impassable"])
            for i in range(len(owned))
        ]
        srv_w = []
        for i, s in enumerate(owned):
            if cats[i] in SERVICE_CATS or s["id"] == capital_id:
                srv_w.append(float(pops[i]))
            else:
                srv_w.append(0.0)
        if sum(srv_w) <= 0:
            srv_w = [float(p) for p in pops]
        srv_d = cap_distribute(srv_total, srv_w, 20)

        for i, s in enumerate(owned):
            pop = pops[i]
            cat = cats[i]
            is_cap = s["id"] == capital_id
            civs = civ_d[i]
            mils = mil_d[i]
            docks = dock_d[i]
            parks = park_d[i]
            extras = {
                "finance_center": finance_d[i],
                "services_building": srv_d[i],
                "renewable_park": parks,
                "synthetic_refinery": refinery_d[i],
                "fuel_silo": silo_d[i],
                "energy_infrastructure": grid_d[i],
            }
            ntl = ntl_mean_for(tag, s["loc_pretty"], s["pretty"], ntl_by_iso3)
            if ntl is None:
                infra = category_infra(cat, is_cap, s["impassable"])
            else:
                infra = ntl_to_infra(ntl)
                if s["impassable"]:
                    infra = min(infra, 2)
            slots = extra_slots(cat, civs, mils, docks, extras)
            rec = {
                "state_id": s["id"],
                "file": s["file"],
                "owner_2026": tag,
                "loc_name": s["loc_pretty"],
                "manpower": pop,
                "civs": civs,
                "mils": mils,
                "docks": docks,
                "infra": infra,
                "finance": extras["finance_center"],
                "services": extras["services_building"],
                "refinery": extras["synthetic_refinery"],
                "fuel_silo": extras["fuel_silo"],
                "energy_grid": extras["energy_infrastructure"],
                "renewable": parks,
                "air_base": air_d[i],
                "anti_air": aa_d[i],
                "radar": radar_d[i],
                "naval_primary": (1 + naval_d[i]) if s.get("ports") else 0,
                "extra_slots": slots,
                "category": cat,
                "pop_source": sources[i],
                "oil": res_alloc["oil"][i],
                "coal": res_alloc["coal"][i],
                "steel": res_alloc["steel"][i],
                "aluminium": res_alloc["aluminium"][i],
                "tungsten": res_alloc["tungsten"][i],
                "chromium": res_alloc["chromium"][i],
                "copper": res_alloc["copper"][i],
                "graphite": res_alloc["graphite"][i],
                "lithium": res_alloc["lithium"][i],
                "cobalt": res_alloc["cobalt"][i],
                "rare_earths": res_alloc["rare_earths"][i],
                "rubber": res_alloc["rubber"][i],
            }
            plan_rows.append(rec)
            gaz_rows.append(
                {
                    "state_id": s["id"],
                    "file": s["file"],
                    "owner": tag,
                    "loc_name": s["loc_pretty"],
                    "pretty_file": s["pretty"],
                    "pop_source": sources[i],
                    "official_weight": official_weight(tag, s["loc_pretty"], s["pretty"]),
                    "pixels": int(s["pixels"]),
                    "coastal": int(s["coastal"]),
                }
            )

    plan_rows.sort(key=lambda r: r["state_id"])
    gaz_rows.sort(key=lambda r: r["state_id"])
    write_csv(
        STATES_CSV,
        plan_rows,
        [
            "state_id", "file", "owner_2026", "loc_name", "manpower", "civs", "mils", "docks",
            "infra", "finance", "services", "refinery", "fuel_silo", "energy_grid", "renewable",
            "air_base", "anti_air", "radar", "naval_primary",
            "extra_slots", "category", "pop_source",
            "oil", "coal", "steel", "aluminium", "tungsten", "chromium", "copper", "graphite",
            "lithium", "cobalt", "rare_earths", "rubber",
        ],
    )
    write_csv(
        GAZETTEER_CSV,
        gaz_rows,
        ["state_id", "file", "owner", "loc_name", "pretty_file", "pop_source", "official_weight", "pixels", "coastal"],
    )
    world_pop = sum(r["manpower"] for r in plan_rows)
    world_civs = sum(r["civs"] for r in plan_rows)
    world_mils = sum(r["mils"] for r in plan_rows)
    world_docks = sum(r["docks"] for r in plan_rows)
    world_parks = sum(r["renewable"] for r in plan_rows)
    world_fin = sum(r["finance"] for r in plan_rows)
    world_srv = sum(r["services"] for r in plan_rows)
    world_ref = sum(r["refinery"] for r in plan_rows)
    world_silo = sum(r["fuel_silo"] for r in plan_rows)
    world_grid = sum(r["energy_grid"] for r in plan_rows)
    world_air = sum(r["air_base"] for r in plan_rows)
    world_aa = sum(r["anti_air"] for r in plan_rows)
    world_radar = sum(r["radar"] for r in plan_rows)
    world_naval_extra = sum(max(0, r["naval_primary"] - 1) for r in plan_rows)
    print("states", len(plan_rows), "country_rows_refreshed", refreshed)
    print("world manpower", world_pop, "civs", world_civs, "mils", world_mils, "docks", world_docks, "parks", world_parks)
    print("world finance", world_fin, "services", world_srv, "refinery", world_ref, "silos", world_silo, "grid", world_grid)
    print("world air", world_air, "aa", world_aa, "radar", world_radar, "naval_extra", world_naval_extra)
    for sid in (1, 16, 378, 375, 126, 613, 1030, 358, 261, 362, 629):
        rec = next((r for r in plan_rows if r["state_id"] == sid), None)
        if rec:
            print(
                f"  {sid} {rec['loc_name']}: pop={rec['manpower']} civs={rec['civs']} "
                f"mils={rec['mils']} docks={rec['docks']} parks={rec['renewable']} "
                f"infra={rec['infra']} fin={rec['finance']} srv={rec['services']} "
                f"ref={rec['refinery']} silo={rec['fuel_silo']} grid={rec['energy_grid']} "
                f"air={rec['air_base']} aa={rec['anti_air']} radar={rec['radar']} "
                f"nav={rec['naval_primary']} src={rec['pop_source']}"
            )


if __name__ == "__main__":
    main()
