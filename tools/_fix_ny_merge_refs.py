"""Restore pre-merge gameplay refs, then remap state IDs with placeholders (no cascade)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "tools/_recovered"


def install_recovered() -> None:
    shutil.copy2(REC / "doomsday_usa.txt", ROOT / "common/scripted_effects/doomsday_usa.txt")
    shutil.copy2(REC / "USA - USA.txt", ROOT / "history/countries/USA - USA.txt")
    shutil.copy2(REC / "USB - USB.txt", ROOT / "history/countries/USB - USB.txt")
    shutil.copy2(REC / "FVA - Atlantic Command.txt", ROOT / "history/countries/FVA - Atlantic Command.txt")
    shutil.copy2(REC / "NYF - New York Finance.txt", ROOT / "history/countries/NYF - New York Finance.txt")


def patch_usa_pre_merge() -> None:
    path = ROOT / "common/scripted_effects/doomsday_usa.txt"
    text = path.read_text(encoding="utf-8")

    # WCL also takes LA metro
    text = text.replace(
        """		WCL = {
			transfer_state = 378
			add_state_core = 378
			transfer_state = 377
			add_state_core = 377
			transfer_state = 376
			add_state_core = 376
			set_capital = { state = 378 }
			set_country_flag = dd_cw_released
		}""",
        """		WCL = {
			transfer_state = 378
			add_state_core = 378
			transfer_state = 1139
			add_state_core = 1139
			transfer_state = 377
			add_state_core = 377
			transfer_state = 376
			add_state_core = 376
			set_capital = { state = 378 }
			set_country_flag = dd_cw_released
		}""",
    )

    # NYF owns island + NYC
    text = text.replace(
        """		NYF = {
			transfer_state = 1125
			add_state_core = 1125
			set_capital = { state = 1125 }
			set_country_flag = dd_cw_released
		}""",
        """		NYF = {
			transfer_state = 1125
			add_state_core = 1125
			transfer_state = 1138
			add_state_core = 1138
			set_capital = { state = 1138 }
			set_country_flag = dd_cw_released
		}""",
    )

    # TXO owns gulf oil + Houston metro (+ keep NOLA if present)
    if "transfer_state = 1140" not in text:
        text = text.replace(
            """		TXO = {
			transfer_state = 1126
			add_state_core = 1126
			transfer_state = 1133
			add_state_core = 1133
			set_country_flag = dd_cw_released
		}""",
            """		TXO = {
			transfer_state = 1126
			add_state_core = 1126
			transfer_state = 1140
			add_state_core = 1140
			transfer_state = 1133
			add_state_core = 1133
			set_country_flag = dd_cw_released
		}""",
        )

    path.write_text(text, encoding="utf-8", newline="\n")


def patch_war_pre_merge() -> None:
    path = ROOT / "common/scripted_effects/doomsday_usa_war.txt"
    text = path.read_text(encoding="utf-8")

    # Spawn helpers: province 859 lives in state 1125 (island), not 358
    text = text.replace(
        """		358 = {
			create_unit = {
				division = "name = \\"Militia\\" division_template = \\"Militia\\" start_experience_factor = 0.2 start_equipment_factor = 0.55"
				owner = PREV
				count = 1
				prioritize_location = 859
				allow_spawning_on_enemy_provs = yes
			}
		}""",
        """		1125 = {
			create_unit = {
				division = "name = \\"Militia\\" division_template = \\"Militia\\" start_experience_factor = 0.2 start_equipment_factor = 0.55"
				owner = PREV
				count = 1
				prioritize_location = 859
				allow_spawning_on_enemy_provs = yes
			}
		}""",
    )
    text = text.replace(
        """		358 = {
			create_unit = {
				division = "name = \\"National Guard\\" division_template = \\"National Guard\\" start_experience_factor = 0.3 start_equipment_factor = 0.65"
				owner = PREV
				count = 1
				prioritize_location = 859
				allow_spawning_on_enemy_provs = yes
			}
		}""",
        """		1125 = {
			create_unit = {
				division = "name = \\"National Guard\\" division_template = \\"National Guard\\" start_experience_factor = 0.3 start_equipment_factor = 0.65"
				owner = PREV
				count = 1
				prioritize_location = 859
				allow_spawning_on_enemy_provs = yes
			}
		}""",
    )

    # Insert LA metro pocket after the San Diego / CA pocket block if missing
    if "13424" not in text:
        needle = """		set_province_controller = 768
	}
	# Rubio holds northern and central Arizona."""
        insert = """		set_province_controller = 768
	}
	# Anarchists hold one Los Angeles metro province inside liberal LA.
	if = {
		limit = {
			ACA = { has_country_flag = dd_cw_released }
			1139 = { NOT = { is_owned_by = ACA } }
		}
		if = {
			limit = {
				1139 = { is_owned_by = WCL }
				NOT = { ACA = { has_war_with = WCL } }
			}
			ACA = { declare_war_on = { target = WCL type = dd_annex } }
		}
		if = {
			limit = {
				1139 = { is_owned_by = USA }
				NOT = { ACA = { has_war_with = USA } }
			}
			ACA = { declare_war_on = { target = USA type = dd_annex } }
		}
		ACA = { set_province_controller = 13424 }
	}
	else_if = {
		limit = {
			has_country_flag = dd_usa_keep_aca
			1139 = { NOT = { is_owned_by = USA } }
		}
		if = {
			limit = {
				1139 = { is_owned_by = WCL }
				NOT = { has_war_with = WCL }
			}
			declare_war_on = { target = WCL type = dd_annex }
		}
		set_province_controller = 13424
	}
	# Rubio holds northern and central Arizona."""
        if needle not in text:
            raise SystemExit("war LA insert needle missing")
        text = text.replace(needle, insert, 1)

    # NYF capital should be NYC metro before merge remap
    text = text.replace(
        """	NYF = {
		set_capital = { state = 1125 }
		set_variable = { dd_cw_spawn = 2 }
		dd_usa_cw_spawn_inf_eng_n = yes
	}""",
        """	NYF = {
		set_capital = { state = 1138 }
		set_variable = { dd_cw_spawn = 2 }
		dd_usa_cw_spawn_inf_eng_n = yes
	}""",
    )

    # FVA: if they own NCR, capital there and spawn DC garrison
    if "owns_state = 1141" not in text and "prioritize_location = 3957" not in text:
        old_fva_cap = """		FVA = {
			set_capital = { state = 463 }
			dd_usa_cw_tpl_infantry_3x6_eng = yes"""
        new_fva_cap = """		FVA = {
			if = {
				limit = { owns_state = 1141 }
				set_capital = { state = 1141 }
			}
			else = {
				set_capital = { state = 463 }
			}
			dd_usa_cw_tpl_infantry_3x6_eng = yes"""
        if old_fva_cap not in text:
            raise SystemExit("FVA capital block missing")
        text = text.replace(old_fva_cap, new_fva_cap, 1)

        old_spawn = """			1112 = { create_unit = { division = "name = \\"Federal Garrison\\" division_template = \\"Federal Garrison\\" start_experience_factor = 0.4 start_equipment_factor = 0.8" owner = FVA count = 2 prioritize_location = 7590 } }
			463 = { create_unit = { division = "name = \\"Federal Garrison\\" division_template = \\"Federal Garrison\\" start_experience_factor = 0.4 start_equipment_factor = 0.8" owner = FVA count = 3 prioritize_location = 13091 } }
		}
	}"""
        new_spawn = """			1112 = { create_unit = { division = "name = \\"Federal Garrison\\" division_template = \\"Federal Garrison\\" start_experience_factor = 0.4 start_equipment_factor = 0.8" owner = FVA count = 2 prioritize_location = 7590 } }
			463 = { create_unit = { division = "name = \\"Federal Garrison\\" division_template = \\"Federal Garrison\\" start_experience_factor = 0.4 start_equipment_factor = 0.8" owner = FVA count = 3 prioritize_location = 13091 } }
			if = {
				limit = { owns_state = 1141 }
				1141 = { create_unit = { division = "name = \\"Federal Garrison\\" division_template = \\"Federal Garrison\\" start_experience_factor = 0.4 start_equipment_factor = 0.8" owner = FVA count = 4 prioritize_location = 3957 } }
			}
		}
	}"""
        if old_spawn not in text:
            raise SystemExit("FVA spawn block missing")
        text = text.replace(old_spawn, new_spawn, 1)

    # Comment
    text = text.replace(
        "# Wall Street holds upstate/adjacent New York province 859.",
        "# Wall Street owns New York Island (state 1125); no extra province seizes.",
    )

    path.write_text(text, encoding="utf-8", newline="\n")


