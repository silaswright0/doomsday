"""Set 2026 equipment resource costs from what the weapon is actually made of.

Costs are per factory, so they stay small integers. Chromium stands in for nickel
and stainless. Microchips are only on digital fire control, seekers, and combat
systems. Uranium is only on warheads; reactor cores are the nuclear-engine module.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "common" / "units" / "equipment" / "zz_doomsday_cw_land.txt",
    ROOT / "common" / "units" / "equipment" / "zz_doomsday_cw_air.txt",
    ROOT / "common" / "units" / "equipment" / "zz_doomsday_cw_chassis.txt",
    ROOT / "common" / "units" / "equipment" / "zz_doomsday_cw_hulls.txt",
    ROOT / "common" / "units" / "equipment" / "nuclear_missiles.txt",
    ROOT / "common" / "units" / "equipment" / "ballistic_missiles.txt",
    ROOT / "common" / "units" / "equipment" / "hypersonic_missiles.txt",
    ROOT / "common" / "units" / "equipment" / "sam_missile.txt",
    ROOT / "common" / "units" / "equipment" / "doomsday_uav.txt",
]
ORDER = (
    "aluminium", "rubber", "tungsten", "steel", "chromium", "titanium",
    "rare_earths", "lithium", "cobalt", "copper", "graphite", "uranium", "microchips",
)


def num(name: str) -> int:
    match = re.search(r"(\d+)[a-z]?$", name)
    return int(match.group(1)) if match else 1


def pack(*pairs: tuple[str, int]) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in pairs:
        if value:
            out[key] = out.get(key, 0) + value
    return out


def recipe(name: str) -> dict[str, int] | None:
    n = num(name)
    if name.startswith("infantry_equipment_cw"):
        # Rifles and small arms. Copper is the sight and radio, not a chip line.
        return pack(("steel", 2), ("copper", 1 if n >= 4 else 0))
    if name.startswith("motorized_equipment_"):
        return pack(("steel", 1), ("rubber", 1), ("copper", 1 if n >= 4 else 0))
    if name.startswith("mechanized_equipment_"):
        return pack(
            ("steel", 3), ("rubber", 1), ("chromium", 1),
            ("copper", 1 if n >= 5 else 0),
            ("rare_earths", 1 if n >= 6 else 0),
        )
    if name.startswith("support_equipment_cw"):
        return pack(("steel", 1), ("aluminium", 1), ("copper", 1 if n >= 3 else 0))
    if name.startswith("artillery_equipment_cw"):
        return pack(("steel", 2), ("tungsten", 1), ("copper", 1 if n >= 3 else 0))
    if name.startswith("rocket_artillery_equipment_cw"):
        return pack(("steel", 1), ("tungsten", 1), ("aluminium", 1), ("copper", 1 if n >= 3 else 0))
    if name.startswith("anti_tank_equipment_cw"):
        return pack(("steel", 2), ("tungsten", 2), ("copper", 1 if n >= 3 else 0))
    if name.startswith("anti_air_equipment_cw"):
        return pack(("steel", 2))
    if name.startswith("manpads_equipment"):
        return pack(
            ("steel", 1), ("aluminium", 1), ("rare_earths", 1),
            ("microchips", 1 if n >= 3 else 0),
        )
    if name.startswith("spg_equipment"):
        return pack(("steel", 2), ("tungsten", 1), ("rubber", 1), ("copper", 1 if n >= 5 else 0))
    if name.startswith("dew_equipment"):
        return pack(("rare_earths", 2), ("copper", 1), ("chromium", 1), ("microchips", 1))
    if name.startswith("prsm_equipment") or name.startswith("mrc_equipment") or name.startswith("hypersonic_glcm"):
        return pack(("aluminium", 2), ("rare_earths", 1), ("copper", 1), ("microchips", 1), ("graphite", 1))
    if name.startswith("shorad_equipment"):
        return pack(("steel", 2), ("rare_earths", 1), ("copper", 1), ("microchips", 1 if n >= 3 else 0))
    if name.startswith("hpm_equipment"):
        return pack(("rare_earths", 2), ("copper", 1), ("microchips", 1))
    if name.startswith("mortar_equipment_"):
        return pack(("steel", 1), ("copper", 1 if n >= 3 else 0))
    if name.startswith("td_equipment_"):
        return pack(("steel", 3), ("tungsten", 2), ("chromium", 1), ("copper", 1 if n >= 4 else 0))
    if name.startswith("spaa_equipment_"):
        return pack(("steel", 2), ("rare_earths", 1), ("copper", 1), ("microchips", 1 if n >= 4 else 0))
    if name.startswith("ifpc_equipment") or name.startswith("bmd_equipment"):
        return pack(("steel", 2), ("aluminium", 1), ("rare_earths", 1), ("copper", 1), ("microchips", 1))
    if name.startswith("sam_equipment_"):
        return pack(
            ("aluminium", 1), ("steel", 1), ("rare_earths", 1), ("copper", 1),
            ("microchips", 1 if n >= 3 else 0),
        )
    if name.startswith("infantry_at_equipment_"):
        return pack(("steel", 1), ("tungsten", 1), ("rare_earths", 1 if n >= 5 else 0))
    if name.startswith("attack_heli_equipment_"):
        return pack(
            ("aluminium", 2), ("steel", 1), ("rare_earths", 1),
            ("microchips", 1 if n >= 3 else 0),
            ("cobalt", 1 if n >= 3 else 0),
        )
    if "fighter_equipment_cw" in name:
        if re.search(r"cw45|cw5|cw6", name):
            # Titanium structure, carbon skin, AESA, single-crystal turbine.
            return pack(
                ("aluminium", 2), ("titanium", 2), ("graphite", 1), ("rare_earths", 1),
                ("copper", 1), ("microchips", 1), ("cobalt", 1),
            )
        if "cw4" in name:
            return pack(("aluminium", 3), ("titanium", 1), ("rubber", 1), ("rare_earths", 1), ("copper", 1))
        if "cw3" in name:
            return pack(("aluminium", 3), ("titanium", 1), ("rubber", 1), ("chromium", 1))
        return pack(("aluminium", 3), ("rubber", 1), ("chromium", 1))
    if name.startswith("cas_equipment_cw"):
        base = pack(("aluminium", 2), ("steel", 1), ("rubber", 1))
        if n >= 3:
            base["titanium"] = 1
        if n >= 4:
            base.update(copper=1, rare_earths=1, microchips=1)
        return base
    if name.startswith("nav_bomber_equipment_cw") or name.startswith("tac_bomber_equipment_cw"):
        base = pack(("aluminium", 3), ("rubber", 1))
        if n >= 3:
            base.update(titanium=1, copper=1)
        if n >= 4:
            base.update(rare_earths=1, microchips=1)
        return base
    if name.startswith("strat_bomber_equipment_cw"):
        if n >= 4:
            return pack(
                ("aluminium", 3), ("titanium", 1), ("rubber", 1), ("rare_earths", 1),
                ("copper", 1), ("microchips", 1), ("graphite", 1),
            )
        return pack(("aluminium", 3), ("rubber", 1), ("steel", 1))
    if name.startswith("scout_plane_equipment_cw"):
        return pack(("aluminium", 2), ("rare_earths", 1), ("copper", 1))
    if name.startswith("aew_equipment_") or name.startswith("mpa_equipment_cw"):
        return pack(("aluminium", 2), ("rare_earths", 1), ("copper", 1), ("microchips", 1))
    if name.startswith("cca_") or name.startswith("hale_uav") or name.startswith("recon_uav_equipment"):
        base = pack(("aluminium", 1), ("lithium", 1), ("graphite", 1), ("rare_earths", 1), ("microchips", 1))
        if "strike" in name:
            base["cobalt"] = 1
        return base
    if name.startswith("transport_heli_equipment"):
        return pack(("aluminium", 2), ("steel", 1))
    if name.startswith("loitering_munition_equipment"):
        return pack(("aluminium", 1), ("rare_earths", 1), ("graphite", 1), ("microchips", 1), ("lithium", 1))
    if name.startswith("guided_missile_equipment"):
        return pack(("aluminium", 2), ("tungsten", 1), ("rare_earths", 1), ("copper", 1), ("microchips", 1), ("graphite", 1))
        return pack(("aluminium", 2), ("tungsten", 1), ("rare_earths", 1), ("copper", 1), ("microchips", 1), ("graphite", 1))
    if name.startswith("mbt_equipment_"):
        base = pack(("steel", 3), ("tungsten", 1), ("chromium", 1))
        if n >= 5:
            base.update(copper=1, rare_earths=1)
        if n >= 7:
            base.update(microchips=1, titanium=1)
        return base
    if name.startswith("light_tank_equipment_cw"):
        base = pack(("steel", 2), ("tungsten", 1))
        if n >= 5:
            base.update(copper=1, chromium=1)
        return base
    if name.startswith("ship_hull_light_cw"):
        base = pack(("steel", 2), ("chromium", 1))
        if n >= 4:
            base["copper"] = 1
        if n >= 6:
            base.update(rare_earths=1, microchips=1, titanium=1)
        return base
    if name.startswith("ship_hull_cruiser_cw"):
        base = pack(("steel", 3), ("chromium", 1))
        if n >= 3:
            base.update(copper=1, rare_earths=1, microchips=1, titanium=1)
        return base
    if name.startswith("ship_hull_carrier_cw"):
        base = pack(("steel", 3), ("chromium", 1), ("aluminium", 1))
        if n >= 4:
            base.update(copper=1, microchips=1)
        return base
    if name.startswith("ship_hull_submarine_cw") or name.startswith("ship_hull_submarine_diesel"):
        base = pack(("steel", 2), ("chromium", 1), ("titanium", 1))
        if n >= 4 or "diesel" in name:
            base.update(copper=1, microchips=1, rare_earths=1)
        return base
    if name.startswith("ship_hull_ssbn_"):
        # Reactor core is the required nuclear-engine module, not a second hull cost.
        base = pack(("steel", 2), ("chromium", 1), ("titanium", 1), ("copper", 1))
        if n >= 3:
            base.update(microchips=1, rare_earths=1)
        return base
    if name.startswith("ship_hull_amphib_"):
        return pack(("steel", 2), ("chromium", 1), ("aluminium", 1), ("copper", 1 if n >= 3 else 0))
    if name.startswith("ship_hull_usv_") or name.startswith("ship_hull_uuv_"):
        return pack(("steel", 1), ("copper", 1), ("microchips", 1), ("lithium", 1))
    if name.startswith("nuclear_missile_equipment"):
        # The warhead. Level 2 is the thermonuclear body.
        return pack(
            ("aluminium", 2 if n < 2 else 3),
            ("tungsten", 1),
            ("rare_earths", 1),
            ("copper", 1),
            ("microchips", 1),
            ("graphite", 1),
            ("uranium", 1 if n < 2 else 2),
        )
    if name.startswith("ballistic_missile_equipment"):
        return pack(
            ("aluminium", 2), ("tungsten", 1), ("rare_earths", 1),
            ("copper", 1), ("microchips", 1 if n >= 2 else 0), ("graphite", 1 if n >= 3 else 0),
        )
    if name.startswith("hypersonic_missile_equipment"):
        return pack(("aluminium", 2), ("tungsten", 1), ("rare_earths", 1), ("cobalt", 1), ("copper", 1), ("microchips", 1), ("graphite", 1))
    if name.startswith("sam_missile_equipment"):
        return pack(("aluminium", 1), ("tungsten", 1), ("rare_earths", 1), ("copper", 1), ("microchips", 1 if n >= 2 else 0))
    if "uav_equipment" in name:
        base = pack(("aluminium", 1), ("lithium", 1), ("graphite", 1), ("rare_earths", 1), ("microchips", 1), ("copper", 1))
        if "strike" in name:
            base["cobalt"] = 1
        return base
    return None


def format_block(cost: dict[str, int]) -> str:
    lines = ["\t\tresources = {"]
    for key in ORDER:
        if cost.get(key):
            lines.append(f"\t\t\t{key} = {cost[key]}")
    lines.append("\t\t}")
    return "\n".join(lines)


def equipment_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    spans = []
    depth = 0
    current = None
    start = None
    for idx, line in enumerate(lines):
        code = line.split("#", 1)[0]
        if depth == 1 and current is None:
            match = re.match(r"\t([A-Za-z0-9_]+) = \{", line)
            if match and "{" in code:
                current = match.group(1)
                start = idx
        depth += code.count("{") - code.count("}")
        if current is not None and depth == 1:
            spans.append((current, start, idx))
            current = None
    return spans


def apply_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    spans = equipment_spans(lines)
    missed = []
    # Replace from the bottom so indexes stay valid.
    for name, start, end in reversed(spans):
        cost = recipe(name)
        if cost is None:
            missed.append(name)
            continue
        block = lines[start : end + 1]
        body = "\n".join(block)
        formatted = format_block(cost)
        updated, count = re.subn(r"\t\tresources = \{[^{}]*\}", formatted, body, count=1)
        if count == 0:
            updated = body[: body.rfind("\n\t}")] + "\n" + formatted + "\n\t}"
        lines[start : end + 1] = updated.split("\n")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return missed


def main() -> None:
    missed: list[str] = []
    for path in FILES:
        missed.extend(f"{path.name}: {name}" for name in apply_file(path))
    if missed:
        print("no recipe:")
        for row in missed:
            print(" ", row)
    else:
        print("every equipment block has a recipe")


if __name__ == "__main__":
    main()
