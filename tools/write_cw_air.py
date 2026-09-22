"""Complete-design CW aircraft: combat stats, missions, correct BBA archetypes.

HOI4 wings key off archetype. Empty module_slots inherit hulls do not fight.
Do not run gen_modern_tech.py to refresh this file unless it imports write().
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "common" / "units" / "equipment" / "doomsday_cw_air.txt"

# BVR = air_superiority + interception. SEAD/IADS strike = attack_logistics (airfields, radar, supply).
FTR = "air_superiority\n\t\t\tinterception\n\t\t\tcas"
FTR_SEAD = "air_superiority\n\t\t\tinterception\n\t\t\tcas\n\t\t\tattack_logistics"
CAS = "cas\n\t\t\tnaval_bomber\n\t\t\tport_strike\n\t\t\tattack_logistics"
NAV = "naval_bomber\n\t\t\tport_strike\n\t\t\tnaval_patrol\n\t\t\tcas"
TAC = "cas\n\t\t\tstrategic_bomber\n\t\t\tnaval_bomber\n\t\t\tport_strike\n\t\t\tattack_logistics"
STR = "strategic_bomber\n\t\t\tnaval_bomber\n\t\t\tport_strike\n\t\t\tattack_logistics"
SCT = "recon"
MPA = "naval_patrol\n\t\t\tnaval_bomber\n\t\t\tport_strike\n\t\t\trecon"


def resources(year: int, extra: str = "") -> str:
    lines = ["aluminium = 3", "rubber = 1", "rare_earths = 1"]
    if year >= 1981:
        lines.append("cobalt = 1")
    if year >= 2005:
        lines.append("copper = 1")
    if extra:
        lines.append(extra)
    body = "\n".join(f"\t\t\t{ln}" for ln in lines)
    return f"\t\tresources = {{\n{body}\n\t\t}}"


def plane(
    name: str,
    *,
    year: int,
    archetype: str,
    parent: str,
    missions: str,
    rng: int,
    speed: int,
    agi: int,
    defence: int,
    ic: float,
    superiority: float,
    air_attack: int = 0,
    ground: int = 0,
    bombing: int = 0,
    naval: float = 0,
    ntarget: float = 0,
    surface: int = 0,
    sub: int = 0,
    fuel: float = 0.26,
    manpower: int = 20,
    priority: int = 6,
    carrier: bool = False,
    extra: str = "",
) -> str:
    bits = [
        f"\t{name} = {{",
        f"\t\tyear = {year}",
        f"\t\tarchetype = {archetype}",
        f"\t\tparent = {parent}",
        f"\t\tpriority = {priority}",
    ]
    if carrier:
        bits.append("\t\tcarrier_capable = yes")
    bits += [
        "\t\tallow_mission_type = {",
        f"\t\t\t{missions}",
        "\t\t}",
        f"\t\tair_range = {rng}",
        f"\t\tmaximum_speed = {speed}",
        f"\t\tair_agility = {agi}",
        f"\t\tair_defence = {defence}",
        f"\t\tair_attack = {air_attack}",
        f"\t\tair_ground_attack = {ground}",
        f"\t\tair_bombing = {bombing}",
        f"\t\tnaval_strike_attack = {naval}",
        f"\t\tnaval_strike_targetting = {ntarget}",
        f"\t\tsurface_detection = {surface}",
        f"\t\tsub_detection = {sub}",
        f"\t\tair_superiority = {superiority}",
        "\t\tweight = 5",
        f"\t\tbuild_cost_ic = {ic}",
        f"\t\tmanpower = {manpower}",
        f"\t\tfuel_consumption = {fuel}",
        resources(year),
    ]
    if extra:
        bits.append(extra)
    bits.append("\t}")
    return "\n".join(bits) + "\n"


def simple(
    name: str,
    *,
    year: int,
    archetype: str,
    parent: str,
    rng: int,
    speed: int,
    agi: int,
    defence: int,
    ic: float,
    air_attack: int = 0,
    ground: int = 0,
    surface: int = 0,
    sub: int = 0,
    fuel: float | None = None,
    extra: str = "",
) -> str:
    bits = [
        f"\t{name} = {{",
        f"\t\tyear = {year}",
        f"\t\tarchetype = {archetype}",
        f"\t\tparent = {parent}",
        f"\t\tpriority = 90",
        f"\t\tair_range = {rng}",
        f"\t\tmaximum_speed = {speed}",
        f"\t\tair_agility = {agi}",
        f"\t\tair_defence = {defence}",
        f"\t\tair_attack = {air_attack}",
        f"\t\tbuild_cost_ic = {ic}",
    ]
    if ground:
        bits.append(f"\t\tair_ground_attack = {ground}")
    if surface:
        bits.append(f"\t\tsurface_detection = {surface}")
    if sub:
        bits.append(f"\t\tsub_detection = {sub}")
    if fuel is not None:
        bits.append(f"\t\tfuel_consumption = {fuel}")
    if extra:
        bits.append(extra)
    bits.append("\t}")
    return "\n".join(bits) + "\n"


def build() -> str:
    chunks: list[str] = [
        "# Complete designs. No module_slots inherit — empty BBA hulls do not fight.\n",
        "# Later fighter gens buy attack/defence (BVR + stealth stand-in), not WW2 agility.\n",
        "equipments = {\n",
    ]

    fighters = [
        # name, year, parent, rng, spd, agi, def, ic, sup, atk, naval, ntg, surf, fuel, missions
        ("fighter_equipment_cw1", 1953, "fighter_equipment_3", 800, 950, 48, 16, 24.0, 1.0, 28, 1, 8, 12, 0.21, FTR),
        ("fighter_equipment_cw2", 1960, "fighter_equipment_cw1", 1200, 1800, 50, 22, 28.0, 1.15, 40, 2, 8, 16, 0.24, FTR),
        ("fighter_equipment_cw3", 1970, "fighter_equipment_cw2", 1600, 2200, 52, 28, 34.0, 1.3, 52, 3, 9, 22, 0.26, FTR),
        ("fighter_equipment_cw4", 1981, "fighter_equipment_cw3", 2200, 2450, 65, 48, 44.0, 1.6, 75, 6, 10, 32, 0.28, FTR_SEAD),
        ("fighter_equipment_cw45", 1994, "fighter_equipment_cw4", 2400, 2500, 70, 58, 52.0, 1.8, 85, 8, 11, 40, 0.28, FTR_SEAD),
        ("fighter_equipment_cw5a", 2005, "fighter_equipment_cw45", 2800, 2450, 78, 85, 88.0, 2.2, 105, 10, 12, 48, 0.30, FTR_SEAD),
        ("fighter_equipment_cw5b", 2016, "fighter_equipment_cw45", 3000, 2000, 75, 92, 72.0, 2.4, 112, 12, 12, 52, 0.28, FTR_SEAD),
        ("fighter_equipment_cw6", 2030, "fighter_equipment_cw5a", 3400, 2550, 80, 95, 110.0, 2.6, 120, 14, 13, 60, 0.32, FTR_SEAD),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, nav, ntg, surf, fuel, missions in fighters:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="small_plane_airframe",
                parent=parent,
                missions=missions,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=max(2, surf // 8),
                fuel=fuel,
            )
        )

    cv = [
        ("cv_fighter_equipment_cw2", 1960, "cv_fighter_equipment_3", 900, 1600, 52, 20, 30.0, 1.15, 38, 4, 10, 18, 0.24, FTR),
        ("cv_fighter_equipment_cw4", 1983, "cv_fighter_equipment_cw2", 1400, 2200, 68, 44, 46.0, 1.5, 72, 10, 12, 30, 0.28, FTR_SEAD),
        ("cv_fighter_equipment_cw5", 2018, "cv_fighter_equipment_cw4", 1800, 1950, 76, 88, 78.0, 2.0, 108, 14, 13, 48, 0.28, FTR_SEAD),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, nav, ntg, surf, fuel, missions in cv:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="cv_small_plane_airframe",
                parent=parent,
                missions=missions,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=max(3, surf // 6),
                fuel=fuel,
                carrier=True,
            )
        )

    cas = [
        ("cas_equipment_cw1", 1960, "CAS_equipment_3", 900, 1100, 32, 18, 22.0, 0.2, 6, 22, 0, 8, 8, 16, 0.26),
        ("cas_equipment_cw2", 1977, "cas_equipment_cw1", 1000, 1200, 35, 26, 32.0, 0.3, 8, 32, 0, 12, 10, 20, 0.28),
        ("cas_equipment_cw3", 1991, "cas_equipment_cw2", 1200, 1300, 38, 32, 40.0, 0.35, 10, 42, 2, 14, 12, 24, 0.28),
        ("cas_equipment_cw4", 2010, "cas_equipment_cw3", 1400, 1400, 42, 40, 48.0, 0.4, 14, 55, 4, 16, 14, 28, 0.30),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, gnd, bomb, nav, ntg, surf, fuel in cas:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="small_plane_cas_airframe",
                parent=parent,
                missions=CAS,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                ground=gnd,
                bombing=bomb,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=4,
                fuel=fuel,
            )
        )

    navb = [
        ("nav_bomber_equipment_cw1", 1960, "nav_bomber_equipment_3", 1600, 900, 25, 16, 28.0, 0.15, 8, 6, 4, 32, 12, 28, 14, 0.28),
        ("nav_bomber_equipment_cw2", 1982, "nav_bomber_equipment_cw1", 2200, 980, 28, 22, 40.0, 0.2, 10, 8, 6, 45, 14, 40, 20, 0.30),
        ("nav_bomber_equipment_cw3", 2008, "nav_bomber_equipment_cw2", 2800, 1050, 30, 30, 52.0, 0.25, 12, 10, 8, 62, 16, 52, 26, 0.32),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, gnd, bomb, nav, ntg, surf, sub, fuel in navb:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="small_plane_naval_bomber_airframe",
                parent=parent,
                missions=NAV,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                ground=gnd,
                bombing=bomb,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=sub,
                fuel=fuel,
            )
        )

    tac = [
        ("tac_bomber_equipment_cw1", 1960, "tac_bomber_equipment_3", 2800, 950, 22, 22, 36.0, 0.2, 8, 14, 28, 12, 8, 24, 0.40),
        ("tac_bomber_equipment_cw2", 1974, "tac_bomber_equipment_cw1", 3200, 1100, 24, 28, 48.0, 0.3, 10, 20, 38, 16, 9, 28, 0.44),
        ("tac_bomber_equipment_cw3", 1990, "tac_bomber_equipment_cw2", 3800, 1200, 28, 36, 56.0, 0.4, 14, 28, 52, 20, 10, 34, 0.46),
        ("tac_bomber_equipment_cw4", 2026, "tac_bomber_equipment_cw3", 4600, 1300, 32, 50, 40.0, 0.5, 18, 38, 68, 24, 12, 42, 0.42),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, gnd, bomb, nav, ntg, surf, fuel in tac:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="medium_plane_airframe",
                parent=parent,
                missions=TAC,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                ground=gnd,
                bombing=bomb,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=6,
                fuel=fuel,
                manpower=40,
            )
        )

    # Strat: range is the payload. Stealth is defence, not guns. B-21 (cw5) beats B-2 (cw4).
    strat = [
        ("strat_bomber_equipment_cw1", 1955, "strat_bomber_equipment_3", 6000, 900, 8, 22, 80.0, 0.05, 4, 48, 8, 6, 12, 0.90),
        ("strat_bomber_equipment_cw2", 1974, "strat_bomber_equipment_cw1", 7000, 1000, 10, 28, 100.0, 0.08, 5, 62, 14, 8, 14, 1.00),
        ("strat_bomber_equipment_cw3", 1986, "strat_bomber_equipment_cw2", 7500, 1100, 12, 34, 120.0, 0.1, 6, 78, 20, 10, 16, 1.10),
        ("strat_bomber_equipment_cw4", 1997, "strat_bomber_equipment_cw3", 8000, 950, 14, 55, 200.0, 0.12, 8, 95, 18, 8, 18, 1.00),
        ("strat_bomber_equipment_cw5", 2023, "strat_bomber_equipment_cw4", 8500, 1000, 16, 70, 175.0, 0.15, 10, 115, 22, 10, 22, 0.95),
        ("strat_bomber_equipment_cw6", 2036, "strat_bomber_equipment_cw5", 9000, 1100, 18, 80, 140.0, 0.18, 12, 135, 26, 12, 26, 0.90),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, bomb, nav, ntg, surf, fuel in strat:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="large_plane_airframe",
                parent=parent,
                missions=STR,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                bombing=bomb,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=3,
                fuel=fuel,
                manpower=80,
            )
        )

    chunks.append(
        plane(
            "scout_plane_equipment_cw1",
            year=1960,
            archetype="medium_plane_scout_plane_airframe",
            parent="scout_plane_equipment_2",
            missions=SCT,
            rng=2800,
            speed=900,
            agi=35,
            defence=16,
            ic=40.0,
            superiority=0,
            surface=55,
            sub=12,
            fuel=0.26,
            manpower=40,
        )
    )

    aew = [
        ("aew_equipment_1", 1977, "scout_plane_equipment_2", 3500, 700, 18, 20, 70.0, 80, 22),
        ("aew_equipment_2", 2012, "aew_equipment_1", 5000, 750, 20, 28, 80.0, 140, 32),
        ("aew_equipment_3", 2032, "aew_equipment_2", 5800, 800, 22, 34, 50.0, 180, 40),
    ]
    prev_parent = "scout_plane_equipment_2"
    for name, year, parent, rng, spd, agi, df, ic, surf, sub in aew:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="medium_plane_scout_plane_airframe",
                parent=parent if parent else prev_parent,
                missions=SCT,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=0.05,
                surface=surf,
                sub=sub,
                fuel=0.55,
                manpower=60,
            )
        )
        prev_parent = name

    mpa = [
        ("mpa_equipment_cw1", 1962, 4000, 550, 12, 18, 60.0, 8, 10, 28, 14, 40, 28, 0.70),
        ("mpa_equipment_cw2", 1985, 5500, 600, 14, 24, 72.0, 10, 12, 38, 16, 55, 40, 0.75),
        ("mpa_equipment_cw3", 2013, 7000, 650, 16, 30, 90.0, 12, 14, 48, 18, 70, 52, 0.80),
    ]
    parent = "large_plane_airframe_4"
    for i, (name, year, rng, spd, agi, df, ic, atk, gnd, nav, ntg, surf, sub, fuel) in enumerate(mpa):
        chunks.append(
            plane(
                name,
                year=year,
                archetype="large_plane_maritime_patrol_plane_airframe",
                parent=parent,
                missions=MPA,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=0.05,
                air_attack=atk,
                ground=gnd,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=sub,
                fuel=fuel,
                manpower=80,
            )
        )
        parent = name

    cca = [
        ("cca_equipment_1", 2026, "fighter_equipment_cw45", 1800, 2200, 82, 42, 32.0, 1.4, 70, 8, 10, 30, 0.18),
        ("cca_equipment_2", 2034, "cca_equipment_1", 2000, 2400, 88, 50, 18.0, 1.6, 82, 10, 11, 36, 0.16),
    ]
    for name, year, parent, rng, spd, agi, df, ic, sup, atk, nav, ntg, surf, fuel in cca:
        chunks.append(
            plane(
                name,
                year=year,
                archetype="small_plane_airframe",
                parent=parent,
                missions=FTR_SEAD,
                rng=rng,
                speed=spd,
                agi=agi,
                defence=df,
                ic=ic,
                superiority=sup,
                air_attack=atk,
                naval=nav,
                ntarget=ntg,
                surface=surf,
                sub=4,
                fuel=fuel,
                manpower=0,
            )
        )

    chunks.append(
        plane(
            "cca_strike_equipment_1",
            year=2028,
            archetype="small_plane_cas_airframe",
            parent="CAS_equipment_3",
            missions=CAS,
            rng=1600,
            speed=1800,
            agi=55,
            defence=36,
            ic=32.0,
            superiority=0.4,
            air_attack=12,
            ground=48,
            bombing=8,
            naval=14,
            ntarget=12,
            surface=24,
            fuel=0.18,
            manpower=0,
        )
    )

    chunks.append(
        plane(
            "hale_uav_equipment_1",
            year=1998,
            archetype="recon_uav_equipment",
            parent="recon_uav_equipment_1",
            missions=SCT,
            rng=8000,
            speed=600,
            agi=28,
            defence=12,
            ic=36.0,
            superiority=0,
            surface=75,
            sub=10,
            fuel=0.06,
            manpower=5,
        )
    )

    chunks.append(
        simple(
            "recon_uav_equipment_2",
            year=2015,
            archetype="recon_uav_equipment",
            parent="recon_uav_equipment_1",
            rng=600,
            speed=180,
            agi=40,
            defence=6,
            ic=8.0,
            surface=28,
            sub=6,
            fuel=0.02,
        )
    )
    chunks.append(
        simple(
            "transport_heli_equipment_2",
            year=1975,
            archetype="transport_heli_equipment",
            parent="transport_heli_equipment_1",
            rng=700,
            speed=280,
            agi=28,
            defence=16,
            ic=22.0,
            fuel=0.35,
        )
    )
    chunks.append(
        simple(
            "transport_heli_equipment_3",
            year=2030,
            archetype="transport_heli_equipment",
            parent="transport_heli_equipment_2",
            rng=900,
            speed=320,
            agi=32,
            defence=20,
            ic=48.0,
            fuel=0.40,
        )
    )
    chunks.append(
        simple(
            "guided_missile_equipment_cw",
            year=2009,
            archetype="guided_missile_equipment",
            parent="guided_missile_equipment_4",
            rng=2500,
            speed=880,
            agi=12,
            defence=18,
            ic=48.0,
            extra="\t\tair_bombing = 720",
        )
    )
    chunks.append("}\n")
    return "".join(chunks)


EQUIPMENT_NAMES = [
    "fighter_equipment_cw1",
    "fighter_equipment_cw2",
    "fighter_equipment_cw3",
    "fighter_equipment_cw4",
    "fighter_equipment_cw45",
    "fighter_equipment_cw5a",
    "fighter_equipment_cw5b",
    "fighter_equipment_cw6",
    "cv_fighter_equipment_cw2",
    "cv_fighter_equipment_cw4",
    "cv_fighter_equipment_cw5",
    "cas_equipment_cw1",
    "cas_equipment_cw2",
    "cas_equipment_cw3",
    "cas_equipment_cw4",
    "nav_bomber_equipment_cw1",
    "nav_bomber_equipment_cw2",
    "nav_bomber_equipment_cw3",
    "tac_bomber_equipment_cw1",
    "tac_bomber_equipment_cw2",
    "tac_bomber_equipment_cw3",
    "tac_bomber_equipment_cw4",
    "strat_bomber_equipment_cw1",
    "strat_bomber_equipment_cw2",
    "strat_bomber_equipment_cw3",
    "strat_bomber_equipment_cw4",
    "strat_bomber_equipment_cw5",
    "strat_bomber_equipment_cw6",
    "scout_plane_equipment_cw1",
    "aew_equipment_1",
    "aew_equipment_2",
    "aew_equipment_3",
    "mpa_equipment_cw1",
    "mpa_equipment_cw2",
    "mpa_equipment_cw3",
    "cca_equipment_1",
    "cca_equipment_2",
    "cca_strike_equipment_1",
    "hale_uav_equipment_1",
    "recon_uav_equipment_2",
    "transport_heli_equipment_2",
    "transport_heli_equipment_3",
    "guided_missile_equipment_cw",
]


def write() -> Path:
    OUT.write_text(build(), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    path = write()
    print("wrote", path)
