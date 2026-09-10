#!/usr/bin/env python3
"""Point leftover Cold War techs at vanilla techtree gridboxes and expose 2026 nodes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "interface" / "countrytechtreeview.gui"

GRID_RENAME = [
    ("bba_early_transport_plane_tree", "bba_improved_transport_plane_tree"),
    ("early_transport_plane_tree", "improved_transport_plane_tree"),
    ("early_ship_hull_light_tree", "basic_ship_hull_light_tree"),
    ("early_ship_hull_submarine_tree", "basic_ship_hull_submarine_tree"),
    ("early_destroyer_tree", "basic_destroyer_tree"),
    ("early_submarine_tree", "basic_submarine_tree"),
    ("early_fighter_tree", "jet_fighter1_tree"),
    ("early_bomber_tree", "jet_tactical_bomber1_tree"),
    ("gwtank_chassis_tree", "main_battle_tank_chassis_tree"),
    ("gwtank_tree", "main_battle_tank_tree"),
    ("gw_artillery_tree", "artillery2_tree"),
    ("strategic_bomber1_tree", "jet_strategic_bomber1_tree"),
    ("iw_small_airframe_tree", "advanced_small_airframe_tree"),
    ("iw_medium_airframe_tree", "advanced_medium_airframe_tree"),
    ("iw_large_airframe_tree", "advanced_large_airframe_tree"),
]

AIR_BOXES = """
			gridboxtype = {
				name = "dd_recon_uav_tree"
				position = { x = 300 y = 998 }
				slotsize = { width = 70 height = 70 }
				format = "LEFT"
			}
			gridboxtype = {
				name = "dd_strike_uav_tree"
				position = { x = 440 y = 998 }
				slotsize = { width = 70 height = 70 }
				format = "LEFT"
			}
			gridboxtype = {
				name = "dd_transport_heli_tree"
				position = { x = 580 y = 998 }
				slotsize = { width = 70 height = 70 }
				format = "LEFT"
			}
			gridboxtype = {
				name = "dd_loitering_munition_tree"
				position = { x = 720 y = 998 }
				slotsize = { width = 70 height = 70 }
				format = "LEFT"
			}
"""

ARTY_BOXES = """
			gridboxtype = {
				name = "dd_manpads_tree"
				position = { x = 80 y = 1012 }
				slotsize = { width = 70 height = 70 }
				format = "UP"
			}
			gridboxtype = {
				name = "dd_shorad_tree"
				position = { x = 80 y = 1082 }
				slotsize = { width = 70 height = 70 }
				format = "UP"
			}
			gridboxtype = {
				name = "dd_sam_tree"
				position = { x = 80 y = 1152 }
				slotsize = { width = 70 height = 70 }
				format = "UP"
			}
"""

ELEC_BOXES = """
			gridboxtype = {
				name = "dd_cruise_missile_tree"
				position = { x=1050 y=820 }
				slotsize = { width=60 height= 60 }
				format = "LEFT"
			}
			gridboxtype = {
				name = "dd_srbm_tree"
				position = { x=1170 y=820 }
				slotsize = { width=60 height= 60 }
				format = "LEFT"
			}
"""


def main() -> None:
    text = GUI.read_text(encoding="utf-8")
    if "dd_recon_uav_tree" in text and "main_battle_tank_tree" in text:
        print("already patched")
        return
    for old, new in GRID_RENAME:
        count = text.count(old)
        print(f"{old} -> {new}: {count}")
        if count < 1:
            raise SystemExit(f"missing {old}")
        text = text.replace(old, new)

    text = text.replace('text = "1945"', 'text = "2020"')
    text = text.replace('text = "1950"', 'text = "2026"')
    text = text.replace("width = 2500 height = 1300", "width = 2500 height = 1600")
    text = text.replace("width = 2240 height = 1300", "width = 2240 height = 1600")
    text = text.replace("width = 1515 height = 1390", "width = 1515 height = 1700")

    air_marker = """			gridboxtype = {
				name = "experimental_rockets_tree"
				position = { x = 540 y = 0 }
				size = { width = 400 height = 400 }
				slotsize = { width = 70 height = 70 }
				format = "UP"
			}
		}"""
    if text.count(air_marker) < 2:
        raise SystemExit(f"air marker count {text.count(air_marker)}")
    text = text.replace(air_marker, air_marker.replace("\t\t}", AIR_BOXES + "\t\t}"), 2)

    arty_marker = """			gridboxtype = {
				name = "artillery2_tree"
				position = { x = 300 y = 172 }
				size = { width = 80% height = 80% }
				slotsize = { width = 70 height = 70 }
				format = "UP"
			}
		}"""
    if arty_marker not in text:
        raise SystemExit("arty marker missing")
    text = text.replace(arty_marker, arty_marker.replace("\t\t}", ARTY_BOXES + "\t\t}"), 1)

    elec_marker = """			gridboxtype = {
				name = "experimental_rockets_tree"
				position = { x=1050 y=172 }
				size = { width = 480 height = 650 }
				slotsize = { width=60 height= 60 }
				format = "UP"
			}"""
    if elec_marker not in text:
        raise SystemExit("elec marker missing")
    text = text.replace(elec_marker, elec_marker + ELEC_BOXES, 1)

    GUI.write_text(text, encoding="utf-8")
    print("wrote", GUI)


if __name__ == "__main__":
    main()
