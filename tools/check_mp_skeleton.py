"""Sanity checks for the MP-safe modern warfare skeleton."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)


def check_replace_paths() -> None:
    needed = {
        'replace_path="common/technologies"',
        'replace_path="common/units"',
        'replace_path="common/units/equipment"',
        'replace_path="common/idea_tags"',
        'replace_path="events"',
        'replace_path="common/on_actions"',
        'replace_path="common/national_focus"',
        'replace_path="common/decisions"',
        'replace_path="common/decisions/categories"',
        'replace_path="common/ai_strategy_plans"',
        'replace_path="common/ai_strategy"',
        'replace_path="common/ai_templates"',
        'replace_path="common/military_industrial_organization"',
        'replace_path="common/military_industrial_organization/organizations"',
        'replace_path="common/military_industrial_organization/policies"',
        'replace_path="history/general"',
    }
    for path in (ROOT / "descriptor.mod", ROOT.parent / "doomsday.mod"):
        text = path.read_text(encoding="utf-8")
        missing = [line for line in needed if line not in text]
        if missing:
            fail(f"{path.name} missing {missing}")


def check_identical_tech() -> None:
    blocks = []
    for path in sorted((ROOT / "history" / "countries").glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"set_technology = \{.*?\n\}", text, re.S)
        if not match:
            fail(f"{path.name} has no set_technology block")
            continue
        blocks.append((path.name, match.group(0)))
    if not blocks:
        fail("no country history files")
        return
    first = blocks[0][1]
    for name, block in blocks[1:]:
        if block != first:
            fail(f"{name} TECH_BLOCK differs from {blocks[0][0]}")
            break
    for needed in (
        "improved_infantry_weapons = 1",
        "main_battle_tank = 1",
        "jet_fighter1 = 1",
        "dd_recon_uav = 1",
        "dd_manpads = 1",
        "dd_shorad = 1",
    ):
        if needed not in first:
            fail(f"TECH_BLOCK missing Cold War floor {needed}")
    for too_modern in (
        "advanced_infantry_weapons2 = 1",
        "modern_small_airframe = 1",
        "dd_strike_uav = 1",
        "dd_cruise_missile = 1",
        "dd_srbm = 1",
        "dd_sam = 1",
    ):
        if too_modern in first:
            fail(f"TECH_BLOCK starts too modern ({too_modern})")


def check_no_random() -> None:
    files = [
        ROOT / "common" / "scripted_effects" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_effects" / "doomsday_market.txt",
        ROOT / "common" / "scripted_guis" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_localisation" / "doomsday_economy.txt",
        ROOT / "common" / "on_actions" / "doomsday_economy.txt",
        ROOT / "common" / "ideas" / "doomsday_policies.txt",
        ROOT / "common" / "decisions" / "doomsday_economy.txt",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        stripped = re.sub(r"#.*", "", text)
        if re.search(r"\brandom(?:_list|_select_amount)?\b", stripped):
            fail(f"non-deterministic token in {path.name}")


def check_buildings() -> None:
    text = (ROOT / "common" / "buildings" / "00_buildings.txt").read_text(encoding="utf-8")
    for name in ("finance_center", "services_building", "renewable_park", "sam_site"):
        if f"{name} = {{" not in text:
            fail(f"missing building {name}")
    civ = re.search(r"industrial_complex = \{.*?base_cost = (\d+)", text, re.S)
    fin = re.search(r"finance_center = \{.*?base_cost = (\d+)", text, re.S)
    ren = re.search(r"renewable_park = \{.*?base_cost = (\d+)", text, re.S)
    srv = re.search(r"services_building = \{.*?base_cost = (\d+)", text, re.S)
    if not all((civ, fin, ren, srv)):
        fail("could not read building costs")
        return
    costs = [int(civ.group(1)), int(fin.group(1)), int(ren.group(1)), int(srv.group(1))]
    if costs != sorted(costs, reverse=True):
        fail(f"build cost order should be civ>finance>renewable>services, got {costs}")
    if "energy_gain_factor" not in text:
        fail("renewable_park missing energy_gain_factor")
    spawn_section = text.split("spawn_points")[-1] if "spawn_points" in text else ""
    if "dd_" in spawn_section or "sam_site_spawn" in spawn_section:
        fail("new spawn type added; v1 must reuse rocket_site_spawn")
    if re.search(r"sam_site = \{.*?spawn_point = rocket_site_spawn", text, re.S):
        fail("SAM site should not steal rocket_site_spawn from launch sites")
    sam = re.search(r"sam_site = \{.*?level_cap = \{.*?\}", text, re.S)
    if not sam or "rocket_launch_capacity" not in sam.group(0):
        fail("sam_site needs rocket_launch_capacity so SAM missions can intercept")
    if sam and re.search(r"anti_air\s*=\s*yes", sam.group(0)):
        fail("sam_site must not grant free gun AA; intercepts require SAM equipment")
    if sam and not re.search(r"need_supply\s*=\s*yes", sam.group(0)):
        fail("sam_site must be provincial and need_supply to fire")
    if sam and not re.search(r"province_max", sam.group(0)):
        fail("sam_site must be provincial (province_max)")
    if sam and not re.search(r"state_max", sam.group(0)):
        fail("sam_site needs state_max so the construction UI is not 1/0")
    if sam and re.search(r"spawn_point\s*=", sam.group(0)):
        fail("sam_site must not declare a spawn_point")
    leftover = []
    for path in (ROOT / "history" / "states").glob("*.txt"):
        hist = path.read_text(encoding="utf-8", errors="ignore")
        bm = re.search(r"\bbuildings\s*=", hist)
        if not bm:
            continue
        i = hist.find("{", bm.start())
        depth = 0
        block = ""
        for j in range(i, len(hist)):
            if hist[j] == "{":
                depth += 1
            elif hist[j] == "}":
                depth -= 1
                if depth == 0:
                    block = hist[i : j + 1]
                    break
        for m in re.finditer(r"(?m)^[ \t]*sam_site\s*=", block):
            if block[: m.start()].count("{") - block[: m.start()].count("}") == 1:
                leftover.append(path.name)
                break
        if len(leftover) >= 5:
            break
    if leftover:
        fail(f"sam_site still state-level in {leftover[:5]}")
    sam_eq = (ROOT / "common" / "units" / "equipment" / "sam_missile.txt").read_text(encoding="utf-8")
    if "sam_mission" not in sam_eq:
        fail("SAM equipment must allow sam_mission")
    if "one_use_only" not in sam_eq:
        fail("SAM equipment must be one_use_only so sites spend missiles to fire")
    if "barrage_mission" in sam_eq.split("allow_mission_type")[1].split("forbid_mission_type")[0]:
        fail("SAM equipment must not allow barrage_mission")
    for name in ("ballistic_missiles.txt", "guided_missiles.txt", "nuclear_missiles.txt"):
        eq = (ROOT / "common" / "units" / "equipment" / name).read_text(encoding="utf-8")
        allowed = eq.split("allow_mission_type")[1].split("forbid_mission_type")[0]
        if "sam_mission" in allowed:
            fail(f"{name} must not allow sam_mission")
        if "forbid_mission_type" not in eq or "sam_mission" not in eq.split("forbid_mission_type")[1][:200]:
            fail(f"{name} must forbid sam_mission")
    air = (ROOT / "common" / "units" / "air.txt").read_text(encoding="utf-8")
    if "sam_missile = {" not in air:
        fail("missing sam_missile air unit")
    else:
        sam_chunk = air.split("sam_missile = {", 1)[1].split("mothership", 1)[0]
        if "sam_missile_equipment" not in sam_chunk:
            fail("SAM wings must need sam_missile_equipment to fire")
        if "carrier_air_wing_size" in sam_chunk or "submarine_carrier_air_wing_size" in sam_chunk:
            fail("SAM wings must not launch from carriers or missile subs")
    rocket = re.search(r"rocket_site = \{.*?level_cap = \{.*?\}", text, re.S)
    if rocket and re.search(r"shares_slots = yes", rocket.group(0)):
        fail("rocket_site is underground and must not share factory slots")
    if rocket and re.search(r"disable_grow_animation", rocket.group(0)):
        fail("rocket_site disable_grow_animation draws extra V2 meshes")
    if rocket and not re.search(r"show_on_map\s*=\s*1", rocket.group(0)):
        fail("rocket_site must be 1 map pad per constructed silo")
    aa = (ROOT / "common" / "units" / "doomsday_aa.txt").read_text(encoding="utf-8")
    if "mobile_sam" not in aa:
        fail("missing mobile_sam battalion")
    elif "sam_missile_equipment" not in aa:
        fail("mobile SAM must need sam_missile_equipment as ammo")
    tech = (ROOT / "common" / "technologies" / "doomsday_techs.txt").read_text(encoding="utf-8")
    sam = re.search(r"dd_sam = \{.*?ai_will_do", tech, re.S)
    if not sam or "mobile_sam" not in sam.group(0):
        fail("dd_sam must enable mobile_sam")
    if sam and re.search(r"enable_building", sam.group(0)):
        fail("dd_sam must not gate static SAM; starting techs already place batteries")
    shorad = re.search(r"dd_shorad = \{.*?ai_will_do", tech, re.S)
    if not shorad or "sam_site" not in shorad.group(0):
        fail("dd_shorad (starting) must enable sam_site so history batteries are not 1/0")


def check_research_costs() -> None:
    text = (ROOT / "common" / "technologies" / "doomsday_techs.txt").read_text(encoding="utf-8")
    costs = re.findall(r"research_cost = ([0-9.]+)", text)
    if len(costs) < 8:
        fail("expected doomsday techs to declare research_cost")


def check_politics_slots() -> None:
    tags = (ROOT / "common" / "idea_tags" / "00_idea.txt").read_text(encoding="utf-8")
    gov = re.search(r"government = \{[^}]*\}", tags, re.S)
    if not gov:
        fail("could not read government idea category")
    elif "dd_welfare_laws" in gov.group(0) or "character_slot = political_advisor" in gov.group(0):
        fail("government row should not hold budget policies or cabinet")
    elif gov.group(0).count("slot =") != 6:
        fail("government row needs 6 law slots")
    elif not all(
        key in gov.group(0)
        for key in (
            "mobilization_laws",
            "trade_laws",
            "economy",
            "dd_religion_laws",
            "dd_media_laws",
            "dd_civil_military_laws",
        )
    ):
        fail("government row should be conscription/trade/economy plus religion/media/civil-military")
    pol = re.search(r"dd_policies = \{[^}]*\}", tags, re.S)
    if not pol:
        fail("missing dd_policies idea category")
    elif pol.group(0).count("slot = dd_") != 6:
        fail("policies row needs 6 policy law slots")
    pol2 = re.search(r"dd_policies_2 = \{[^}]*\}", tags, re.S)
    if not pol2:
        fail("missing dd_policies_2 idea category")
    elif pol2.group(0).count("slot = dd_") != 6:
        fail("second policies row needs 6 policy law slots")
    gui = (ROOT / "interface" / "doomsday_market.gui").read_text(encoding="utf-8")
    sg = (ROOT / "common" / "scripted_guis" / "doomsday_economy.txt").read_text(encoding="utf-8")
    start = gui.find('name = "dd_arms_market_window"')
    if start < 0:
        fail("missing dd_arms_market_window")
    else:
        brace = gui.find("{", start)
        depth = 0
        end = brace
        for i, ch in enumerate(gui[brace:], brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if "dd_market_list_" in gui[start:end]:
            fail("market land/air/navy lists must be independent windows, not nested")
    for cat in ("land", "air", "navy"):
        if f'window_name = "dd_market_list_{cat}"' not in sg:
            fail(f"missing dd_market_list_{cat} scripted GUI")
        if f"dd_market_list_{cat}_ui" not in sg or "parent_window_name = dd_arms_market_window" not in sg:
            fail(f"dd_market_list_{cat} must attach to the market window")
    prod = re.search(r"research_production = \{.*?military_staff", tags, re.S)
    if not prod:
        fail("could not read research_production idea category")
    else:
        if prod.group(0).count("character_slot = political_advisor") != 6:
            fail("cabinet row needs 6 political_advisor slots")
        if "tank_manufacturer" in prod.group(0):
            fail("cabinet row still has designer slots")
    policies = (ROOT / "common" / "ideas" / "doomsday_policies.txt").read_text(encoding="utf-8")
    if policies.count("law = yes") < 15:
        fail("policy ideas must be laws, not national spirits")
    if "country = {" in policies:
        fail("policies should not live in the country/spirit bucket")


def check_energy_define() -> None:
    text = (ROOT / "common" / "defines" / "doomsday_defines.lua").read_text(encoding="utf-8")
    if 'ENERGY_RESOURCE = "coal"' not in text:
        fail("ENERGY_RESOURCE must stay coal")


def main() -> int:
    check_replace_paths()
    check_identical_tech()
    check_no_random()
    check_buildings()
    check_research_costs()
    check_politics_slots()
    check_energy_define()
    if ERRORS:
        print("FAIL")
        for err in ERRORS:
            print(" -", err)
        return 1
    print("OK: identical TECH_BLOCK, no random in money/policy, spawn types unchanged, cost order civ>finance>renewable>services")
    print("MP gate still needs a host+2 clients 3-month observe: treasuries, policy ideas, and market stockpiles must match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
