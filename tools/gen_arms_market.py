"""Generate treasury Arms Market rows from every equipment archetype."""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EQ = ROOT / "common" / "units" / "equipment"
SKIP_DIRS = {"modules", "upgrades"}
SKIP_FILES = {"plane_filters.txt", "tank_filters.txt", "x_plane_airframes.txt", "x_tank_chassis.txt"}
SKIP_ARCH = {"mothership_equipment"}

LAND_IFACE = {
    "interface_category_land",
    "interface_category_armor",
}
AIR_IFACE = {"interface_category_air"}
NAVY_IFACE = {
    "interface_category_other_ships",
    "interface_category_capital_ships",
    "interface_category_screen_ships",
}

SPRITE_OVERRIDE = {
    "ballistic_missile_equipment": "GFX_ballistic_missile_equipment_1_medium",
    "guided_missile_equipment": "GFX_guided_missile_equipment_3_medium",
    "sam_missile_equipment": "GFX_sam_missile_equipment_medium",
    "nuclear_missile_equipment": "GFX_ballistic_missile_equipment_1_medium",
    "explosive_ammo_equipment": "GFX_guided_missile_equipment_3_medium",
    "recon_uav_equipment": "GFX_scout_plane1_medium",
    "strike_uav_equipment": "GFX_archetype_CAS_equipment_medium",
}


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        if "#" in line:
            line = line[: line.index("#")]
        out.append(line)
    return "\n".join(out)


def extract_blocks(text: str) -> list[tuple[str, str]]:
    m = re.search(r"equipments\s*=\s*\{", text)
    if not m:
        return []
    i = m.end()
    depth = 1
    body_start = i
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    body = text[body_start : i - 1]
    blocks = []
    j = 0
    while j < len(body):
        mm = re.search(r"([A-Za-z0-9_]+)\s*=\s*\{", body[j:])
        if not mm:
            break
        name = mm.group(1)
        start = j + mm.end()
        depth = 1
        k = start
        while k < len(body) and depth:
            if body[k] == "{":
                depth += 1
            elif body[k] == "}":
                depth -= 1
            k += 1
        blocks.append((name, body[start : k - 1]))
        j = k
    return blocks


def first(pat: str, content: str, default=None):
    m = re.search(pat, content)
    return m.group(1) if m else default


def parse():
    archetypes: dict[str, dict] = {}
    variants: dict[str, list] = {}
    for path in sorted(EQ.rglob("*.txt")):
        if path.parent.name in SKIP_DIRS or path.name in SKIP_FILES:
            continue
        text = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
        for name, content in extract_blocks(text):
            if re.search(r"is_archetype\s*=\s*yes", content):
                ic = first(r"build_cost_ic\s*=\s*([0-9.]+)", content)
                archetypes[name] = {
                    "picture": first(r"picture\s*=\s*(\S+)", content),
                    "ic": float(ic) if ic else None,
                    "iface": first(r"interface_category\s*=\s*(\S+)", content),
                }
            arch = first(r"archetype\s*=\s*(\S+)", content)
            if arch:
                year = first(r"year\s*=\s*(\d+)", content)
                ic = first(r"build_cost_ic\s*=\s*([0-9.]+)", content)
                variants.setdefault(arch, []).append(
                    {
                        "name": name,
                        "year": int(year) if year else 0,
                        "ic": float(ic) if ic else None,
                    }
                )
    return archetypes, variants


def category(iface: str | None, name: str) -> str:
    if iface in LAND_IFACE:
        return "land"
    if iface in AIR_IFACE:
        return "air"
    if iface in NAVY_IFACE:
        return "navy"
    if "hull" in name or name in {"convoy"}:
        return "navy"
    if "plane" in name or "missile" in name or "uav" in name:
        return "air"
    return "land"


def lot_size(cat: str, name: str) -> int:
    if cat == "navy":
        return 10 if name == "convoy" else 1
    if cat == "air":
        return 10
    if name in {"infantry_equipment", "support_equipment"}:
        return 100
    if "train" in name:
        return 5
    if "railway" in name or "land_cruiser" in name:
        return 1
    if "tank" in name or "chassis" in name or "mechanized" in name or "armored" in name:
        return 10
    return 20