def remap_with_placeholders(text: str) -> str:
    """OLD->NEW: 1141->1140, 1140->1139, 1139->1138, 1138->1125. Use temps to avoid cascade."""
    mapping = [(1141, 1140), (1140, 1139), (1139, 1138), (1138, 1125)]
    # First replace old IDs with unique tokens
    for old, _new in mapping:
        token = f"__DD_STATE_{old}__"
        patterns = [
            (rf"\btransfer_state\s*=\s*{old}\b", f"transfer_state = {token}"),
            (rf"\badd_state_core\s*=\s*{old}\b", f"add_state_core = {token}"),
            (rf"\bowns_state\s*=\s*{old}\b", f"owns_state = {token}"),
            (rf"\bcontrols_state\s*=\s*{old}\b", f"controls_state = {token}"),
            (rf"\bset_capital\s*=\s*\{{\s*state\s*=\s*{old}\b", f"set_capital = {{ state = {token}"),
            (rf"(?m)^capital\s*=\s*{old}\b", f"capital = {token}"),
            (rf"(?m)^(\t+){old}\s*=\s*{{", rf"\g<1>{token} = {{"),
            (rf"(?<!\d){old}\s*=\s*{{\s*create_unit", f"{token} = {{ create_unit"),
            (rf"(?<!\d){old}\s*=\s*{{\s*add_building_construction", f"{token} = {{ add_building_construction"),
            (
                rf"(?<!\d){old}\s*=\s*{{(\s*(?:NOT\s*=\s*{{)?\s*is_owned_by)",
                rf"{token} = {{\1",
            ),
            (rf"(?<!\d){old}\s*=\s*{{\s*NOT\s*=\s*{{\s*is_owned_by", f"{token} = {{ NOT = {{ is_owned_by"),
        ]
        for pat, repl in patterns:
            text = re.sub(pat, repl, text)

    for old, new in mapping:
        text = text.replace(f"__DD_STATE_{old}__", str(new))
    return text


