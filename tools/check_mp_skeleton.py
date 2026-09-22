"""Sanity checks for the MP-safe modern warfare skeleton."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []

# Off-map utility tags (intel insurgent pool). Skip start-setup floor checks.
DORMANT_TAGS = {"IG1", "IG2", "IG3", "IG4"}


def fail(msg: str) -> None:
    ERRORS.append(msg)


def history_tag(path: Path) -> str:
    return path.name.split(" ")[0].strip()


def check_replace_paths() -> None:
    needed = {
        'replace_path="common/technologies"',
        'replace_path="common/units"',
        'replace_path="common/units/equipment"',
        'replace_path="common/idea_tags"',
        'replace_path="common/ideologies"',
        'replace_path="common/characters"',
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
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        missing = [line for line in needed if line not in text]
        if missing:
            fail(f"{path.name} missing {missing}")


def check_identical_tech() -> None:
    from start_setup import MUST_NOT_START, extra_techs

    floor_need = (
        "improved_infantry_weapons = 1",
        "main_battle_tank = 1",
        "jet_fighter1 = 1",
        "dd_inf_1 = 1",
        "dd_mbt_1 = 1",
        "dd_manpad_1 = 1",
        "dd_shorad_1 = 1",
        "dd_ftr_2 = 1",
        "dd_uav_3 = 1",
        "dd_slot_1 = 1",
        "dd_vls_1 = 1",
    )
    too_modern = tuple(f"{t} = 1" for t in sorted(MUST_NOT_START))
    for path in sorted((ROOT / "history" / "countries").glob("*.txt")):
        tag = history_tag(path)
        if tag in DORMANT_TAGS:
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(r"set_technology = \{.*?\n\}", text, re.S)
        if not match:
            fail(f"{path.name} has no set_technology block")
            continue
        block = match.group(0)
        for needed in floor_need:
            if needed not in block:
                fail(f"{path.name} missing Cold War floor {needed}")
                break
        for bad in too_modern:
            if bad in block:
                fail(f"{path.name} starts too modern ({bad})")
                break
        granted = set(re.findall(r"^\t([A-Za-z0-9_]+) = 1", block, re.M))
        extra = set(extra_techs(tag))
        missing = extra - granted
        if missing:
            fail(f"{path.name} missing extra techs {sorted(list(missing))[:6]}")


def check_start_setup() -> None:
    john = 0
    bad_pop = 0
    bad_slots = 0
    missing_john = 0
    for path in (ROOT / "history" / "countries").glob("*.txt"):
        if history_tag(path) in DORMANT_TAGS:
            continue
        text = path.read_text(encoding="utf-8")
        if "set_stability = 0.90" not in text or "set_war_support = 0.70" not in text:
            fail(f"{path.name} missing 90/70 stab/ws")
            break
        if "_john_army" not in text:
            missing_john += 1
        m = re.search(r"set_popularities = \{(.*?)\}", text, re.S)
        if m:
            vals = [int(x) for x in re.findall(r"=\s*(\d+)", m.group(1))]
            if sum(vals) != 100:
                bad_pop += 1
        sm = re.search(r"set_research_slots = (\d+)", text)
        if not sm or not (1 <= int(sm.group(1)) <= 5):
            bad_slots += 1
        if "last_election" not in text:
            fail(f"{path.name} missing last_election")
            break
    if missing_john:
        fail(f"{missing_john} country files missing John Army")
    if bad_pop:
        fail(f"{bad_pop} popularity pies do not sum to 100")
    if bad_slots:
        fail(f"{bad_slots} research slots outside 1-5")
    staff = list((ROOT / "common" / "characters").glob("doomsday_staff_*.txt"))
    if not staff:
        fail("missing generated staff characters")
    for path in staff:
        txt = path.read_text(encoding="utf-8")
        if re.search(r"\brandom\b", re.sub(r"#.*", "", txt)):
            fail(f"random in {path.name}")
    basing = ROOT / "common" / "on_actions" / "doomsday_basing.txt"
    if not basing.exists():
        fail("missing doomsday_basing.txt")
    else:
        btxt = basing.read_text(encoding="utf-8")
        if "dd_basing_init" not in btxt or "give_military_access" not in btxt:
            fail("basing on_action incomplete")
        if re.search(r"\brandom\b", re.sub(r"#.*", "", btxt)):
            fail("random in doomsday_basing.txt")
    usa = (ROOT / "history" / "units" / "USA_2026.txt")
    usa_text = usa.read_text(encoding="utf-8") if usa.exists() else ""
    if not usa_text or "location =" not in usa_text:
        fail("USA_2026 OOB missing located divisions")
    if not (ROOT / "localisation" / "replace" / "doomsday_country_names_l_english.yml").exists():
        fail("missing country name loc")
    if 'replace_path="common/characters"' not in (ROOT / "descriptor.mod").read_text(encoding="utf-8"):
        fail("descriptor must replace_path common/characters")
    usa_hist = next((ROOT / "history" / "countries").glob("USA*.txt"), None)
    if usa_hist:
        ut = usa_hist.read_text(encoding="utf-8")
        if "set_research_slots = 5" not in ut:
            fail("USA should have 5 research slots")
        if "dd_inf_6 = 1" not in ut:
            fail("USA missing tier-3 extra tech")
        head = ut.split('oob =', 1)[0]
        if "give_military_access = USA" not in head:
            fail("USA military access must be granted before the OOB loads")
        stock = [int(x) for x in re.findall(r"add_equipment_to_stockpile = \{ type = infantry_equipment_\w+ amount = (\d+)", ut)]
        land_divs = usa_text.count("\tdivision = {")
        if stock and land_divs and stock[0] >= land_divs * 900:
            fail("USA surplus infantry looks like a full deployed army")
    dpk = next((ROOT / "history" / "countries").glob("DPK*.txt"), None)
    if dpk:
        dt = dpk.read_text(encoding="utf-8")
        m = re.search(r"set_variable = \{ debt = ([0-9.]+) \}", dt)
        if not m or float(m.group(1)) <= 0:
            fail("DPK debt should be a positive override, not zero")
    sng = next((ROOT / "history" / "countries").glob("SNG*.txt"), None)
    if sng:
        st = sng.read_text(encoding="utf-8")
        tm = re.search(r"set_variable = \{ treasury = ([0-9.]+) \}", st)
        dm = re.search(r"set_variable = \{ debt = ([0-9.]+) \}", st)
        if not dm or float(dm.group(1)) <= 0:
            fail("SNG debt should be positive")
        if not tm or float(tm.group(1)) < 10:
            fail("SNG treasury should reflect SWF-scale reserves")
    if basing.exists():
        btxt = basing.read_text(encoding="utf-8")
        for host, guest in (("JAP", "USA"), ("KOR", "USA"), ("QAT", "USA"), ("DJI", "CHI"), ("BLR", "SOV")):
            blob = f"{host} = {{\n					give_military_access = {guest}"
            if blob not in btxt:
                fail(f"missing {host}->{guest} basing access")
    ham = ROOT / "history" / "units" / "HAM_2026.txt"
    if ham.exists() and "Militia Brigade" not in ham.read_text(encoding="utf-8"):
        fail("HAM OOB should be militia-heavy")
    empty = ROOT / "history" / "units" / "DOOMSDAY_EMPTY.txt"
    if not empty.exists():
        fail("missing DOOMSDAY_EMPTY OOB")


def check_no_random() -> None:
    files = [
        ROOT / "common" / "scripted_effects" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_effects" / "doomsday_market.txt",
        ROOT / "common" / "scripted_effects" / "doomsday_mercs.txt",
        ROOT / "common" / "scripted_triggers" / "doomsday_mercs.txt",
        ROOT / "common" / "scripted_effects" / "doomsday_intel.txt",
        ROOT / "common" / "scripted_guis" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_localisation" / "doomsday_economy.txt",
        ROOT / "common" / "on_actions" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_triggers" / "doomsday_policies.txt",
        ROOT / "common" / "scripted_triggers" / "doomsday_intel.txt",
        ROOT / "common" / "on_actions" / "doomsday_resource_rights.txt",
        ROOT / "common" / "on_actions" / "doomsday_basing.txt",
        ROOT / "events" / "doomsday_events.txt",
        ROOT / "common" / "ideas" / "doomsday_policies.txt",
        ROOT / "common" / "ideas" / "doomsday_intel.txt",
        ROOT / "common" / "decisions" / "doomsday_economy.txt",
        ROOT / "common" / "decisions" / "doomsday_intel.txt",
        ROOT / "common" / "dynamic_modifiers" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_localisation" / "doomsday_economy.txt",
        ROOT / "common" / "scripted_localisation" / "doomsday_mercs_intel.txt",
    ]
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        stripped = re.sub(r"#.*", "", text)
        if re.search(r"\brandom(?:_list|_select_amount)?\b", stripped):
            fail(f"non-deterministic token in {path.name}")


def check_buildings() -> None:
    text = (ROOT / "common" / "buildings" / "00_buildings.txt").read_text(encoding="utf-8")
    for name in ("finance_center", "services_building", "renewable_park"):
        if f"{name} = {{" not in text:
            fail(f"missing building {name}")
    if re.search(r"(?m)^\s*sam_site\s*=\s*\{", text):
        fail("sam_site building must be removed; SAM is interceptor aircraft")
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
    leftover = []
    empty_states = []
    for path in (ROOT / "history" / "states").glob("*.txt"):
        hist = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(?m)^\s*sam_site\s*=", hist):
            leftover.append(path.name)
            if len(leftover) >= 5:
                break
        # provinces must be a state key, not a history effect. Missing
        # buildings } (Trieste one-liner SAM strip) crashes InitGameState.
        hm = re.search(r"\bhistory\s*=", hist)
        pm = re.search(r"\bprovinces\s*=", hist)
        if hm and pm and hist[hm.start():pm.start()].count("{") - hist[hm.start():pm.start()].count("}") > 0:
            empty_states.append(path.name)
        elif not pm or not re.search(r"\bprovinces\s*=\s*\{[^}]*\d+", hist):
            empty_states.append(path.name)
    if leftover:
        fail(f"sam_site still in history {leftover[:5]}")
    if empty_states:
        fail(f"state file missing provinces block {empty_states[:5]}")
    bmap = (ROOT / "map" / "buildings.txt").read_text(encoding="utf-8", errors="ignore")
    if ";sam_site;" in bmap:
        fail("sam_site rows still in map/buildings.txt")
    sam_eq = (ROOT / "common" / "units" / "equipment" / "sam_missile.txt").read_text(encoding="utf-8")
    if "type = interceptor" not in sam_eq:
        fail("SAM equipment must be interceptor aircraft on airbases")
    if "interception" not in sam_eq.split("allow_mission_type")[1].split("forbid_mission_type")[0]:
        fail("SAM equipment must allow interception")
    if "one_use_only" not in sam_eq:
        fail("SAM equipment must be one_use_only so intercepts spend missiles")
    if "barrage_mission" in sam_eq.split("allow_mission_type")[1].split("forbid_mission_type")[0]:
        fail("SAM equipment must not allow barrage_mission")
    strike_types = {
        "ballistic_missiles.txt": "ballistic_missile",
        "guided_missiles.txt": "missile",
        "nuclear_missiles.txt": "nuclear_missile",
        "hypersonic_missiles.txt": "ballistic_missile",
    }
    for name, expected in strike_types.items():
        eq = (ROOT / "common" / "units" / "equipment" / name).read_text(encoding="utf-8")
        if f"type = {expected}" not in eq:
            fail(f"{name} must stay type = {expected} so it launches from rocket sites")
        if "type = fighter" in eq or "type = interceptor" in eq:
            fail(f"{name} must not fly from airbases")
        allowed = eq.split("allow_mission_type")[1].split("forbid_mission_type")[0]
        if "sam_mission" in allowed:
            fail(f"{name} must not allow sam_mission")
        if "forbid_mission_type" not in eq or "sam_mission" not in eq.split("forbid_mission_type")[1][:200]:
            fail(f"{name} must forbid sam_mission")
    air = (ROOT / "common" / "units" / "air.txt").read_text(encoding="utf-8")
    if "sam_missile = {" not in air:
        fail("missing sam_missile air unit")
    else:
        sam_chunk = air.split("sam_missile = {", 1)[1].split("hypersonic_missile", 1)[0]
        if "sam_missile_equipment" not in sam_chunk:
            fail("SAM wings must need sam_missile_equipment to fire")
        if "type = interceptor" not in sam_chunk:
            fail("SAM air unit must be interceptor")
        if "carrier_air_wing_size" in sam_chunk or "submarine_carrier_air_wing_size" in sam_chunk:
            fail("SAM wings must not launch from carriers or missile subs")
    if "hypersonic_missile = {" not in air:
        fail("missing hypersonic_missile air unit")
    else:
        hyp = air.split("hypersonic_missile = {", 1)[1].split("mothership", 1)[0]
        if "type = ballistic_missile" not in hyp:
            fail("hypersonic wings must be ballistic_missile so they use rocket sites")
    rocket = re.search(r"rocket_site = \{.*?level_cap = \{.*?\}", text, re.S)
    if rocket and re.search(r"shares_slots = yes", rocket.group(0)):
        fail("rocket_site is underground and must not share factory slots")
    if rocket and re.search(r"disable_grow_animation", rocket.group(0)):
        fail("rocket_site disable_grow_animation draws extra V2 meshes")
    if rocket and not re.search(r"show_on_map\s*=\s*0", rocket.group(0)):
        fail("rocket_site show_on_map plus spawn_point draws two V2 pads")
    if rocket and not re.search(r"spawn_point\s*=\s*rocket_site_spawn", rocket.group(0)):
        fail("rocket_site must keep rocket_site_spawn")
    aa = (ROOT / "common" / "units" / "doomsday_aa.txt").read_text(encoding="utf-8")
    if "mobile_sam" not in aa:
        fail("missing mobile_sam battalion")
    elif "sam_missile_equipment" not in aa:
        fail("mobile SAM must need sam_missile_equipment as ammo")
    tech_dir = ROOT / "common" / "technologies"
    arty = (tech_dir / "dd_artillery.txt").read_text(encoding="utf-8") if (tech_dir / "dd_artillery.txt").exists() else ""
    air_dd = (tech_dir / "dd_air.txt").read_text(encoding="utf-8") if (tech_dir / "dd_air.txt").exists() else ""
    sam = re.search(r"dd_sam_1 = \{.*?ai_will_do", arty, re.S)
    if not sam or "mobile_sam" not in sam.group(0):
        fail("dd_sam_1 must enable mobile_sam")
    if sam and re.search(r"enable_building", sam.group(0)):
        fail("dd_sam_1 must not enable a SAM building")
    shorad = re.search(r"dd_shorad_1 = \{.*?ai_will_do", arty, re.S)
    if shorad and "sam_site" in shorad.group(0):
        fail("dd_shorad_1 must not enable sam_site")
    if "hypersonic_missile_equipment_1" not in air_dd and "hypersonic_glcm_equipment_1" not in arty:
        fail("missile trees must enable hypersonic missiles")
    cw_air = (ROOT / "common" / "units" / "equipment" / "doomsday_cw_air.txt").read_text(encoding="utf-8")
    if "module_slots = inherit" in cw_air:
        fail("CW air complete designs must not inherit empty BBA module slots")
    ftr3 = re.search(r"fighter_equipment_cw3 = \{.*?^\t\}", cw_air, re.S | re.M)
    if not ftr3 or "air_attack =" not in ftr3.group(0) or re.search(r"air_attack = 0\b", ftr3.group(0)):
        fail("CW fighters need air_attack so they can fight without weapon modules")
    cas1 = re.search(r"cas_equipment_cw1 = \{.*?^\t\}", cw_air, re.S | re.M)
    if not cas1 or "small_plane_cas_airframe" not in cas1.group(0):
        fail("CAS must use small_plane_cas_airframe")
    if "nav_bomber_equipment_cw1" not in cw_air or "mpa_equipment_cw1" not in cw_air:
        fail("missing naval bomber / MPA complete designs")
    aew1 = re.search(r"aew_equipment_1 = \{.*?^\t\}", cw_air, re.S | re.M)
    if not aew1 or "medium_plane_scout_plane_airframe" not in aew1.group(0) or "surface_detection" not in aew1.group(0):
        fail("AEW must be scout-archetype with detection")
    if "recon_uav =" not in air or "strike_uav =" not in air or "transport_helicopter =" not in air:
        fail("missing UAV / transport helicopter air subunits")
    manpads = re.search(r"manpads = \{.*?^\t\}", aa, re.S | re.M)
    if manpads and re.search(r"air_attack = -", manpads.group(0)):
        fail("MANPADS battalion air_attack must not be negative")
    if re.search(r"naval_strike_attack = (?!0)\d", sam_eq.split("sam_missile_equipment =", 1)[-1][:800]):
        fail("SAM interceptors must not have naval strike")
    units_dir = ROOT / "history" / "units"
    usa_oob = (units_dir / "USA_2026.txt").read_text(encoding="utf-8") if (units_dir / "USA_2026.txt").exists() else ""
    if "helicopter_equipment" in usa_oob.split("air_wings", 1)[-1]:
        fail("air wings must not spawn land attack helicopters")
    if "fighter_equipment_cw5a" not in usa_oob:
        fail("USA 2026 OOB should start with 5th-gen fighters")
    air_blocks = re.findall(r"air_wings = \{.*?\n\}", usa_oob, re.S)
    for block in air_blocks:
        states = re.findall(r"^\t(\d+) = \{", block, re.M)
        if len(states) != len(set(states)):
            fail("USA air_wings has duplicate state keys")


def check_modern_trees() -> None:
    land = (ROOT / "common" / "units" / "equipment" / "doomsday_cw_land.txt").read_text(encoding="utf-8")
    if "infantry_equipment_cw1" not in land:
        fail("generated land equipment missing infantry_equipment_cw1")
    if "manpads_equipment =" not in land:
        fail("generated land equipment missing manpads archetype")
    inf = ROOT / "common" / "technologies" / "dd_infantry.txt"
    if not inf.exists() or "dd_inf_2" not in inf.read_text(encoding="utf-8"):
        fail("missing generated infantry tree")
    ind = (ROOT / "common" / "technologies" / "dd_industry.txt").read_text(encoding="utf-8")
    if "mined_resource_factor" in ind:
        fail("industry tree uses invalid mined_resource_factor")
    if "dd_slot_3" not in ind:
        fail("missing dd_slot building-capacity techs")
    if "XOR" not in ind:
        fail("concentrated/dispersed must XOR")
    air = (ROOT / "common" / "technologies" / "dd_air.txt").read_text(encoding="utf-8")
    nav = (ROOT / "common" / "technologies" / "dd_naval.txt").read_text(encoding="utf-8")
    if air.count("dd_cv_2 =") and nav.count("dd_cv_2 ="):
        fail("dd_cv_2 collides between air and naval trees")
    if "dd_cvf_2" not in air:
        fail("carrier-fighter branch must use dd_cvf_* ids")
    if "air_dew_pod_1" in air:
        fail("air DEW must be a fighter/CAS modifier, not air_dew_pod_1")
    if "attack_logistics" not in (ROOT / "common" / "units" / "equipment" / "doomsday_cw_air.txt").read_text(
        encoding="utf-8"
    ):
        fail("BVR/SEAD fighters must have attack_logistics")
    cw_air = (ROOT / "common" / "units" / "equipment" / "doomsday_cw_air.txt").read_text(encoding="utf-8")
    if "air_dew_pod_1" in cw_air or "tanker" in cw_air:
        fail("air file still has DEW airframe or tanker equipment")
    chassis = (ROOT / "common" / "units" / "equipment" / "doomsday_cw_chassis.txt").read_text(encoding="utf-8")
    if "module_slots = inherit" in chassis:
        fail("CW tanks must be complete designs, not empty NSB hulls")
    if "soft_attack" not in chassis or "mbt_equipment_4" not in chassis:
        fail("MBTs missing complete combat stats")
    if "ap_attack = 200" not in land:
        fail("Javelin-era infantry AT needs ap_attack")
    mods = (ROOT / "common" / "units" / "equipment" / "modules" / "doomsday_ship_modules.txt").read_text(
        encoding="utf-8"
    )
    if "ship_vls_1" not in mods or "lg_attack" not in mods:
        fail("VLS modules need strike (lg_attack) as well as AA")
    if "intel_from_operatives_factor" in (ROOT / "common" / "technologies" / "dd_electronics.txt").read_text(
        encoding="utf-8"
    ):
        fail("electronics tree must not use LaR-only intel_from_operatives_factor")
    hist = next((ROOT / "history" / "countries").glob("*.txt")).read_text(encoding="utf-8")
    if "dd_inf_1 = 1" not in hist:
        fail("country history missing modern floor techs")


def check_research_costs() -> None:
    texts = []
    for path in sorted((ROOT / "common" / "technologies").glob("dd_*.txt")):
        texts.append(path.read_text(encoding="utf-8"))
    text = "\n".join(texts)
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
    for slot in (
        "welfare", "education", "immigration", "taxes", "women", "minority",
        "investment", "security", "healthcare", "labor", "fertility",
        "aid", "religion", "media", "civil_military",
    ):
        for n in range(1, 6):
            token = f"dd_{slot}_{n} ="
            if token not in policies:
                fail(f"missing five-tier policy {token.strip()}")
    fx = (ROOT / "common" / "scripted_effects" / "doomsday_economy.txt").read_text(encoding="utf-8")
    if "dd_sync_fertility_to_women" not in fx:
        fail("women's rights must floor fertility laws")
    if "add_to_variable = { dd_admin_factor = 0.64 }" not in fx:
        fail("extreme policy cost band 0.64 missing")
    ideologies = (ROOT / "common" / "ideologies" / "00_ideologies.txt").read_text(encoding="utf-8")
    for token in (
        "social_democracy", "social_liberalism", "liberal_conservatism",
        "progressive_populism", "national_populism", "sovereign_democracy",
        "military_junta", "absolute_monarchy", "state_socialism",
        "left_wing_nationalism", "islamic_democracy", "theocratic_absolutism",
        "jihadist_fundamentalism", "democratic_confederalism", "fascism",
        "communism", "technocracy", "anarcho_communism",
    ):
        if f"{token} = {{" not in ideologies:
            fail(f"missing ideology {token}")
    if "color = { 80 0 8 }" not in ideologies:
        fail("communism must use dark red")
    if "ruling_party = democratic" in (ROOT / "history" / "countries" / "USA - USA.txt").read_text(encoding="utf-8"):
        fail("country history still uses vanilla democratic")
    recalc = fx.split("dd_recalc_policy_expense = {", 1)[1].split("\n}\n", 1)[0]
    if "dd_labor_4" in recalc or "dd_labor_5" in recalc:
        fail("labour laws must not add a treasury surcharge")
    if policies.count("cost = 150") < 75:
        fail("policy laws should cost 150 PP per adjacent tier")
    if "has_idea = dd_welfare_2" not in policies or "has_idea = dd_welfare_3" in policies.split("dd_welfare_1 = {", 1)[1].split("dd_welfare_2 = {", 1)[0]:
        fail("policy switches must be adjacent tiers only")
    if "add_ideas = dd_taxes_3" not in fx:
        fail("missing tax law default is standard (dd_taxes_3)")
    if "set_variable = { dd_rate_tax_2 = 0.50 }" not in fx:
        fail("low taxes must be half the standard take")
    if "set_variable = { dd_rate_tax_4 = 1.50 }" not in fx:
        fail("high taxes must be +50% of the standard take")
    if "set_variable = { dd_rate_tax_5 = 2.00 }" not in fx:
        fail("choke out capital must double the standard take")
    trig = (ROOT / "common" / "scripted_triggers" / "doomsday_policies.txt").read_text(encoding="utf-8")
    for token in (
        "dd_imm_allows_closed", "dd_imm_allows_tight", "dd_imm_allows_mid",
        "dd_imm_allows_open", "dd_imm_allows_mass",
        "dd_min_allows_persecution", "dd_min_allows_disenfranchised",
        "dd_min_allows_enshrined", "dd_min_allows_uplift",
        "dd_min_allows_equalization",
    ):
        if f"{token} =" not in trig or f"{token} = yes" not in policies:
            fail(f"missing immigration/minority coupling {token}")
    loc = (ROOT / "localisation" / "english" / "doomsday_economy_l_english.yml").read_text(encoding="utf-8")
    for key in (
        "dd_taxes_5:0", "Choke Out Capital",
        "DD_IMM_NEED_MASS_MINORITY", "DD_MIN_NEED_CLOSED_IMM",
    ):
        if key not in loc:
            fail(f"missing tax/immigration loc {key}")


def check_market_pool() -> None:
    market = (ROOT / "common" / "scripted_effects" / "doomsday_market.txt").read_text(encoding="utf-8")
    onact = (ROOT / "common" / "on_actions" / "doomsday_economy.txt").read_text(encoding="utf-8")
    if "dd_init_market_pool" not in market:
        fail("missing dd_init_market_pool")
    if "global.dd_pool_" not in market or "global.dd_ask_" not in market:
        fail("market must use a shared pool and listed cash ask")
    if "dd_init_market_pool = yes" not in onact:
        fail("on_startup must seed the arms market pool")
    if "check_variable = { global.dd_pool_" not in market:
        fail("buys must require pool stock")
    if "set_global_flag = dd_market_pool_init" not in market:
        fail("pool seed must run once")


def check_energy_define() -> None:
    text = (ROOT / "common" / "defines" / "doomsday_defines.lua").read_text(encoding="utf-8")
    if 'ENERGY_RESOURCE = "coal"' not in text:
        fail("ENERGY_RESOURCE must stay coal")
    res = (ROOT / "common" / "resources" / "00_resources.txt").read_text(encoding="utf-8")
    for name in ("coal", "rare_earths", "lithium", "cobalt", "copper", "graphite"):
        if f"{name} = {{" not in res:
            fail(f"missing resource {name}")
    gfx = (ROOT / "interface" / "doomsday_resources.gfx").read_text(encoding="utf-8")
    if gfx.count("noOfFrames = 12") < 2:
        fail("resource icon strips must have 12 frames")
    prod = (ROOT / "interface" / "countryproductionlineview.gui").read_text(encoding="utf-8")
    for token in ("rare_earths_checkbox", "copper_checkbox", "graphite_checkbox"):
        if token not in prod:
            fail(f"production filter missing {token}")
    trade = (ROOT / "interface" / "countrytradeview.gui").read_text(encoding="utf-8")
    if "verticalScrollbar" not in trade or "max_slots = { x = 12 y = 1 }" not in trade:
        fail("trade resource grid must list all 12 resources")


def check_resource_rights() -> None:
    path = ROOT / "common" / "on_actions" / "doomsday_resource_rights.txt"
    if not path.exists():
        fail("missing doomsday_resource_rights on_actions")
        return
    text = path.read_text(encoding="utf-8")
    if "give_resource_rights" not in text:
        fail("start-date resource rights must use give_resource_rights")
    if "set_global_flag = dd_resource_rights_init" not in text:
        fail("resource rights seed must run once")
    if "receiver = CHI" not in text or "receiver = USA" not in text:
        fail("resource rights must include CHI and USA concessions")
    if "receiver = FRA" not in text:
        fail("resource rights must include FRA Gabon concession")
    for token in (
        "state = 780", "state = 889", "state = 545", "state = 556",
        "state = 796", "state = 884", "state = 885", "state = 640",
        "state = 673", "state = 492", "state = 817", "state = 508",
        "state = 687", "state = 897", "state = 298", "state = 539",
    ):
        if token not in text:
            fail(f"resource rights missing {token}")
    if "random" in re.sub(r"#.*", "", text):
        fail("resource rights must stay deterministic")


def check_no_gdp() -> None:
    """GDP is spreadsheet-only. In-game ledger is cash / revenue / expense / debt."""
    gdp_token = re.compile(r"\bgdp\b|debt_to_gdp|GetDdGdp|DD_USD_GDP")
    skip = {"plan_a_parked"}
    roots = [
        ROOT / "common" / "scripted_effects",
        ROOT / "common" / "decisions",
        ROOT / "common" / "scripted_localisation",
        ROOT / "common" / "scripted_guis",
        ROOT / "localisation",
        ROOT / "interface",
        ROOT / "history" / "countries",
    ]
    leftover = []
    for folder in roots:
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".yml", ".gui"}:
                continue
            if any(part in skip for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if gdp_token.search(text):
                leftover.append(path.name)
                if len(leftover) >= 8:
                    break
        if len(leftover) >= 8:
            break
    if leftover:
        fail(f"GDP still in gameplay files {leftover[:8]}")
    gen = (ROOT / "tools" / "generate_doomsday.py").read_text(encoding="utf-8")
    if 'set_variable = {{ gdp' in gen or "set_variable = { gdp" in gen:
        fail("generator still writes gdp into country history")
    dyn = ROOT / "common" / "dynamic_modifiers" / "doomsday_economy.txt"
    if not dyn.exists() or "dd_debt_burden" not in dyn.read_text(encoding="utf-8"):
        fail("missing dd_debt_burden dynamic modifier")
    fx = (ROOT / "common" / "scripted_effects" / "doomsday_economy.txt").read_text(encoding="utf-8")
    if "dd_refresh_debt_burden" not in fx:
        fail("ledger must refresh debt-to-revenue burden")


def main() -> int:
    check_replace_paths()
    check_identical_tech()
    check_no_random()
    check_buildings()
    check_modern_trees()
    check_research_costs()
    check_politics_slots()
    check_market_pool()
    check_energy_define()
    check_resource_rights()
    check_no_gdp()
    check_start_setup()
    if ERRORS:
        print("FAIL")
        for err in ERRORS:
            print(" -", err)
        return 1
    print("OK: floor tech + extras, no random in money/policy, spawn types unchanged, start setup pies/slots/OOBs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
