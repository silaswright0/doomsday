"""Write Doomsday ideology definitions and remap country history. Does not run generate_doomsday."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from ideology_map import (
    AUTHORITARIAN,
    ELECTED,
    FAR_LEFT,
    FAR_RIGHT,
    IDEOLOGIES,
    PARENTS,
    TYPE_OF,
    popularities,
    resolve,
)

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = Path(__file__).with_name("doomsday_countries.csv")

RULES = {
    "elected": """		rules = {
			can_create_collaboration_government = no
			can_declare_war_on_same_ideology = no
			can_force_government = yes
			can_send_volunteers = no
			can_puppet = no
			can_lower_tension = yes
			can_only_justify_war_on_threat_country = yes
			can_guarantee_other_ideologies = yes
		}
		can_host_government_in_exile = yes
		war_impact_on_world_tension = 0.20
		faction_impact_on_world_tension = 0.10
		modifiers = {
			generate_wargoal_tension = 1.00
			join_faction_tension = 0.80
			lend_lease_tension = 0.50
			send_volunteers_tension = 0.50
			guarantee_tension = 0.25
			civilian_intel_to_others = 20.0
			army_intel_to_others = 5.0
			navy_intel_to_others = 20.0
			airforce_intel_to_others = 5
			embargo_cost_factor = -0.5
			embargo_threshold_factor = -0.5
		}
		faction_modifiers = {
			faction_trade_opinion_factor = 0.50
		}
		ai_democratic = yes
		ai_ideology_wanted_units_factor = 1.10
		ai_give_core_state_control_threshold = 0""",
    "illiberal": """		rules = {
			can_create_collaboration_government = no
			can_force_government = yes
			can_send_volunteers = yes
			can_puppet = no
			can_guarantee_other_ideologies = yes
		}
		can_host_government_in_exile = yes
		war_impact_on_world_tension = 0.40
		faction_impact_on_world_tension = 0.20
		modifiers = {
			generate_wargoal_tension = 0.50
			join_faction_tension = 0.40
			lend_lease_tension = 0.35
			send_volunteers_tension = 0.30
			guarantee_tension = 0.25
			civilian_intel_to_others = 15.0
			army_intel_to_others = 8.0
			navy_intel_to_others = 15.0
			airforce_intel_to_others = 8
		}
		ai_democratic = yes
		ai_ideology_wanted_units_factor = 1.25
		ai_give_core_state_control_threshold = 10""",
    "authoritarian": """		rules = {
			can_force_government = yes
			can_puppet = yes
			can_send_volunteers = no
		}
		war_impact_on_world_tension = 0.25
		faction_impact_on_world_tension = 0.10
		modifiers = {
			generate_wargoal_tension = 0.50
			join_faction_tension = 0.40
			lend_lease_tension = 0.60
			send_volunteers_tension = 0.40
			guarantee_tension = 0.40
			drift_defence_factor = 0.10
			civilian_intel_to_others = 20.0
			army_intel_to_others = 10.0
			navy_intel_to_others = 20.0
			airforce_intel_to_others = 10.0
		}
		ai_neutral = yes
		ai_ideology_wanted_units_factor = 1.15
		ai_give_core_state_control_threshold = 10000""",
    "far_left": """		rules = {
			can_force_government = yes
			can_send_volunteers = yes
			can_puppet = yes
		}
		can_collaborate = yes
		war_impact_on_world_tension = 0.75
		faction_impact_on_world_tension = 0.50
		modifiers = {
			civilian_intel_to_others = 10.0
			army_intel_to_others = 7.5
			navy_intel_to_others = 12.5
			airforce_intel_to_others = 7.5
			hidden_modifier = { join_faction_tension = -0.1 }
			embargo_threshold_factor = 0.5
			lend_lease_tension = 0.50
		}
		ai_communist = yes
		ai_ideology_wanted_units_factor = 1.20
		ai_give_core_state_control_threshold = 10""",
    "far_right": """		rules = {
			can_force_government = yes
			can_send_volunteers = yes
			can_puppet = yes
		}
		can_collaborate = yes
		war_impact_on_world_tension = 1.00
		faction_impact_on_world_tension = 1.00
		modifiers = {
			justify_war_goal_when_in_major_war_time = -0.80
			civilian_intel_to_others = 15.0
			army_intel_to_others = 10.0
			navy_intel_to_others = 10.0
			airforce_intel_to_others = 10.0
			hidden_modifier = { join_faction_tension = -0.1 }
			embargo_cost_factor = 1
			lend_lease_tension = 0.50
		}
		ai_fascist = yes
		ai_ideology_wanted_units_factor = 1.65
		ai_give_core_state_control_threshold = 10000""",
}

FACTION_NAMES = {
    "elected": "DEMOCRATIC",
    "illiberal": "DEMOCRATIC",
    "authoritarian": "NONALIGNED",
    "far_left": "COMMUNIST",
    "far_right": "FASCIST",
}


def write_ideologies() -> None:
    lines = [
        "# Doomsday 2026 ideologies. Country-scoped. No random.",
        "ideologies = {",
        "",
    ]
    for token, typ, _name, _tname, _noun, color, kind, _icon in IDEOLOGIES:
        r, g, b = color
        fam = FACTION_NAMES[kind]
        count = 6 if fam == "DEMOCRATIC" else 5
        names = "\n".join(f'\t\t\t"FACTION_NAME_{fam}_{i}"' for i in range(1, count + 1))
        extra = ""
        if token == "anarcho_communism":
            extra = "\n\t\t\t\tcan_be_randomly_selected = no"
        lines.append(f"\t{token} = {{")
        lines.append("\t\ttypes = {")
        lines.append(f"\t\t\t{typ} = {{{extra}")
        lines.append("\t\t\t}")
        lines.append("\t\t}")
        lines.append("\t\tdynamic_faction_names = {")
        lines.append(names)
        lines.append("\t\t}")
        lines.append(f"\t\tcolor = {{ {r} {g} {b} }}")
        lines.append(RULES[kind])
        lines.append("\t}")
        lines.append("")
    lines.append("}")
    path = ROOT / "common" / "ideologies" / "00_ideologies.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_gfx() -> None:
    lines = ["spriteTypes = {"]
    for token, _typ, _n, _tn, _noun, _c, _k, icon in IDEOLOGIES:
        tex = f"gfx/interface/ideologies/{icon}.dds"
        group = tex if icon == "anarchism" else f"gfx/interface/ideologies/{icon}_group.dds"
        lines.append("	spriteType = {")
        lines.append(f'		name = "GFX_ideology_{token}"')
        lines.append(f'		texturefile = "{tex}"')
        lines.append("	}")
        lines.append("	spriteType = {")
        lines.append(f'		name = "GFX_ideology_{token}_group"')
        lines.append(f'		texturefile = "{group}"')
        lines.append("	}")
    lines.append("}")
    path = ROOT / "interface" / "doomsday_ideologies.gfx"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_loc() -> None:
    lines = ["l_english:"]
    for token, typ, name, tname, noun, _c, _k, _icon in IDEOLOGIES:
        desc = {
            "social_democracy": "A parliamentary welfare state. Markets stay, but labour and public services set the floor.",
            "social_liberalism": "Civil rights and open markets first. The state referees; it does not own the shop.",
            "liberal_conservatism": "Elections, property, and cautious reform. Change is allowed if it does not smash the furniture.",
            "progressive_populism": "A popular mandate against elites, from the left. Redistribution and identity both count as politics.",
            "national_populism": "The nation against the cosmopolitan centre. Elections continue; institutions bend.",
            "sovereign_democracy": "Managed pluralism. Parties exist, but the circle that matters does not rotate.",
            "military_junta": "Officers hold the ministries. Civilian politics wait in the courtyard.",
            "absolute_monarchy": "The crown is the state. Cabinets advise; they do not rule.",
            "state_socialism": "A vanguard party monopolizes the state and the commanding heights.",
            "left_wing_nationalism": "Anti-imperial politics with a national flag. The party speaks for the people and the soil.",
            "islamic_democracy": "Elected government under an Islamic public order. Ballots and sharia share the room.",
            "theocratic_absolutism": "Clerics hold sovereignty. Law is revelation administered by the faithful.",
            "jihadist_fundamentalism": "Armed restoration of a purified Islamic order. The state is a camp on the way to the caliphate.",
            "democratic_confederalism": "Bottom-up councils, communal economy, and armed self-defence without a conventional nation-state.",
            "fascism": "The leader, the nation, and the party are one. Opposition is treason.",
            "communism": "Class rule through a communist party aiming at a classless society. No private commanding heights.",
            "technocracy": "Engineers and planners govern. Expertise outranks faction.",
            "anarcho_communism": "No state, no capital. Voluntary communes and mutual aid replace ministries.",
        }[token]
        lines.append(f' {token}:0 "{name}"')
        lines.append(f' {token}_noun:0 "{noun}"')
        lines.append(f' {token}_desc:0 "{desc}"')
        lines.append(f' {typ}:0 "{tname}"')
        lines.append(f' {typ}_desc:0 "{desc}"')
    path = ROOT / "localisation" / "english" / "doomsday_ideologies_l_english.yml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig", newline="\n")


def trigger_or(names: list[str]) -> str:
    inner = "\n".join(f"		has_government = {n}" for n in names)
    return f"	OR = {{\n{inner}\n	}}"


def write_triggers() -> None:
    text = "\n".join(
        [
            "# Ideology families. Country-scoped. No random.",
            "dd_is_elected_gov = {",
            trigger_or(ELECTED),
            "}",
            "",
            "dd_is_authoritarian_gov = {",
            trigger_or(AUTHORITARIAN),
            "}",
            "",
            "dd_is_far_left_gov = {",
            trigger_or(FAR_LEFT),
            "}",
            "",
            "dd_is_far_right_gov = {",
            trigger_or(FAR_RIGHT),
            "}",
            "",
        ]
    )
    path = ROOT / "common" / "scripted_triggers" / "doomsday_ideologies.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def patch_replace_paths() -> None:
    line = 'replace_path="common/ideologies"'
    for path in (ROOT / "descriptor.mod", ROOT.parent / "doomsday.mod"):
        text = path.read_text(encoding="utf-8")
        if line in text:
            continue
        text = text.replace(
            'replace_path="common/idea_tags"',
            'replace_path="common/idea_tags"\n' + line,
            1,
        )
        path.write_text(text, encoding="utf-8", newline="\n")


def load_csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def patch_csv(rows: list[dict[str, str]]) -> dict[str, dict]:
    by_tag = {}
    for row in rows:
        tag = row["tag"]
        new = resolve(tag, row.get("ideology") or "", row.get("subideology") or "")
        row["ideology"] = new
        row["subideology"] = TYPE_OF[new]
        by_tag[tag] = row
    write_csv(rows)
    return by_tag


def pop_block(pops: dict[str, int]) -> str:
    lines = ["set_popularities = {"]
    for token in PARENTS:
        if token in pops:
            lines.append(f"	{token} = {pops[token]}")
    lines.append("}")
    return "\n".join(lines)


def patch_country_file(path: Path, row: dict | None) -> None:
    text = path.read_text(encoding="utf-8")
    tag = path.name.split(" -", 1)[0].strip()
    old_id = "neutrality"
    old_sub = "oligarchism"
    m = re.search(r"ruling_party = (\w+)", text)
    if m:
        old_id = m.group(1)
    m = re.search(r"create_country_leader = \{.*?ideology = (\w+)", text, re.S)
    if m:
        old_sub = m.group(1)
    if row:
        ruling = resolve(tag, row.get("ideology") or old_id, row.get("subideology") or old_sub)
        # CSV already rewritten to new tokens; resolve still works via TAG_IDEOLOGY
        ruling = row["ideology"] if row.get("ideology") in TYPE_OF else ruling
        dem = int(float(row.get("dem") or 0))
        com = int(float(row.get("com") or 0))
        fas = int(float(row.get("fas") or 0))
        neu = int(float(row.get("neu") or 0))
    else:
        ruling = resolve(tag, old_id, old_sub)
        buckets = {k: 0 for k in ("democratic", "communism", "fascism", "neutrality")}
        for name, val in re.findall(r"\t(democratic|communism|fascism|neutrality) = (\d+)", text):
            buckets[name] = int(val)
        if sum(buckets.values()) == 0:
            buckets["neutrality"] = 100
        dem, com, fas, neu = buckets["democratic"], buckets["communism"], buckets["fascism"], buckets["neutrality"]
    pops = popularities(ruling, dem, com, fas, neu)
    sub = TYPE_OF[ruling]
    text = re.sub(r"ruling_party = \w+", f"ruling_party = {ruling}", text, count=1)
    text = re.sub(
        r"set_popularities = \{.*?\n\}",
        pop_block(pops),
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(
        r"(create_country_leader = \{.*?ideology = )\w+",
        rf"\g<1>{sub}",
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_history(by_tag: dict[str, dict]) -> None:
    folder = ROOT / "history" / "countries"
    for path in folder.glob("*.txt"):
        tag = path.name.split(" -", 1)[0].strip()
        patch_country_file(path, by_tag.get(tag))


def patch_bookmarks() -> None:
    path = ROOT / "common" / "bookmarks" / "doomsday_2026.txt"
    text = path.read_text(encoding="utf-8")
    mapping = {
        '"USA"': "national_populism",
        '"CHI"': "state_socialism",
        '"SOV"': "sovereign_democracy",
        '"RAJ"': "national_populism",
        '"ENG"': "social_democracy",
        '"FRA"': "social_liberalism",
        '"GER"': "liberal_conservatism",
        '"JAP"': "liberal_conservatism",
    }
    for tag, ideo in mapping.items():
        text = re.sub(
            rf"({re.escape(tag)}=\{{.*?ideology = )\w+",
            rf"\g<1>{ideo}",
            text,
            count=1,
            flags=re.S,
        )
    path.write_text(text, encoding="utf-8", newline="\n")


GOV_REPLACEMENTS = [
    (r"has_government = democratic", "dd_is_elected_gov = yes"),
    (r"has_government = neutrality", "dd_is_authoritarian_gov = yes"),
    (r"has_government = communism", "dd_is_far_left_gov = yes"),
    (r"has_government = fascism", "dd_is_far_right_gov = yes"),
]


def patch_government_checks() -> None:
    roots = [
        ROOT / "common" / "national_focus",
        ROOT / "common" / "technologies",
        ROOT / "common" / "units",
    ]
    for folder in roots:
        if not folder.exists():
            continue
        for path in folder.rglob("*.txt"):
            text = path.read_text(encoding="utf-8")
            new = text
            for pat, repl in GOV_REPLACEMENTS:
                new = re.sub(pat, repl, new)
            if new != text:
                path.write_text(new, encoding="utf-8", newline="\n")


def main() -> None:
    write_ideologies()
    write_gfx()
    write_loc()
    write_triggers()
    patch_replace_paths()
    rows = load_csv_rows()
    by_tag = patch_csv(rows)
    patch_history(by_tag)
    patch_bookmarks()
    patch_government_checks()
    print(f"wrote {len(PARENTS)} ideologies, remapped {len(list((ROOT / 'history' / 'countries').glob('*.txt')))} countries")


if __name__ == "__main__":
    main()