def apply_remap() -> None:
    targets = [
        ROOT / "common/scripted_effects/doomsday_usa.txt",
        ROOT / "common/scripted_effects/doomsday_usa_war.txt",
        ROOT / "history/countries/USA - USA.txt",
        ROOT / "history/countries/USB - USB.txt",
        ROOT / "history/countries/FVA - Atlantic Command.txt",
        ROOT / "history/countries/NYF - New York Finance.txt",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        path.write_text(remap_with_placeholders(text), encoding="utf-8", newline="\n")

    # Clean duplicate NYF transfers (1125+1138 both -> 1125)
    usa = ROOT / "common/scripted_effects/doomsday_usa.txt"
    text = usa.read_text(encoding="utf-8")
    text = re.sub(
        r"(NYF = \{\n\t\t\ttransfer_state = 1125\n\t\t\tadd_state_core = 1125\n)"
        r"\t\t\ttransfer_state = 1125\n\t\t\tadd_state_core = 1125\n",
        r"\1",
        text,
    )
    text = text.replace(
        "\t# NY Island + Rhode Island\n",
        "\t# New York City + Rhode Island\n",
    )
    text = text.replace(
        "# Shared cores: west coast for anarchists; right-wing bloc; demsoc↔commie + NY Island + RI.",
        "# Shared cores: west coast for anarchists; right-wing bloc; demsoc↔commie + NYC + RI.",
    )
    text = text.replace(
        "\t# Demsoc + communists core each other's states, plus NY Island and Rhode Island.\n",
        "\t# Demsoc + communists core each other's states, plus NYC and Rhode Island.\n",
    )
    usa.write_text(text, encoding="utf-8", newline="\n")

    war = ROOT / "common/scripted_effects/doomsday_usa_war.txt"
    w = war.read_text(encoding="utf-8")
    w = w.replace(
        "# Wall Street owns New York Island (state 1125); no extra province seizes.",
        "# Wall Street owns New York City (state 1125); no extra province seizes.",
    )
    war.write_text(w, encoding="utf-8", newline="\n")


def verify() -> None:
    usa = (ROOT / "history/countries/USA - USA.txt").read_text(encoding="utf-8")
    fva = (ROOT / "history/countries/FVA - Atlantic Command.txt").read_text(encoding="utf-8")
    nyf = (ROOT / "history/countries/NYF - New York Finance.txt").read_text(encoding="utf-8")
    usb = (ROOT / "history/countries/USB - USB.txt").read_text(encoding="utf-8")
    assert "capital = 1140" in usa, usa.splitlines()[1]
    assert "capital = 1140" in fva, fva.splitlines()[1]
    assert "capital = 1140" in usb, usb.splitlines()[1]
    assert "capital = 1125" in nyf, nyf.splitlines()[1]

    fx = (ROOT / "common/scripted_effects/doomsday_usa.txt").read_text(encoding="utf-8")
    assert "transfer_state = 1141" not in fx
    assert "state = 1141" not in fx
    assert "transfer_state = 1140" in fx  # NCR
    assert "add_state_core = 1138" in fx  # LA
    assert "add_state_core = 1139" in fx  # Houston
    # NYF single transfer
    assert fx.count("NYF = {\n\t\t\ttransfer_state = 1125\n\t\t\tadd_state_core = 1125\n\t\t\tset_capital") == 1

    war = (ROOT / "common/scripted_effects/doomsday_usa_war.txt").read_text(encoding="utf-8")
    assert "1138 = { NOT = { is_owned_by = ACA }" in war or "1138 = { is_owned_by = WCL }" in war
    assert "owns_state = 1140" in war
    assert "prioritize_location = 3957" in war
    assert "set_capital = { state = 1125 }" in war  # NYF

    focus = (ROOT / "common/national_focus/usa.txt").read_text(encoding="utf-8")
    assert "bypass" not in focus
    assert focus.count("cancel_if") >= 100

    assert (ROOT / "gfx/flags/FDS.tga").stat().st_size > 1000
    print("verify ok")


def main() -> None:
    install_recovered()
    patch_usa_pre_merge()
    patch_war_pre_merge()
    apply_remap()
    verify()
    print("done")


if __name__ == "__main__":
    main()