def default_ic(cat: str, name: str) -> float:
    if "nuclear" in name:
        return 200
    if cat == "navy":
        return 80 if name != "convoy" else 8
    if "missile" in name:
        return 40
    if cat == "air":
        return 25
    if "tank" in name or "chassis" in name:
        return 15
    return 5


def sprite_for(arch: str, picture: str | None) -> tuple[str, float]:
    if arch in SPRITE_OVERRIDE:
        return SPRITE_OVERRIDE[arch], 0.42
    if picture:
        return f"GFX_{picture}_medium", 0.42
    if category(None, arch) == "navy":
        return "GFX_im_navy_icon", 1.0
    return "GFX_infantry_equipment_text_icon", 1.0


def catalog() -> list[dict]:
    archetypes, variants = parse()
    rows = []
    for arch, info in archetypes.items():
        if arch in SKIP_ARCH:
            continue
        vs = variants.get(arch, [])
        if not vs:
            continue
        best = max(vs, key=lambda x: (x["year"], x["name"]))
        cat = category(info["iface"], arch)
        ic = best["ic"] or info["ic"] or default_ic(cat, arch)
        amount = lot_size(cat, arch)
        buy = max(1, int(round(ic * amount / 7.0)))
        sell = max(1, buy // 2)
        sprite, scale = sprite_for(arch, info["picture"])
        slug = arch.replace("equipment", "eq").replace("__", "_").strip("_")
        rows.append(
            {
                "arch": arch,
                "buy_type": best["name"],
                "slug": slug,
                "cat": cat,
                "amount": amount,
                "buy": buy,
                "sell": sell,
                "sprite": sprite,
                "scale": scale,
            }
        )
    order = {"land": 0, "air": 1, "navy": 2}
    rows.sort(key=lambda r: (order[r["cat"]], r["arch"]))
    return rows


def entry_gui(row: dict, y: int) -> str:
    slug = row["slug"]
    scale_line = f"\n\t\t\t\t\tscale = {row['scale']}" if row["scale"] != 1.0 else ""
    return f"""
			containerWindowType = {{
				name = "dd_row_{slug}"
				position = {{ x = 10 y = {y} }}
				size = {{ width = 500 height = 100 }}
				clipping = no

				iconType = {{
					name = "dd_{slug}_card"
					spriteType = "GFX_land_equipment_market_entry"
					position = {{ x = 0 y = 0 }}
					frame = 1
					alwaystransparent = yes
				}}
				iconType = {{
					name = "dd_{slug}_icon"
					spriteType = "{row['sprite']}"
					position = {{ x = 168 y = 18 }}{scale_line}
					alwaystransparent = yes
				}}
				instantTextboxType = {{
					name = "dd_{slug}_name"
					position = {{ x = 12 y = 6 }}
					font = "hoi_18mbs"
					text = "DD_MARKET_NAME_{slug.upper()}"
					maxWidth = 300
					maxHeight = 20
					format = left
					alwaystransparent = yes
				}}
				instantTextboxType = {{
					name = "dd_{slug}_stock"
					position = {{ x = 12 y = 28 }}
					font = "hoi_16mbs"
					text = "DD_MARKET_STOCK_{slug.upper()}"
					maxWidth = 300
					maxHeight = 18
					format = left
					alwaystransparent = yes
				}}
				iconType = {{
					name = "dd_{slug}_cash_icon"
					spriteType = "GFX_dd_icon_cash"
					position = {{ x = 12 y = 68 }}
					alwaystransparent = yes
				}}
				instantTextboxType = {{
					name = "dd_{slug}_buy_price"
					position = {{ x = 40 y = 70 }}
					font = "hoi_18mbs"
					text = "DD_MARKET_PRICE_{slug.upper()}_BUY"
					maxWidth = 220
					maxHeight = 20
					format = left
					alwaystransparent = yes
				}}
				instantTextboxType = {{
					name = "dd_{slug}_sell_price"
					position = {{ x = 40 y = 70 }}
					font = "hoi_18mbs"
					text = "DD_MARKET_PRICE_{slug.upper()}_SELL"
					maxWidth = 220
					maxHeight = 20
					format = left
					alwaystransparent = yes
				}}
				buttonType = {{
					name = "dd_buy_{slug}"
					quadTextureSprite = "GFX_diplo_filter_entry"
					buttonText = "DD_MARKET_BUY"
					buttonFont = "hoi_16mbs"
					position = {{ x = 360 y = 32 }}
					clicksound = click_default
					pdx_tooltip = "DD_BUY_{slug.upper()}_TT"
				}}
				buttonType = {{
					name = "dd_sell_{slug}"
					quadTextureSprite = "GFX_diplo_filter_entry"
					buttonText = "DD_MARKET_SELL"
					buttonFont = "hoi_16mbs"
					position = {{ x = 360 y = 32 }}
					clicksound = click_default
					pdx_tooltip = "DD_SELL_{slug.upper()}_TT"
				}}
			}}"""


def list_gui(cat: str, rows: list[dict]) -> str:
    entries = []
    for i, row in enumerate(rows):
        entries.append(entry_gui(row, 8 + i * 104))
    inner = "\n".join(entries)
    # Independent windows. Nested lists ignore _visible, so navy sat on top.
    return f"""
	containerWindowType = {{
		name = "dd_market_list_{cat}"
		position = {{ x = 10 y = 226 }}
		size = {{ width = 530 height = 100%% }}
		margin = {{ top = 0 bottom = 24 }}
		verticalScrollbar = "right_vertical_slider"
		scroll_wheel_factor = 40
		smooth_scrolling = yes
		clipping = yes

		background = {{
			name = "dd_market_list_{cat}_bg"
			spriteType = "GFX_tiled_window2_1b_border"
		}}
{inner}
	}}"""


def write_gui(rows: list[dict]) -> None:
    by_cat = {c: [r for r in rows if r["cat"] == c] for c in ("land", "air", "navy")}
    lists = "".join(list_gui(cat, by_cat[cat]) for cat in ("land", "air", "navy"))
    text = f"""guiTypes = {{

	containerWindowType = {{
		name = "dd_arms_market_window"
		position = {{ x = 5 y = 78 }}
		size = {{ width = 550 height = 100%% }}
		clipping = no

		background = {{
			name = "Background"
			spriteType = "GFX_tiled_bg"
		}}

		iconType = {{
			name = "dd_market_header_bg"
			spriteType = "GFX_header_bg"
			position = {{ x = 5 y = 7 }}
		}}

		instantTextboxType = {{
			name = "dd_market_title"
			position = {{ x = 45 y = 8 }}
			font = "hoi_36header"
			text = "DD_ARMS_MARKET_TITLE"
			maxWidth = 440
			maxHeight = 20
			format = left
		}}

		buttonType = {{
			name = "dd_close_market"
			position = {{ x = -43 y = 9 }}
			quadTextureSprite = "GFX_closebutton"
			buttonFont = "Main_14_black"
			shortcut = "ESCAPE"
			Orientation = "UPPER_RIGHT"
			clicksound = click_close
		}}

		containerWindowType = {{
			name = "dd_market_top"
			position = {{ x = 9 y = 47 }}
			clipping = no

			iconType = {{
				name = "dd_market_top_bg"
				quadTextureSprite = "GFX_deployment_binding"
			}}

			iconType = {{
				name = "dd_market_cash_icon"
				spriteType = "GFX_dd_icon_cash"
				position = {{ x = 16 y = 6 }}
				pdx_tooltip = "DD_TOPBAR_ECON_TT"
			}}

			instantTextboxType = {{
				name = "dd_market_cash"
				position = {{ x = 42 y = 7 }}
				font = "hoi_18mbs"
				text = "DD_ARMS_MARKET_CASH"
				maxWidth = 480
				maxHeight = 18
				format = left
				pdx_tooltip = "DD_TOPBAR_ECON_TT"
			}}
		}}

		iconType = {{
			name = "dd_tabs_background"
			quadTextureSprite = "GFX_tab_diplomacy_bg"
			position = {{ x = 15 y = 184 }}
			alwaystransparent = yes
		}}

		buttonType = {{
			name = "dd_tab_buy_on"
			quadTextureSprite = "GFX_Access_&_buy_equipment"
			position = {{ x = 15 y = 80 }}
			buttonText = "DD_MARKET_TAB_BUY"
			font = "hoi_18mbs"
			frame = 2
			clicksound = click_default
		}}
		buttonType = {{
			name = "dd_tab_buy_off"
			quadTextureSprite = "GFX_Access_&_buy_equipment"
			position = {{ x = 15 y = 80 }}
			buttonText = "DD_MARKET_TAB_BUY"
			font = "hoi_18mbs"
			frame = 1
			clicksound = click_default
		}}

		buttonType = {{
			name = "dd_tab_sell_on"
			quadTextureSprite = "GFX_Add_equipment_to_markete"
			position = {{ x = 275 y = 80 }}
			buttonText = "DD_MARKET_TAB_SELL"
			font = "hoi_18mbs"
			frame = 2
			clicksound = click_default
		}}
		buttonType = {{
			name = "dd_tab_sell_off"
			quadTextureSprite = "GFX_Add_equipment_to_markete"
			position = {{ x = 275 y = 80 }}
			buttonText = "DD_MARKET_TAB_SELL"
			font = "hoi_18mbs"
			frame = 1
			clicksound = click_default
		}}

		buttonType = {{
			name = "dd_cat_land_on"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 15 y = 186 }}
			buttonText = "DD_MARKET_CAT_LAND"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 2
		}}
		buttonType = {{
			name = "dd_cat_land_off"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 15 y = 186 }}
			buttonText = "DD_MARKET_CAT_LAND"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 1
		}}
		buttonType = {{
			name = "dd_cat_air_on"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 148 y = 186 }}
			buttonText = "DD_MARKET_CAT_AIR"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 2
		}}
		buttonType = {{
			name = "dd_cat_air_off"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 148 y = 186 }}
			buttonText = "DD_MARKET_CAT_AIR"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 1
		}}
		buttonType = {{
			name = "dd_cat_navy_on"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 281 y = 186 }}
			buttonText = "DD_MARKET_CAT_NAVY"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 2
		}}
		buttonType = {{
			name = "dd_cat_navy_off"
			quadTextureSprite = "GFX_diplo_filter_entry"
			position = {{ x = 281 y = 186 }}
			buttonText = "DD_MARKET_CAT_NAVY"
			font = "hoi_16mbs"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
			frame = 1
		}}
	}}
{lists}
}}
"""
    (ROOT / "interface" / "doomsday_market.gui").write_text(text, encoding="utf-8")


def effect_block(row: dict) -> str:
    slug = row["slug"]
    buy_need = row["buy"] - 0.01
    sell_have = row["amount"] - 1
    return f"""
dd_buy_{slug} = {{
	if = {{
		limit = {{ check_variable = {{ treasury > {buy_need} }} }}
		subtract_from_variable = {{ treasury = {row['buy']} }}
		add_equipment_to_stockpile = {{
			type = {row['buy_type']}
			amount = {row['amount']}
			producer = ROOT
		}}
		dd_refresh_market_counts = yes
		dd_refresh_loan_preview = yes
	}}
}}

dd_sell_{slug} = {{
	if = {{
		limit = {{ has_equipment = {{ {row['arch']} > {sell_have} }} }}
		add_equipment_to_stockpile = {{
			type = {row['arch']}
			amount = -{row['amount']}
		}}
		add_to_variable = {{ treasury = {row['sell']} }}
		dd_refresh_market_counts = yes
		dd_refresh_loan_preview = yes
	}}
}}
"""


def write_effects(rows: list[dict]) -> None:
    counts = "\n".join(
        f"\tset_variable = {{ dd_stock_{r['slug']} = num_equipment@{r['arch']} }}"
        for r in rows
    )
    body = "# Generated. Fixed prices. Host and clients must never disagree.\n"
    body += "\n".join(effect_block(r).rstrip() for r in rows)
    (ROOT / "common" / "scripted_effects" / "doomsday_market.txt").write_text(
        body + "\n", encoding="utf-8"
    )
    econ = ROOT / "common" / "scripted_effects" / "doomsday_economy.txt"
    text = econ.read_text(encoding="utf-8")
    new_fn = "dd_refresh_market_counts = {\n" + counts + "\n}\n"
    text = re.sub(
        r"dd_refresh_market_counts = \{.*?\n\}",
        new_fn.rstrip(),
        text,
        count=1,
        flags=re.S,
    )
    econ.write_text(text, encoding="utf-8")


def row_clicks(rows: list[dict]) -> tuple[str, str]:
    effects = []
    triggers = []
    for r in rows:
        slug = r["slug"]
        buy_need = r["buy"] - 0.01
        sell_have = r["amount"] - 1
        effects.append(f"			dd_buy_{slug}_click = {{ dd_buy_{slug} = yes }}")
        effects.append(f"			dd_sell_{slug}_click = {{ dd_sell_{slug} = yes }}")
        triggers.append(
            f"""			dd_{slug}_buy_price_visible = {{
				NOT = {{ has_country_flag = dd_market_sell_tab }}
			}}
			dd_{slug}_sell_price_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_buy_{slug}_visible = {{
				NOT = {{ has_country_flag = dd_market_sell_tab }}
			}}
			dd_sell_{slug}_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_buy_{slug}_click_enabled = {{ check_variable = {{ treasury > {buy_need} }} }}
			dd_sell_{slug}_click_enabled = {{ has_equipment = {{ {r['arch']} > {sell_have} }} }}"""
        )
    return "\n".join(effects), "\n".join(triggers)


def list_visible(cat: str) -> str:
    if cat == "land":
        return """			has_country_flag = dd_show_arms_market
			NOT = { has_country_flag = dd_market_air_tab }
			NOT = { has_country_flag = dd_market_navy_tab }"""
    if cat == "air":
        return """			has_country_flag = dd_show_arms_market
			has_country_flag = dd_market_air_tab"""
    return """			has_country_flag = dd_show_arms_market
			has_country_flag = dd_market_navy_tab"""


def write_scripted_gui(rows: list[dict]) -> None:
    by_cat = {c: [r for r in rows if r["cat"] == c] for c in ("land", "air", "navy")}
    list_uis = []
    for cat in ("land", "air", "navy"):
        effects, triggers = row_clicks(by_cat[cat])
        list_uis.append(
            f"""
	dd_market_list_{cat}_ui = {{
		context_type = player_context
		parent_window_name = dd_arms_market_window
		window_name = "dd_market_list_{cat}"
		visible = {{
{list_visible(cat)}
		}}

		effects = {{
{effects}
		}}

		triggers = {{
{triggers}
		}}
	}}"""
        )
    text = f"""scripted_gui = {{

	doomsday_economy_ui = {{
		context_type = decision_category
		window_name = "doomsday_economy_window"

		effects = {{
			dd_open_market_click = {{
				set_country_flag = dd_show_arms_market
				clr_country_flag = dd_market_sell_tab
				clr_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
				dd_refresh_market_counts = yes
				dd_refresh_loan_preview = yes
			}}
		}}
	}}

	dd_arms_market_ui = {{
		context_type = player_context
		window_name = "dd_arms_market_window"
		visible = {{
			has_country_flag = dd_show_arms_market
		}}

		effects = {{
			dd_close_market_click = {{
				clr_country_flag = dd_show_arms_market
				clr_country_flag = dd_market_sell_tab
				clr_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
			}}
			dd_tab_buy_on_click = {{ clr_country_flag = dd_market_sell_tab }}
			dd_tab_buy_off_click = {{ clr_country_flag = dd_market_sell_tab }}
			dd_tab_sell_on_click = {{ set_country_flag = dd_market_sell_tab }}
			dd_tab_sell_off_click = {{ set_country_flag = dd_market_sell_tab }}
			dd_cat_land_on_click = {{
				clr_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
			}}
			dd_cat_land_off_click = {{
				clr_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
			}}
			dd_cat_air_on_click = {{
				set_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
			}}
			dd_cat_air_off_click = {{
				set_country_flag = dd_market_air_tab
				clr_country_flag = dd_market_navy_tab
			}}
			dd_cat_navy_on_click = {{
				clr_country_flag = dd_market_air_tab
				set_country_flag = dd_market_navy_tab
			}}
			dd_cat_navy_off_click = {{
				clr_country_flag = dd_market_air_tab
				set_country_flag = dd_market_navy_tab
			}}
		}}

		triggers = {{
			dd_tab_buy_on_visible = {{
				NOT = {{ has_country_flag = dd_market_sell_tab }}
			}}
			dd_tab_buy_off_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_tab_sell_on_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_tab_sell_off_visible = {{
				NOT = {{ has_country_flag = dd_market_sell_tab }}
			}}
			dd_cat_land_on_visible = {{
				NOT = {{ has_country_flag = dd_market_air_tab }}
				NOT = {{ has_country_flag = dd_market_navy_tab }}
			}}
			dd_cat_land_off_visible = {{
				OR = {{
					has_country_flag = dd_market_air_tab
					has_country_flag = dd_market_navy_tab
				}}
			}}
			dd_cat_air_on_visible = {{
				has_country_flag = dd_market_air_tab
			}}
			dd_cat_air_off_visible = {{
				NOT = {{ has_country_flag = dd_market_air_tab }}
			}}
			dd_cat_navy_on_visible = {{
				has_country_flag = dd_market_navy_tab
			}}
			dd_cat_navy_off_visible = {{
				NOT = {{ has_country_flag = dd_market_navy_tab }}
			}}
		}}
	}}
{"".join(list_uis)}

	dd_topbar_econ = {{
		context_type = player_context
		parent_window_token = top_bar
		window_name = "dd_topbar_econ_window"
		visible = {{
			always = yes
		}}
		triggers = {{
			dd_net_up_visible = {{
				check_variable = {{ dd_last_net > -0.005 }}
			}}
			dd_net_down_visible = {{
				check_variable = {{ dd_last_net < 0 }}
			}}
			dd_net_pos_visible = {{
				check_variable = {{ dd_last_net > -0.005 }}
			}}
			dd_net_neg_visible = {{
				check_variable = {{ dd_last_net < 0 }}
			}}
		}}
	}}
}}
"""
    (ROOT / "common" / "scripted_guis" / "doomsday_economy.txt").write_text(text, encoding="utf-8")


def write_loc(rows: list[dict]) -> None:
    lines = ["l_english:"]
    lines.append(' DD_MARKET_CAT_LAND:0 "Land"')
    lines.append(' DD_MARKET_CAT_AIR:0 "Air"')
    lines.append(' DD_MARKET_CAT_NAVY:0 "Navy"')
    for r in rows:
        u = r["slug"].upper()
        lines.append(f' DD_MARKET_NAME_{u}:0 "${r["arch"]}$"')
        lines.append(f' DD_MARKET_STOCK_{u}:0 "Stockpile: [?dd_stock_{r["slug"]}|0]"')
        lines.append(f' DD_MARKET_PRICE_{u}_BUY:0 "{r["buy"]}B  ({r["amount"]} units)"')
        lines.append(f' DD_MARKET_PRICE_{u}_SELL:0 "{r["sell"]}B  ({r["amount"]} units)"')
        lines.append(
            f' DD_BUY_{u}_TT:0 "Buy {r["amount"]} ${r["arch"]}$ for {r["buy"]}B US dollars."'
        )
        lines.append(
            f' DD_SELL_{u}_TT:0 "Sell {r["amount"]} ${r["arch"]}$ for {r["sell"]}B US dollars."'
        )
    path = ROOT / "localisation" / "english" / "doomsday_market_l_english.yml"
    path.write_bytes("\ufeff".encode("utf-8") + ("\n".join(lines) + "\n").encode("utf-8"))


def main() -> None:
    rows = catalog()
    print("rows", len(rows), {c: sum(1 for r in rows if r["cat"] == c) for c in ("land", "air", "navy")})
    for r in rows:
        print(f"  {r['cat']:4} {r['slug']:42} buy {r['buy']:4} x{r['amount']:<3} {r['buy_type']}")
    write_gui(rows)
    write_effects(rows)
    write_scripted_gui(rows)
    write_loc(rows)


if __name__ == "__main__":
    main()
