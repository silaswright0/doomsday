"""Generate treasury Arms Market rows, one per equipment variant."""
from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EQ = ROOT / "common" / "units" / "equipment"
SKIP_DIRS = {"modules", "upgrades"}
SKIP_FILES = {"plane_filters.txt", "tank_filters.txt", "x_plane_airframes.txt", "x_tank_chassis.txt"}
SKIP_ARCH = {"mothership_equipment"}

# Cash asks are integer billions. build_cost_ic × lot / 50 lands a current rifle
# battalion near 15B and a fleet carrier near 90B. USA starts near 615B, a
# mid power near 30B. The old divisor (7, newest model only) priced a
# battleship above 1800B, past both the ask cap and US cash.
PRICE_DIVISOR = 50
# One world record per (model, price). Same price adds to that record.
LIST_MAX = 96
LOT_MAX = 128
CAT_ID = {"land": 0, "air": 1, "navy": 2}

# World pool seed, in lots (lot size × this). Floor kit only; nukes/ships stay at 0.
# Applied to the newest model with year <= 2026, not to every level.
SEED_LOTS = {
    "infantry_equipment": 40,
    "support_equipment": 12,
    "artillery_equipment": 15,
    "anti_air_equipment": 12,
    "anti_tank_equipment": 12,
    "motorized_equipment": 20,
    "mechanized_equipment": 12,
    "armored_car_equipment": 10,
    "light_tank_chassis": 10,
    "medium_tank_chassis": 12,
    "modern_tank_chassis": 12,
    "rocket_artillery_equipment": 8,
    "train_equipment": 8,
    "motorbike_equipment": 10,
    "helicopter_equipment": 8,
    "recon_uav_equipment": 10,
    "small_plane_airframe": 12,
    "transport_plane_equipment": 8,
    "convoy": 25,
}

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
                        "parent": first(r"parent\s*=\s*(\S+)", content),
                        "picture": first(r"picture\s*=\s*(\S+)", content),
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


def slugify(name: str) -> str:
    return name.replace("equipment", "eq").replace("__", "_").strip("_")


def assign_family_prices(vs: list[dict], eff_ic, amount: int) -> dict[str, int]:
    """One price per variant. A model costs at least 1B more than the model it replaces."""
    byname = {v["name"]: v for v in vs}
    children: dict[str, list[str]] = {v["name"]: [] for v in vs}
    roots = []
    for v in vs:
        parent = v["parent"]
        if parent in byname and parent != v["name"]:
            children[parent].append(v["name"])
        else:
            roots.append(v["name"])
    used: set[int] = set()
    prices: dict[str, int] = {}

    def take(price: int) -> int:
        price = max(1, price)
        while price in used:
            price += 1
        used.add(price)
        return price

    def walk(name: str, seen: set[str]) -> None:
        if name in seen:
            return
        parent = byname[name]["parent"]
        floor = prices[parent] + 1 if parent in prices else 1
        raw = eff_ic(name) * amount
        base = max(floor, int(round(raw / PRICE_DIVISOR)))
        prices[name] = take(base)
        kids = sorted(children[name], key=lambda n: (eff_ic(n), byname[n]["year"], n))
        nxt = seen | {name}
        for kid in kids:
            walk(kid, nxt)

    for name in sorted(roots, key=lambda n: (byname[n]["year"], eff_ic(n), n)):
        walk(name, set())
    return prices


