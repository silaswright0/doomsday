"""Complete-design CW tanks. Empty NSB module_slots inherit hulls have no gun."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "common" / "units" / "equipment" / "doomsday_cw_chassis.txt"


def resources(year: int) -> str:
    lines = ["steel = 3", "tungsten = 1", "rare_earths = 1"]
    if year >= 2005:
        lines.append("copper = 1")
    if year >= 2015:
        lines.append("cobalt = 1")
    body = "\n".join(f"\t\t\t{ln}" for ln in lines)
    return f"\t\tresources = {{\n{body}\n\t\t}}"


def tank(
    name: str,
    *,
    year: int,
    archetype: str,
    parent: str,
    ic: float,
    speed: float,
    armor: int,
    soft: int,
    hard: int,
    ap: int,
    defence: int,
    brk: int,
    hardness: float,
    fuel: float,
    air: int = 0,
) -> str:
    bits = [
        f"\t{name} = {{",
        f"\t\tyear = {year}",
        f"\t\tarchetype = {archetype}",
        f"\t\tparent = {parent}",
        "\t\tpriority = 2000",
        f"\t\tbuild_cost_ic = {ic}",
        f"\t\tmaximum_speed = {speed}",
        f"\t\tarmor_value = {armor}",
        "\t\treliability = 0.95",
        f"\t\tdefense = {defence}",
        f"\t\tbreakthrough = {brk}",
        f"\t\thardness = {hardness}",
        f"\t\tsoft_attack = {soft}",
        f"\t\thard_attack = {hard}",
        f"\t\tap_attack = {ap}",
        f"\t\tair_attack = {air}",
        f"\t\tfuel_consumption = {fuel}",
        resources(year),
        "\t}",
        "",
    ]
    return "\n".join(bits)


def build() -> str:
    chunks = [
        "# Complete designs. No module_slots inherit — empty NSB hulls have no gun.\n",
        "equipments = {\n",
        "",
    ]
    mbts = [
        # T-54/M48 through optionally-manned MBT. AP vs armor: later ATGMs still threaten.
        ("mbt_equipment_1", 1955, "modern_tank_chassis_1", 22.0, 9.4, 98, 36, 28, 90, 12, 70, 0.95, 4.0, 0),
        ("mbt_equipment_2", 1965, "mbt_equipment_1", 26.0, 9.8, 106, 40, 34, 110, 13, 76, 0.96, 4.2, 0),
        ("mbt_equipment_3", 1973, "mbt_equipment_2", 28.0, 10.2, 114, 44, 40, 140, 14, 82, 0.97, 4.4, 0),
        ("mbt_equipment_4", 1980, "mbt_equipment_3", 34.0, 10.6, 122, 48, 48, 180, 16, 90, 0.98, 4.8, 0),
        ("mbt_equipment_5", 1992, "mbt_equipment_4", 40.0, 11.0, 130, 52, 54, 200, 18, 96, 0.98, 5.0, 0),
        ("mbt_equipment_6", 2005, "mbt_equipment_5", 46.0, 11.4, 138, 56, 58, 220, 20, 100, 0.98, 5.2, 4),
        ("mbt_equipment_7", 2015, "mbt_equipment_6", 54.0, 11.8, 146, 58, 62, 240, 24, 104, 0.98, 5.4, 8),
        ("mbt_equipment_8", 2026, "mbt_equipment_7", 62.0, 12.2, 154, 62, 68, 260, 26, 110, 0.98, 5.6, 12),
        ("mbt_equipment_9", 2035, "mbt_equipment_8", 68.0, 12.6, 162, 66, 72, 280, 28, 116, 0.98, 5.8, 16),
    ]
    for name, year, parent, ic, spd, armor, soft, hard, ap, df, brk, hardn, fuel, air in mbts:
        chunks.append(
            tank(
                name,
                year=year,
                archetype="modern_tank_chassis",
                parent=parent,
                ic=ic,
                speed=spd,
                armor=armor,
                soft=soft,
                hard=hard,
                ap=ap,
                defence=df,
                brk=brk,
                hardness=hardn,
                fuel=fuel,
                air=air,
            )
        )
    lights = [
        ("light_tank_equipment_cw1", 1955, "light_tank_chassis_3", 14.0, 12.4, 38, 22, 12, 50, 8, 28, 0.70, 2.4, 0),
        ("light_tank_equipment_cw2", 1968, "light_tank_equipment_cw1", 16.0, 12.8, 46, 24, 14, 60, 8, 32, 0.72, 2.6, 0),
        ("light_tank_equipment_cw3", 1981, "light_tank_equipment_cw2", 18.0, 13.2, 54, 26, 16, 75, 9, 36, 0.75, 2.8, 0),
        ("light_tank_equipment_cw4", 2002, "light_tank_equipment_cw3", 22.0, 13.6, 62, 30, 20, 90, 10, 40, 0.78, 3.0, 0),
        ("light_tank_equipment_cw5", 2016, "light_tank_equipment_cw4", 26.0, 14.0, 70, 32, 24, 110, 11, 44, 0.80, 3.2, 2),
        ("light_tank_equipment_cw6", 2024, "light_tank_equipment_cw5", 30.0, 14.4, 78, 36, 28, 130, 12, 48, 0.82, 3.4, 4),
        ("light_tank_equipment_cw7", 2034, "light_tank_equipment_cw6", 34.0, 14.8, 86, 38, 32, 150, 13, 52, 0.84, 3.6, 6),
    ]
    for name, year, parent, ic, spd, armor, soft, hard, ap, df, brk, hardn, fuel, air in lights:
        chunks.append(
            tank(
                name,
                year=year,
                archetype="light_tank_chassis",
                parent=parent,
                ic=ic,
                speed=spd,
                armor=armor,
                soft=soft,
                hard=hard,
                ap=ap,
                defence=df,
                brk=brk,
                hardness=hardn,
                fuel=fuel,
                air=air,
            )
        )
    chunks.append("}\n")
    return "".join(chunks)


def write() -> Path:
    OUT.write_text(build(), encoding="utf-8")
    return OUT


if __name__ == "__main__":
    print("wrote", write())