def catalog() -> list[dict]:
    archetypes, variants = parse()
    rows = []
    used_slugs: set[str] = set()
    for arch, info in archetypes.items():
        if arch in SKIP_ARCH:
            continue
        vs = variants.get(arch, [])
        if not vs:
            continue
        dedup = {}
        for v in vs:
            dedup[v["name"]] = v
        vs = list(dedup.values())
        cat = category(info["iface"], arch)
        byname = {v["name"]: v for v in vs}

        def eff_ic(name: str, seen: set[str] | None = None) -> float:
            seen = seen or set()
            if name in seen or name not in byname:
                return info["ic"] or default_ic(cat, arch)
            seen = seen | {name}
            v = byname[name]
            if v["ic"]:
                return v["ic"]
            if v["parent"]:
                return eff_ic(v["parent"], seen)
            return info["ic"] or default_ic(cat, arch)

        amount = lot_size(cat, arch)
        prices = assign_family_prices(vs, eff_ic, amount)
        seed_name = None
        if arch in SEED_LOTS:
            pool = [v for v in vs if v["year"] <= 2026] or vs
            top_ic = max(eff_ic(v["name"]) for v in pool)
            # Latest service model, ignoring a cheap sidegrade that shares the family.
            main = [v for v in pool if eff_ic(v["name"]) >= top_ic * 0.5] or pool
            seed_name = max(main, key=lambda v: (v["year"], eff_ic(v["name"]), v["name"]))["name"]
        for v in vs:
            base = slugify(v["name"])
            slug = base
            n = 2
            while slug in used_slugs:
                slug = f"{base}_{n}"
                n += 1
            used_slugs.add(slug)
            sprite, scale = sprite_for(arch, v["picture"] or info["picture"])
            buy = prices[v["name"]]
            rows.append(
                {
                    "arch": arch,
                    "variant": v["name"],
                    "year": v["year"],
                    "buy_type": v["name"],
                    "slug": slug,
                    "cat": cat,
                    "amount": amount,
                    "buy": buy,
                    "sell": buy,
                    "sprite": sprite,
                    "scale": scale,
                    "seed": SEED_LOTS.get(arch, 0) * amount if v["name"] == seed_name else 0,
                }
            )
    order = {"land": 0, "air": 1, "navy": 2}
    rows.sort(key=lambda r: (order[r["cat"]], r["arch"], r["year"], r["variant"]))
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
					position = {{ x = 360 y = 18 }}
					clicksound = click_default
					pdx_tooltip = "DD_BUY_{slug.upper()}_TT"
				}}
				buttonType = {{
					name = "dd_sell_{slug}"
					quadTextureSprite = "GFX_diplo_filter_entry"
					buttonText = "DD_MARKET_SELL"
					buttonFont = "hoi_16mbs"
					position = {{ x = 360 y = 18 }}
					clicksound = click_default
					pdx_tooltip = "DD_SELL_{slug.upper()}_TT"
				}}
				buttonType = {{
					name = "dd_ask_down_{slug}"
					quadTextureSprite = "GFX_diplo_filter_entry"
					buttonText = "DD_MARKET_ASK_DOWN"
					buttonFont = "hoi_16mbs"
					position = {{ x = 268 y = 58 }}
					clicksound = click_default
					pdx_tooltip = "DD_ASK_DOWN_TT"
				}}
				buttonType = {{
					name = "dd_ask_up_{slug}"
					quadTextureSprite = "GFX_diplo_filter_entry"
					buttonText = "DD_MARKET_ASK_UP"
					buttonFont = "hoi_16mbs"
					position = {{ x = 360 y = 58 }}
					clicksound = click_default
					pdx_tooltip = "DD_ASK_UP_TT"
				}}
			}}"""


def list_gui(cat: str, rows: list[dict]) -> str:
    entries = []
    y = 8
    prev_hull = False
    for row in rows:
        entries.append(entry_gui(row, y))
        hull = "hull" in row["arch"]
        # Hull cards sit a little closer together than the other rows.
        step = 96 if hull and prev_hull else 104
        prev_hull = hull
        y += step
    inner = "\n".join(entries)
    # Independent windows. Nested lists ignore _visible, so navy sat on top.
    return f"""
	containerWindowType = {{
		name = "dd_market_list_{cat}"
		position = {{ x = 10 y = 210 }}
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
		name = "dd_arms_dismiss_window"
		position = {{ x = 0 y = 0 }}
		size = {{ width = 100% height = 100% }}
		clipping = no

		buttonType = {{
			name = "dd_arms_dismiss"
			position = {{ x = 0 y = 0 }}
			size = {{ width = 100% height = 100% }}
			quadTextureSprite = "GFX_tiled_window_transparent"
			clicksound = click_close
		}}
	}}

	containerWindowType = {{
		name = "dd_arms_market_window"
		# decision_tab already starts at the decisions panel. y=44 sits under that title; 100%% fills the rest.
		position = {{ x = 0 y = 44 }}
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

		# Direct children (a nested container collapsed these to nothing). Sprites are 1-frame.
		buttonType = {{
			name = "dd_tab_buy_on"
			quadTextureSprite = "GFX_button_261x34"
			position = {{ x = 14 y = 86 }}
			size = {{ width = 261 height = 34 }}
			buttonText = "DD_MARKET_TAB_BUY_ON"
			buttonFont = "hoi_18mbs"
			clicksound = click_default
		}}
		buttonType = {{
			name = "dd_tab_buy_off"
			quadTextureSprite = "GFX_button_261x34"
			position = {{ x = 14 y = 86 }}
			size = {{ width = 261 height = 34 }}
			buttonText = "DD_MARKET_TAB_BUY_OFF"
			buttonFont = "hoi_18mbs"
			clicksound = click_default
		}}
		buttonType = {{
			name = "dd_tab_sell_on"
			quadTextureSprite = "GFX_button_261x34"
			position = {{ x = 275 y = 86 }}
			size = {{ width = 261 height = 34 }}
			buttonText = "DD_MARKET_TAB_SELL_ON"
			buttonFont = "hoi_18mbs"
			clicksound = click_default
		}}
		buttonType = {{
			name = "dd_tab_sell_off"
			quadTextureSprite = "GFX_button_261x34"
			position = {{ x = 275 y = 86 }}
			size = {{ width = 261 height = 34 }}
			buttonText = "DD_MARKET_TAB_SELL_OFF"
			buttonFont = "hoi_18mbs"
			clicksound = click_default
		}}

		# Centered Land / Air / Navy (123px + 16px gaps, group centered in 550)
		buttonType = {{
			name = "dd_cat_land_on"
			quadTextureSprite = "GFX_button_123x34"
			position = {{ x = 75 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_LAND_ON"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
		buttonType = {{
			name = "dd_cat_land_off"
			quadTextureSprite = "GFX_button_123x34_gray"
			position = {{ x = 75 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_LAND"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
		buttonType = {{
			name = "dd_cat_air_on"
			quadTextureSprite = "GFX_button_123x34"
			position = {{ x = 214 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_AIR_ON"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
		buttonType = {{
			name = "dd_cat_air_off"
			quadTextureSprite = "GFX_button_123x34_gray"
			position = {{ x = 214 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_AIR"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
		buttonType = {{
			name = "dd_cat_navy_on"
			quadTextureSprite = "GFX_button_123x34"
			position = {{ x = 353 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_NAVY_ON"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
		buttonType = {{
			name = "dd_cat_navy_off"
			quadTextureSprite = "GFX_button_123x34_gray"
			position = {{ x = 353 y = 126 }}
			size = {{ width = 123 height = 34 }}
			buttonText = "DD_MARKET_CAT_NAVY"
			buttonFont = "hoi_16mbs"
			clicksound = click_scroll
		}}
	}}
{lists}
}}
"""
    (ROOT / "interface" / "doomsday_market.gui").write_text(text, encoding="utf-8")


def effect_block(row: dict) -> str:
    slug = row["slug"]
    sell_have = row["amount"] - 1
    pool_have = row["amount"] - 1
    mine = f"dd_my_ask_{slug}"
    pool = f"global.dd_pool_{slug}"
    return f"""
dd_buy_all_{slug} = {{
		set_temp_variable = {{ dd_i = global.dd_active_list }}
		set_temp_variable = {{ dd_price = global.dd_list_price^dd_i }}
		set_temp_variable = {{ dd_qty = global.dd_list_qty^dd_i }}
		set_temp_variable = {{ dd_cat = global.dd_list_cat^dd_i }}
		set_temp_variable = {{ dd_idx = global.dd_list_idx^dd_i }}
		if = {{
			limit = {{
				check_variable = {{ dd_cat = {row['cat_id']} }}
				check_variable = {{ dd_idx = {row['idx']} }}
				check_variable = {{ dd_price > 0 }}
				NOT = {{ check_variable = {{ treasury < dd_price }} }}
				check_variable = {{ dd_qty > {pool_have} }}
				check_variable = {{ {pool} > {pool_have} }}
			}}
			set_variable = {{ global.dd_pay_amt = dd_price }}
			set_variable = {{ global.dd_div_n = dd_qty }}
			set_variable = {{ global.dd_div_d = {row['amount']} }}
			dd_floor_div = yes
			set_variable = {{ global.dd_bulk_lots = global.dd_div_q }}
			set_variable = {{ global.dd_div_n = {pool} }}
			set_variable = {{ global.dd_div_d = {row['amount']} }}
			dd_floor_div = yes
			if = {{
				limit = {{ check_variable = {{ global.dd_div_q < global.dd_bulk_lots }} }}
				set_variable = {{ global.dd_bulk_lots = global.dd_div_q }}
			}}
			set_variable = {{ global.dd_div_n = treasury }}
			set_variable = {{ global.dd_div_d = global.dd_pay_amt }}
			dd_floor_div = yes
			if = {{
				limit = {{ check_variable = {{ global.dd_div_q < global.dd_bulk_lots }} }}
				set_variable = {{ global.dd_bulk_lots = global.dd_div_q }}
			}}
			if = {{
				limit = {{ check_variable = {{ global.dd_bulk_lots > 0 }} }}
				set_variable = {{ global.dd_pay_qty = {row['amount']} }}
				set_variable = {{ global.dd_pay_cost = global.dd_pay_amt }}
				multiply_variable = {{ global.dd_pay_cost = global.dd_bulk_lots }}
				set_variable = {{ global.dd_pay_units = global.dd_pay_qty }}
				multiply_variable = {{ global.dd_pay_units = global.dd_bulk_lots }}
				subtract_from_variable = {{ treasury = global.dd_pay_cost }}
				dd_pay_bulk = yes
				set_temp_variable = {{ dd_i = global.dd_active_list }}
				subtract_from_variable = {{ global.dd_list_qty^dd_i = global.dd_pay_units }}
				subtract_from_variable = {{ {pool} = global.dd_pay_units }}
				if = {{
					limit = {{ check_variable = {{ global.dd_list_qty^dd_i < 1 }} }}
					set_variable = {{ global.dd_list_cat^dd_i = -1 }}
					set_variable = {{ global.dd_list_qty^dd_i = 0 }}
					set_variable = {{ global.dd_list_price^dd_i = 0 }}
				}}
				add_equipment_to_stockpile = {{
					type = {row['buy_type']}
					amount = global.dd_pay_units
					producer = ROOT
				}}
				dd_refresh_market_counts = yes
				dd_refresh_loan_preview = yes
			}}
		}}
}}

dd_buy_{slug} = {{
		set_temp_variable = {{ dd_i = global.dd_active_list }}
		set_temp_variable = {{ dd_price = global.dd_list_price^dd_i }}
		set_temp_variable = {{ dd_qty = global.dd_list_qty^dd_i }}
		set_temp_variable = {{ dd_cat = global.dd_list_cat^dd_i }}
		set_temp_variable = {{ dd_idx = global.dd_list_idx^dd_i }}
		if = {{
			limit = {{
				check_variable = {{ dd_cat = {row['cat_id']} }}
				check_variable = {{ dd_idx = {row['idx']} }}
				NOT = {{ check_variable = {{ treasury < dd_price }} }}
				check_variable = {{ dd_qty > {pool_have} }}
				check_variable = {{ {pool} > {pool_have} }}
			}}
			subtract_from_variable = {{ treasury = dd_price }}
			set_variable = {{ global.dd_pay_amt = dd_price }}
			set_variable = {{ global.dd_pay_qty = {row['amount']} }}
			dd_pay_front_seller = yes
			set_temp_variable = {{ dd_i = global.dd_active_list }}
			subtract_from_variable = {{ global.dd_list_qty^dd_i = {row['amount']} }}
			subtract_from_variable = {{ {pool} = {row['amount']} }}
			if = {{
				limit = {{ check_variable = {{ global.dd_list_qty^dd_i < 1 }} }}
				set_variable = {{ global.dd_list_cat^dd_i = -1 }}
				set_variable = {{ global.dd_list_qty^dd_i = 0 }}
				set_variable = {{ global.dd_list_price^dd_i = 0 }}
			}}
			add_equipment_to_stockpile = {{
				type = {row['buy_type']}
				amount = {row['amount']}
				producer = ROOT
			}}
			dd_refresh_market_counts = yes
			dd_refresh_loan_preview = yes
		}}
}}

dd_sell_all_{slug} = {{
	if = {{
		limit = {{ check_variable = {{ {mine} < 1 }} }}
		set_variable = {{ {mine} = {row['buy']} }}
	}}
	if = {{
		limit = {{
			has_equipment = {{ {row['variant']} > {sell_have} }}
			check_variable = {{ {mine} > 0 }}
		}}
			set_variable = {{ global.dd_div_n = num_equipment@{row['variant']} }}
			set_variable = {{ global.dd_div_d = {row['amount']} }}
			dd_floor_div = yes
			if = {{
				limit = {{ check_variable = {{ global.dd_div_q > 0 }} }}
				set_variable = {{ global.dd_pay_units = global.dd_div_q }}
				multiply_variable = {{ global.dd_pay_units = {row['amount']} }}
				set_variable = {{ global.dd_post_cat = {row['cat_id']} }}
				set_variable = {{ global.dd_post_idx = {row['idx']} }}
				set_variable = {{ global.dd_post_price = {mine} }}
				set_variable = {{ global.dd_post_amt = {row['amount']} }}
				set_variable = {{ global.dd_post_qty = global.dd_pay_units }}
				dd_post_listing = yes
				if = {{
					limit = {{ check_variable = {{ global.dd_post_ok = 1 }} }}
					dd_enqueue_seller = yes
					if = {{
						limit = {{ check_variable = {{ global.dd_enqueue_ok = 1 }} }}
						set_variable = {{ global.dd_pay_units = 0 }}
						subtract_from_variable = {{ global.dd_pay_units = global.dd_post_qty }}
						add_equipment_to_stockpile = {{
							type = {row['variant']}
							amount = global.dd_pay_units
						}}
						add_to_variable = {{ {pool} = global.dd_post_qty }}
						dd_refresh_market_counts = yes
						dd_refresh_loan_preview = yes
					}}
					else = {{
						dd_unpost_lot = yes
					}}
				}}
			}}
		}}
}}

dd_sell_{slug} = {{
	if = {{
		limit = {{ check_variable = {{ {mine} < 1 }} }}
		set_variable = {{ {mine} = {row['buy']} }}
	}}
	if = {{
		limit = {{
			has_equipment = {{ {row['variant']} > {sell_have} }}
			check_variable = {{ {mine} > 0 }}
		}}
		set_variable = {{ global.dd_post_cat = {row['cat_id']} }}
		set_variable = {{ global.dd_post_idx = {row['idx']} }}
		set_variable = {{ global.dd_post_price = {mine} }}
		set_variable = {{ global.dd_post_amt = {row['amount']} }}
		set_variable = {{ global.dd_post_qty = {row['amount']} }}
		dd_post_listing = yes
		if = {{
			limit = {{ check_variable = {{ global.dd_post_ok = 1 }} }}
			dd_enqueue_seller = yes
			if = {{
				limit = {{ check_variable = {{ global.dd_enqueue_ok = 1 }} }}
				add_equipment_to_stockpile = {{
					type = {row['variant']}
					amount = -{row['amount']}
				}}
				add_to_variable = {{ {pool} = {row['amount']} }}
				dd_refresh_market_counts = yes
				dd_refresh_loan_preview = yes
			}}
			else = {{
				dd_unpost_lot = yes
			}}
		}}
	}}
}}

dd_ask_up_{slug} = {{
	if = {{
		limit = {{
			has_equipment = {{ {row['variant']} > 0 }}
			check_variable = {{ {mine} > 0 }}
			check_variable = {{ {mine} < 999 }}
		}}
		add_to_variable = {{ {mine} = 1 }}
		dd_refresh_buy_slots = yes
	}}
}}

dd_ask_down_{slug} = {{
	if = {{
		limit = {{
			has_equipment = {{ {row['variant']} > 0 }}
			check_variable = {{ {mine} > 1 }}
		}}
		subtract_from_variable = {{ {mine} = 1 }}
		dd_refresh_buy_slots = yes
	}}
}}
"""


def listing_book() -> str:
    return f"""
dd_clear_listings = {{
	set_temp_variable = {{ dd_i = 0 }}
	while_loop_effect = {{
		limit = {{ check_variable = {{ dd_i < {LIST_MAX} }} }}
		set_variable = {{ global.dd_list_cat^dd_i = -1 }}
		set_variable = {{ global.dd_list_idx^dd_i = -1 }}
		set_variable = {{ global.dd_list_price^dd_i = 0 }}
		set_variable = {{ global.dd_list_qty^dd_i = 0 }}
		set_variable = {{ global.dd_list_amt^dd_i = 0 }}
		add_to_temp_variable = {{ dd_i = 1 }}
	}}
	set_temp_variable = {{ dd_i = 0 }}
	while_loop_effect = {{
		limit = {{ check_variable = {{ dd_i < {LOT_MAX} }} }}
		set_variable = {{ global.dd_lot_qty^dd_i = 0 }}
		set_variable = {{ global.dd_lot_list^dd_i = -1 }}
		set_variable = {{ global.dd_lot_seq^dd_i = 0 }}
		add_to_temp_variable = {{ dd_i = 1 }}
	}}
	set_variable = {{ global.dd_lot_next = 1 }}
}}

# Merge into the record with this model and price, or open a new one.
dd_post_listing = {{
	set_variable = {{ global.dd_post_ok = 0 }}
	set_variable = {{ global.dd_post_at = -1 }}
	set_temp_variable = {{ dd_i = 0 }}
	set_temp_variable = {{ dd_found = -1 }}
	set_temp_variable = {{ dd_empty = -1 }}
	while_loop_effect = {{
		limit = {{
			check_variable = {{ dd_i < {LIST_MAX} }}
			check_variable = {{ dd_found < 0 }}
		}}
		set_temp_variable = {{ dd_cat = global.dd_list_cat^dd_i }}
		set_temp_variable = {{ dd_idx = global.dd_list_idx^dd_i }}
		set_temp_variable = {{ dd_pr = global.dd_list_price^dd_i }}
		set_temp_variable = {{ dd_q = global.dd_list_qty^dd_i }}
		if = {{
			limit = {{
				check_variable = {{ dd_q > 0 }}
				check_variable = {{ dd_cat = global.dd_post_cat }}
				check_variable = {{ dd_idx = global.dd_post_idx }}
				check_variable = {{ dd_pr = global.dd_post_price }}
			}}
			set_temp_variable = {{ dd_found = dd_i }}
		}}
		if = {{
			limit = {{
				check_variable = {{ dd_empty < 0 }}
				check_variable = {{ dd_q < 1 }}
			}}
			set_temp_variable = {{ dd_empty = dd_i }}
		}}
		add_to_temp_variable = {{ dd_i = 1 }}
	}}
	if = {{
		limit = {{ check_variable = {{ dd_found > -1 }} }}
		add_to_variable = {{ global.dd_list_qty^dd_found = global.dd_post_qty }}
		set_variable = {{ global.dd_post_at = dd_found }}
		set_variable = {{ global.dd_post_ok = 1 }}
	}}
	else_if = {{
		limit = {{ check_variable = {{ dd_empty > -1 }} }}
		set_variable = {{ global.dd_list_cat^dd_empty = global.dd_post_cat }}
		set_variable = {{ global.dd_list_idx^dd_empty = global.dd_post_idx }}
		set_variable = {{ global.dd_list_price^dd_empty = global.dd_post_price }}
		set_variable = {{ global.dd_list_qty^dd_empty = global.dd_post_qty }}
		set_variable = {{ global.dd_list_amt^dd_empty = global.dd_post_amt }}
		set_variable = {{ global.dd_post_at = dd_empty }}
		set_variable = {{ global.dd_post_ok = 1 }}
	}}
}}

# Undo the listing add when the seller queue cannot take another claim.
dd_unpost_lot = {{
	set_temp_variable = {{ dd_i = global.dd_post_at }}
	subtract_from_variable = {{ global.dd_list_qty^dd_i = global.dd_post_qty }}
	if = {{
		limit = {{ check_variable = {{ global.dd_list_qty^dd_i < 1 }} }}
		set_variable = {{ global.dd_list_cat^dd_i = -1 }}
		set_variable = {{ global.dd_list_idx^dd_i = -1 }}
		set_variable = {{ global.dd_list_price^dd_i = 0 }}
		set_variable = {{ global.dd_list_qty^dd_i = 0 }}
		set_variable = {{ global.dd_list_amt^dd_i = 0 }}
	}}
}}

# Remember who sold this lot. Same country selling again at the same price extends their latest claim.
dd_enqueue_seller = {{
	set_variable = {{ global.dd_enqueue_ok = 0 }}
	set_variable = {{ global.dd_pay_best = -1 }}
	set_variable = {{ global.dd_lot_empty = -1 }}
	set_temp_variable = {{ dd_tail_seq = -1 }}
	set_temp_variable = {{ dd_i = 0 }}
	while_loop_effect = {{
		limit = {{ check_variable = {{ dd_i < {LOT_MAX} }} }}
		set_temp_variable = {{ dd_q = global.dd_lot_qty^dd_i }}
		set_temp_variable = {{ dd_list = global.dd_lot_list^dd_i }}
		set_temp_variable = {{ dd_seq = global.dd_lot_seq^dd_i }}
		if = {{
			limit = {{
				check_variable = {{ dd_q > 0 }}
				check_variable = {{ dd_list = global.dd_post_at }}
			}}
			if = {{
				limit = {{ check_variable = {{ dd_seq > dd_tail_seq }} }}
				set_variable = {{ global.dd_pay_best = dd_i }}
				set_temp_variable = {{ dd_tail_seq = dd_seq }}
			}}
		}}
		if = {{
			limit = {{
				check_variable = {{ global.dd_lot_empty < 0 }}
				check_variable = {{ dd_q < 1 }}
			}}
			set_variable = {{ global.dd_lot_empty = dd_i }}
		}}
		add_to_temp_variable = {{ dd_i = 1 }}
	}}
	set_variable = {{ global.dd_same_seller = 0 }}
	if = {{
		limit = {{ check_variable = {{ global.dd_pay_best > -1 }} }}
		set_temp_variable = {{ dd_best = global.dd_pay_best }}
		set_variable = {{ global.dd_pay_who = global.dd_lot_who^dd_best }}
		var:global.dd_pay_who = {{
			if = {{
				limit = {{ tag = ROOT }}
				set_variable = {{ global.dd_same_seller = 1 }}
			}}
		}}
	}}
	if = {{
		limit = {{ check_variable = {{ global.dd_same_seller = 1 }} }}
		set_temp_variable = {{ dd_best = global.dd_pay_best }}
		add_to_variable = {{ global.dd_lot_qty^dd_best = global.dd_post_qty }}
		set_variable = {{ global.dd_enqueue_ok = 1 }}
	}}
	else_if = {{
		limit = {{ check_variable = {{ global.dd_lot_empty > -1 }} }}
		set_temp_variable = {{ dd_empty = global.dd_lot_empty }}
		set_variable = {{ global.dd_lot_list^dd_empty = global.dd_post_at }}
		set_variable = {{ global.dd_lot_qty^dd_empty = global.dd_post_qty }}
		set_variable = {{ global.dd_lot_seq^dd_empty = global.dd_lot_next }}
		set_variable = {{ global.dd_lot_who^dd_empty = THIS }}
		add_to_variable = {{ global.dd_lot_next = 1 }}
		set_variable = {{ global.dd_enqueue_ok = 1 }}
	}}
}}

# Pay the oldest seller of global.dd_active_list one lot.
# A dead seller's lot is still consumed. That cash is not paid to anyone.
# Starting stock has no seller, so that cash is not paid either.
dd_pay_front_seller = {{
	set_variable = {{ global.dd_paid = 0 }}
	set_variable = {{ global.dd_pay_guard = 0 }}
	while_loop_effect = {{
		limit = {{
			check_variable = {{ global.dd_paid = 0 }}
			check_variable = {{ global.dd_pay_guard < {LOT_MAX} }}
		}}
		add_to_variable = {{ global.dd_pay_guard = 1 }}
		set_variable = {{ global.dd_pay_best = -1 }}
		set_temp_variable = {{ dd_best_seq = 0 }}
		set_temp_variable = {{ dd_i = 0 }}
		while_loop_effect = {{
			limit = {{ check_variable = {{ dd_i < {LOT_MAX} }} }}
			set_temp_variable = {{ dd_q = global.dd_lot_qty^dd_i }}
			set_temp_variable = {{ dd_list = global.dd_lot_list^dd_i }}
			set_temp_variable = {{ dd_seq = global.dd_lot_seq^dd_i }}
			if = {{
				limit = {{
					check_variable = {{ dd_q > 0 }}
					check_variable = {{ dd_list = global.dd_active_list }}
				}}
				if = {{
					limit = {{ check_variable = {{ global.dd_pay_best < 0 }} }}
					set_variable = {{ global.dd_pay_best = dd_i }}
					set_temp_variable = {{ dd_best_seq = dd_seq }}
				}}
				else_if = {{
					limit = {{ check_variable = {{ dd_seq < dd_best_seq }} }}
					set_variable = {{ global.dd_pay_best = dd_i }}
					set_temp_variable = {{ dd_best_seq = dd_seq }}
				}}
			}}
			add_to_temp_variable = {{ dd_i = 1 }}
		}}
		if = {{
			limit = {{ check_variable = {{ global.dd_pay_best < 0 }} }}
			set_variable = {{ global.dd_paid = 1 }}
		}}
		else = {{
			set_temp_variable = {{ dd_best = global.dd_pay_best }}
			set_temp_variable = {{ dd_list = global.dd_active_list }}
			set_variable = {{ global.dd_sale_cat = global.dd_list_cat^dd_list }}
			set_variable = {{ global.dd_sale_idx = global.dd_list_idx^dd_list }}
			set_variable = {{ global.dd_pay_who = global.dd_lot_who^dd_best }}
			set_variable = {{ global.dd_seller_alive = 0 }}
			var:global.dd_pay_who = {{
				if = {{
					limit = {{ exists = yes }}
					set_variable = {{ global.dd_seller_alive = 1 }}
					add_to_variable = {{ treasury = global.dd_pay_amt }}
					set_variable = {{ dd_sale_paid = global.dd_pay_amt }}
					set_variable = {{ dd_sale_cat = global.dd_sale_cat }}
					set_variable = {{ dd_sale_idx = global.dd_sale_idx }}
					country_event = {{ id = doomsday_market.1 }}
				}}
			}}
			set_temp_variable = {{ dd_best = global.dd_pay_best }}
			subtract_from_variable = {{ global.dd_lot_qty^dd_best = global.dd_pay_qty }}
			set_variable = {{ global.dd_paid = 1 }}
			set_temp_variable = {{ dd_q = global.dd_lot_qty^dd_best }}
			if = {{
				limit = {{ check_variable = {{ dd_q < 1 }} }}
				set_variable = {{ global.dd_lot_qty^dd_best = 0 }}
				set_variable = {{ global.dd_lot_list^dd_best = -1 }}
				set_variable = {{ global.dd_lot_seq^dd_best = 0 }}
			}}
		}}
	}}
}}

# Floor of global.dd_div_n / global.dd_div_d. Result is global.dd_div_q.
dd_floor_div = {{
	set_temp_variable = {{ dd_q = global.dd_div_n }}
	divide_temp_variable = {{ dd_q = global.dd_div_d }}
	round_temp_variable = dd_q
	set_temp_variable = {{ dd_cost = dd_q }}
	multiply_temp_variable = {{ dd_cost = global.dd_div_d }}
	if = {{
		limit = {{ check_variable = {{ global.dd_div_n < dd_cost }} }}
		subtract_from_temp_variable = {{ dd_q = 1 }}
	}}
	if = {{
		limit = {{ check_variable = {{ dd_q < 1 }} }}
		set_temp_variable = {{ dd_q = 0 }}
	}}
	set_variable = {{ global.dd_div_q = dd_q }}
}}

# Pay global.dd_bulk_lots of the active listing. One popup per seller, for the whole sum.
# Lots with no living seller are still delivered. That cash is not paid to anyone.
dd_pay_bulk = {{
	set_temp_variable = {{ dd_list = global.dd_active_list }}
	set_variable = {{ global.dd_sale_cat = global.dd_list_cat^dd_list }}
	set_variable = {{ global.dd_sale_idx = global.dd_list_idx^dd_list }}
	set_variable = {{ global.dd_pay_guard = 0 }}
	while_loop_effect = {{
		limit = {{
			check_variable = {{ global.dd_bulk_lots > 0 }}
			check_variable = {{ global.dd_pay_guard < {LOT_MAX} }}
		}}
		add_to_variable = {{ global.dd_pay_guard = 1 }}
		set_variable = {{ global.dd_pay_best = -1 }}
		set_temp_variable = {{ dd_best_seq = 0 }}
		set_temp_variable = {{ dd_i = 0 }}
		while_loop_effect = {{
			limit = {{ check_variable = {{ dd_i < {LOT_MAX} }} }}
			set_temp_variable = {{ dd_q = global.dd_lot_qty^dd_i }}
			set_temp_variable = {{ dd_list = global.dd_lot_list^dd_i }}
			set_temp_variable = {{ dd_seq = global.dd_lot_seq^dd_i }}
			if = {{
				limit = {{
					check_variable = {{ dd_q > 0 }}
					check_variable = {{ dd_list = global.dd_active_list }}
				}}
				if = {{
					limit = {{ check_variable = {{ global.dd_pay_best < 0 }} }}
					set_variable = {{ global.dd_pay_best = dd_i }}
					set_temp_variable = {{ dd_best_seq = dd_seq }}
				}}
				else_if = {{
					limit = {{ check_variable = {{ dd_seq < dd_best_seq }} }}
					set_variable = {{ global.dd_pay_best = dd_i }}
					set_temp_variable = {{ dd_best_seq = dd_seq }}
				}}
			}}
			add_to_temp_variable = {{ dd_i = 1 }}
		}}
		if = {{
			limit = {{ check_variable = {{ global.dd_pay_best < 0 }} }}
			set_variable = {{ global.dd_bulk_lots = 0 }}
		}}
		else = {{
			set_temp_variable = {{ dd_best = global.dd_pay_best }}
			set_variable = {{ global.dd_div_n = global.dd_lot_qty^dd_best }}
			set_variable = {{ global.dd_div_d = global.dd_pay_qty }}
			dd_floor_div = yes
			set_variable = {{ global.dd_pay_take = global.dd_div_q }}
			if = {{
				limit = {{ check_variable = {{ global.dd_pay_take > global.dd_bulk_lots }} }}
				set_variable = {{ global.dd_pay_take = global.dd_bulk_lots }}
			}}
			if = {{
				limit = {{ check_variable = {{ global.dd_pay_take < 1 }} }}
				set_variable = {{ global.dd_lot_qty^dd_best = 0 }}
				set_variable = {{ global.dd_lot_list^dd_best = -1 }}
				set_variable = {{ global.dd_lot_seq^dd_best = 0 }}
			}}
			else = {{
				set_variable = {{ global.dd_sale_sum = global.dd_pay_amt }}
				multiply_variable = {{ global.dd_sale_sum = global.dd_pay_take }}
				set_variable = {{ global.dd_pay_units = global.dd_pay_qty }}
				multiply_variable = {{ global.dd_pay_units = global.dd_pay_take }}
				set_variable = {{ global.dd_pay_who = global.dd_lot_who^dd_best }}
				var:global.dd_pay_who = {{
					if = {{
						limit = {{ exists = yes }}
						add_to_variable = {{ treasury = global.dd_sale_sum }}
						set_variable = {{ dd_sale_paid = global.dd_sale_sum }}
						set_variable = {{ dd_sale_cat = global.dd_sale_cat }}
						set_variable = {{ dd_sale_idx = global.dd_sale_idx }}
						country_event = {{ id = doomsday_market.1 }}
					}}
				}}
				set_temp_variable = {{ dd_best = global.dd_pay_best }}
				subtract_from_variable = {{ global.dd_lot_qty^dd_best = global.dd_pay_units }}
				subtract_from_variable = {{ global.dd_bulk_lots = global.dd_pay_take }}
				set_temp_variable = {{ dd_q = global.dd_lot_qty^dd_best }}
				if = {{
					limit = {{ check_variable = {{ dd_q < 1 }} }}
					set_variable = {{ global.dd_lot_qty^dd_best = 0 }}
					set_variable = {{ global.dd_lot_list^dd_best = -1 }}
					set_variable = {{ global.dd_lot_seq^dd_best = 0 }}
				}}
			}}
		}}
	}}
}}
"""


def write_sale_loc(rows: list[dict]) -> None:
    lines = [
        "# Name of the shipment that just paid this country.",
        "defined_text = {",
        "	name = GetDdSaleShipment",
    ]
    for r in rows:
        lines.append("	text = {")
        lines.append("		trigger = {")
        lines.append(f"			check_variable = {{ dd_sale_cat = {r['cat_id']} }}")
        lines.append(f"			check_variable = {{ dd_sale_idx = {r['idx']} }}")
        lines.append("		}")
        lines.append(f"		localization_key = {r['variant']}")
        lines.append("	}")
    lines.append("	text = {")
    lines.append("		localization_key = DD_MARKET_SALE_UNKNOWN")
    lines.append("	}")
    lines.append("}")
    path = ROOT / "common" / "scripted_localisation" / "doomsday_market_sale.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_effects(rows: list[dict]) -> None:
    counts = []
    for cat in ("land", "air", "navy"):
        n = 0
        for r in rows:
            if r["cat"] != cat:
                continue
            r["cat_id"] = CAT_ID[cat]
            r["idx"] = n
            n += 1
    for r in rows:
        counts.append(
            f"\tif = {{\n"
            f"\t\tlimit = {{ check_variable = {{ dd_my_ask_{r['slug']} < 1 }} }}\n"
            f"\t\tset_variable = {{ dd_my_ask_{r['slug']} = {r['buy']} }}\n"
            f"\t}}"
        )
        counts.append(
            f"\tset_variable = {{ dd_stock_{r['slug']} = num_equipment@{r['variant']} }}"
        )
    init_lines = ["dd_init_market_pool = {"]
    init_lines.append("	if = {")
    init_lines.append("		limit = { NOT = { has_global_flag = dd_market_pool_v5 } }")
    init_lines.append("		set_global_flag = dd_market_pool_v5")
    init_lines.append("		dd_clear_listings = yes")
    init_lines.append("		set_temp_variable = { dd_n = 0 }")
    for r in rows:
        init_lines.append(
            f"		set_variable = {{ global.dd_ask_{r['slug']} = {r['buy']} }}"
        )
        init_lines.append(
            f"		set_variable = {{ global.dd_pool_{r['slug']} = {r['seed']} }}"
        )
        if r["seed"]:
            init_lines.append(f"		set_variable = {{ global.dd_list_cat^dd_n = {r['cat_id']} }}")
            init_lines.append(f"		set_variable = {{ global.dd_list_idx^dd_n = {r['idx']} }}")
            init_lines.append(f"		set_variable = {{ global.dd_list_price^dd_n = {r['buy']} }}")
            init_lines.append(f"		set_variable = {{ global.dd_list_qty^dd_n = {r['seed']} }}")
            init_lines.append(f"		set_variable = {{ global.dd_list_amt^dd_n = {r['amount']} }}")
            init_lines.append("		add_to_temp_variable = { dd_n = 1 }")
    init_lines.append("	}")
    init_lines.append("}")
    body = (
        "# Generated. One shared record per model and price. The earliest seller of that price is paid when a buyer takes a lot.\n"
    )
    body += listing_book()
    body += "\n".join(init_lines) + "\n"
    body += "\n".join(effect_block(r).rstrip() for r in rows)
    (ROOT / "common" / "scripted_effects" / "doomsday_market.txt").write_text(
        body + "\n", encoding="utf-8"
    )
    econ = ROOT / "common" / "scripted_effects" / "doomsday_economy.txt"
    text = econ.read_text(encoding="utf-8")
    new_fn = (
        "dd_refresh_market_counts = {\n" + "\n".join(counts) + "\n\tdd_refresh_buy_slots = yes\n}\n"
    )
    text = re.sub(
        r"dd_refresh_market_counts = \{.*?\n\}",
        new_fn.rstrip(),
        text,
        count=1,
        flags=re.S,
    )
    econ.write_text(text, encoding="utf-8")
    write_sale_loc(rows)


def row_clicks(rows: list[dict]) -> tuple[str, str]:
    effects = []
    triggers = []
    for r in rows:
        slug = r["slug"]
        sell_have = r["amount"] - 1
        pool_have = r["amount"] - 1
        ask = f"global.dd_ask_{slug}"
        pool = f"global.dd_pool_{slug}"
        effects.append(f"			dd_buy_{slug}_click = {{ dd_buy_{slug} = yes }}")
        effects.append(f"			dd_sell_{slug}_click = {{ dd_sell_{slug} = yes }}")
        effects.append(f"			dd_ask_up_{slug}_click = {{ dd_ask_up_{slug} = yes }}")
        effects.append(f"			dd_ask_down_{slug}_click = {{ dd_ask_down_{slug} = yes }}")
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
			dd_ask_up_{slug}_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_ask_down_{slug}_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_buy_{slug}_click_enabled = {{
				NOT = {{ check_variable = {{ treasury < {ask} }} }}
				check_variable = {{ {pool} > {pool_have} }}
			}}
			dd_sell_{slug}_click_enabled = {{ has_equipment = {{ {r['variant']} > {sell_have} }} }}
			dd_ask_up_{slug}_click_enabled = {{
				has_equipment = {{ {r['variant']} > 0 }}
				check_variable = {{ {ask} < 999 }}
			}}
			dd_ask_down_{slug}_click_enabled = {{
				has_equipment = {{ {r['variant']} > 0 }}
				check_variable = {{ {ask} > 1 }}
			}}"""
        )
    return "\n".join(effects), "\n".join(triggers)


def list_visible(cat: str) -> str:
    # Sell uses the packed slot list, and only for models you can spare a lot of.
    return "			always = no"


def write_scripted_gui(rows: list[dict]) -> None:
    """Sell-tab lists. Kept out of doomsday_economy.txt so the merc window stays."""
    by_cat = {c: [r for r in rows if r["cat"] == c] for c in ("land", "air", "navy")}
    list_uis = []
    for cat in ("land", "air", "navy"):
        effects, triggers = row_clicks(by_cat[cat])
        list_uis.append(
            f"""
	dd_market_list_{cat}_ui = {{
		context_type = player_context
		parent_window_token = decision_tab
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
    out = "scripted_gui = {\n" + "".join(list_uis) + "\n}\n"
    (ROOT / "common" / "scripted_guis" / "doomsday_market_lists.txt").write_text(
        out, encoding="utf-8"
    )
    econ_path = ROOT / "common" / "scripted_guis" / "doomsday_economy.txt"
    econ = econ_path.read_text(encoding="utf-8")
    cut_at = econ.find("\n\tdd_market_list_land_ui")
    topbar = econ.find("\n\tdd_topbar_econ")
    if cut_at != -1 and topbar != -1 and cut_at < topbar:
        econ_path.write_text(econ[:cut_at] + "\n" + econ[topbar:], encoding="utf-8")


def write_loc(rows: list[dict]) -> None:
    lines = ["l_english:"]
    lines.append(' DD_MARKET_CAT_LAND:0 "Land"')
    lines.append(' DD_MARKET_CAT_AIR:0 "Air"')
    lines.append(' DD_MARKET_CAT_NAVY:0 "Navy"')
    lines.append(' DD_MARKET_ASK_UP:0 "+1B"')
    lines.append(' DD_MARKET_ASK_DOWN:0 "-1B"')
    lines.append(
        ' DD_ASK_UP_TT:0 "Raise your asking price by 1B. The next lot you sell uses this price. Stock already listed keeps its own price."'
    )
    lines.append(
        ' DD_ASK_DOWN_TT:0 "Lower your asking price by 1B. A different price is its own row on the buy menu."'
    )
    for r in rows:
        u = r["slug"].upper()
        slug = r["slug"]
        lines.append(f' DD_MARKET_NAME_{u}:0 "${r["variant"]}$"')
        lines.append(
            f' DD_MARKET_STOCK_{u}:0 "Yours: [?dd_stock_{slug}|0]  ·  Pool: [?global.dd_pool_{slug}|0]"'
        )
        lines.append(
            f' DD_MARKET_PRICE_{u}_BUY:0 "[?global.dd_ask_{slug}|0]B  ({r["amount"]} units)"'
        )
        lines.append(
            f' DD_MARKET_PRICE_{u}_SELL:0 "[?global.dd_ask_{slug}|0]B  ({r["amount"]} units)"'
        )
        lines.append(
            f' DD_BUY_{u}_TT:0 "Buy {r["amount"]} ${r["variant"]}$ from the world pool for [?global.dd_ask_{slug}|0]B cash. Requires pool stock."'
        )
        lines.append(
            f' DD_SELL_{u}_TT:0 "List {r["amount"]} ${r["variant"]}$ at your ask of [?dd_my_ask_{slug}|0]B. You are paid when a buyer takes a lot. The earliest seller at this price is paid first."'
        )
    lines.append(' doomsday_market.1.t:0 "Shipment delivered"')
    lines.append(
        ' doomsday_market.1.d:0 "A buyer accepted your shipment of [GetDdSaleShipment]. You received §Y[?dd_sale_paid|0]B§!."'
    )
    lines.append(' doomsday_market.1.a:0 "Good."')
    lines.append(' DD_MARKET_SALE_UNKNOWN:0 "equipment"')
    path = ROOT / "localisation" / "english" / "doomsday_market_l_english.yml"
    path.write_bytes("\ufeff".encode("utf-8") + ("\n".join(lines) + "\n").encode("utf-8"))


def main() -> None:
    rows = catalog()
    print("rows", len(rows), {c: sum(1 for r in rows if r["cat"] == c) for c in ("land", "air", "navy")})
    seeded = [r for r in rows if r["seed"]]
    print("seed", sum(r["seed"] for r in seeded), "units across", len(seeded), "types")
    prices = [r["buy"] for r in rows]
    print("ask", min(prices), "to", max(prices))
    write_gui(rows)
    write_effects(rows)
    write_scripted_gui(rows)
    write_loc(rows)


if __name__ == "__main__":
    main()
