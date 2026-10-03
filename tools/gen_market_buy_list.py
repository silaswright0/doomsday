"""Buy tab lists only equipment with pool stock, packed from the top."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_arms_market as market

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = market.catalog()
    market.write_effects(rows)
    market.write_loc(rows)
    by_cat = {c: [r for r in rows if r["cat"] == c] for c in ("land", "air", "navy")}
    write_effect(by_cat)
    write_loc(by_cat)
    write_scripted_loc(by_cat)
    write_gui(by_cat)
    write_scripted_gui(by_cat)
    print({c: len(by_cat[c]) for c in by_cat})


def write_effect(by_cat: dict) -> None:
    lines = [
        "# Buy-tab slots. Rebuilt from the shared pool. Same result on every machine.",
        "",
        "dd_refresh_buy_slots = {",
    ]
    for cat, items in by_cat.items():
        lines.append(f"\tclear_array = dd_{cat}_stock_list")
        for row in items:
            lines.append(
                f"\tadd_to_array = {{ dd_{cat}_stock_list = dd_stock_{row['slug']} }}"
            )
        lines.append(f"\tclear_array = global.dd_buy_{cat}_slots")
        for field in ("ask", "pool", "amt", "need", "stock", "list"):
            lines.append(f"\tclear_array = global.dd_{cat}_row_{field}")
        lines.append("\tif = {")
        lines.append("\t\tlimit = { has_country_flag = dd_market_sell_tab }")
        for i, row in enumerate(items):
            need = row["amount"] - 1
            lines.append("\t\tif = {")
            lines.append(
                f"\t\t\tlimit = {{ check_variable = {{ dd_stock_{row['slug']} > {need} }} }}"
            )
            lines.append(f"\t\t\tadd_to_array = {{ global.dd_buy_{cat}_slots = {i} }}")
            lines.append(
                f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_ask = dd_my_ask_{row['slug']} }}"
            )
            lines.append(
                f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_pool = global.dd_pool_{row['slug']} }}"
            )
            lines.append(f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_amt = {row['amount']} }}")
            lines.append(f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_need = {need} }}")
            lines.append(
                f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_stock = dd_stock_{row['slug']} }}"
            )
            lines.append(f"\t\t\tadd_to_array = {{ global.dd_{cat}_row_list = -1 }}")
            lines.append("\t\t}")
        lines.append("\t}")
        lines.append("\telse = {")
        lines.append("\t\tset_temp_variable = { dd_i = 0 }")
        lines.append("\t\twhile_loop_effect = {")
        lines.append("\t\t\tlimit = {")
        lines.append(f"\t\t\t\tcheck_variable = {{ dd_i < {market.LIST_MAX} }}")
        lines.append("\t\t\t}")
        lines.append("\t\t\tset_temp_variable = { dd_q = global.dd_list_qty^dd_i }")
        lines.append("\t\t\tset_temp_variable = { dd_c = global.dd_list_cat^dd_i }")
        lines.append("\t\t\tif = {")
        lines.append("\t\t\t\tlimit = {")
        lines.append("\t\t\t\t\tcheck_variable = { dd_q > 0 }")
        lines.append(f"\t\t\t\t\tcheck_variable = {{ dd_c = {market.CAT_ID[cat]} }}")
        lines.append("\t\t\t\t}")
        lines.append("\t\t\t\tset_temp_variable = { dd_eq = global.dd_list_idx^dd_i }")
        lines.append(f"\t\t\t\tadd_to_array = {{ global.dd_buy_{cat}_slots = dd_eq }}")
        lines.append(f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_list = dd_i }}")
        lines.append(
            f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_ask = global.dd_list_price^dd_i }}"
        )
        lines.append(f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_pool = dd_q }}")
        lines.append(
            f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_amt = global.dd_list_amt^dd_i }}"
        )
        lines.append("\t\t\t\tset_temp_variable = { dd_need = global.dd_list_amt^dd_i }")
        lines.append("\t\t\t\tsubtract_from_temp_variable = { dd_need = 1 }")
        lines.append(f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_need = dd_need }}")
        lines.append(
            f"\t\t\t\tadd_to_array = {{ global.dd_{cat}_row_stock = dd_{cat}_stock_list^dd_eq }}"
        )
        lines.append("\t\t\t}")
        lines.append("\t\t\tadd_to_temp_variable = { dd_i = 1 }")
        lines.append("\t\t}")
        lines.append("\t}")
    lines.append("}")
    lines.append("")
    for cat, items in by_cat.items():
        for effect_name, call in (
            ("dd_buy", "dd_buy"),
            ("dd_buy_all", "dd_buy_all"),
            ("dd_sell", "dd_sell"),
            ("dd_sell_all", "dd_sell_all"),
            ("dd_ask_up", "dd_ask_up"),
            ("dd_ask_down", "dd_ask_down"),
        ):
            lines.append(f"{effect_name}_{cat}_picked = {{")
            for idx, row in enumerate(items):
                kw = "if" if idx == 0 else "else_if"
                lines.append(f"\t{kw} = {{")
                lines.append(f"\t\tlimit = {{ check_variable = {{ dd_pick = {idx} }} }}")
                lines.append(f"\t\t{call}_{row['slug']} = yes")
                lines.append("\t}")
            lines.append("}")
            lines.append("")
    path = ROOT / "common" / "scripted_effects" / "doomsday_market_buy.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_loc(by_cat: dict) -> None:
    lines = ["l_english:", ' DD_MARKET_SLOT_EMPTY:0 ""']
    for cat in by_cat:
        u = cat.upper()
        lines.append(f' DD_MARKET_ROW_{u}_NAME:0 "[dd_market_{cat}_name]"')
        lines.append(
            f' DD_MARKET_ROW_{u}_STOCK:0 "Yours: [?global.dd_{cat}_row_stock^dd_row|0]  ·  Pool: [?global.dd_{cat}_row_pool^dd_row|0]"'
        )
        lines.append(
            f' DD_MARKET_ROW_{u}_PRICE:0 "[?global.dd_{cat}_row_ask^dd_row|0]B ([?global.dd_{cat}_row_amt^dd_row|0] units)"'
        )
    path = ROOT / "localisation" / "english" / "doomsday_market_buy_l_english.yml"
    path.write_bytes("\ufeff".encode("utf-8") + ("\n".join(lines) + "\n").encode("utf-8"))


def write_scripted_loc(by_cat: dict) -> None:
    blocks = []
    for cat, items in by_cat.items():
        for field, key_of in (
            ("name", lambda r: f"DD_MARKET_NAME_{r['slug'].upper()}"),
            ("icon", lambda r: r["sprite"]),
        ):
            parts = [f"defined_text = {{\n\tname = dd_market_{cat}_{field}"]
            for idx, row in enumerate(items):
                parts.append(
                    "\ttext = { "
                    f"trigger = {{ check_variable = {{ dd_eq = {idx} }} }} "
                    f'localization_key = "{key_of(row)}" }}'
                )
            fallback = "GFX_infantry_equipment_text_icon" if field == "icon" else "DD_MARKET_SLOT_EMPTY"
            parts.append(f'\ttext = {{\n\t\tlocalization_key = "{fallback}"\n\t}}')
            parts.append("}")
            blocks.append("\n".join(parts))
    path = ROOT / "common" / "scripted_localisation" / "doomsday_market_buy.txt"
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_gui(by_cat: dict) -> None:
    windows = []
    rows = []
    for cat in by_cat:
        windows.append(
            f"""
	containerWindowType = {{
		name = "dd_market_buy_{cat}"
		position = {{ x = 10 y = 210 }}
		size = {{ width = 530 height = 100%% }}
		margin = {{ top = 0 bottom = 24 }}
		verticalScrollbar = "right_vertical_slider"
		scroll_wheel_factor = 40
		smooth_scrolling = yes
		clipping = yes

		background = {{
			name = "dd_market_buy_{cat}_bg"
			spriteType = "GFX_tiled_window2_1b_border"
		}}

		gridBoxType = {{
			name = "dd_market_{cat}_grid"
			position = {{ x = 8 y = 4 }}
			size = {{ width = 500 height = 100%% }}
			slotsize = {{ width = 500 height = 104 }}
			format = "UPPER_LEFT"
			max_slots_horizontal = 1
		}}
	}}"""
        )
        rows.append(
            f"""
	containerWindowType = {{
		name = "dd_market_{cat}_row"
		size = {{ width = 500 height = 100 }}

		iconType = {{
			name = "dd_{cat}_row_card"
			spriteType = "GFX_land_equipment_market_entry"
			position = {{ x = 0 y = 0 }}
			frame = 1
			alwaystransparent = yes
		}}
		iconType = {{
			name = "dd_{cat}_row_icon"
			spriteType = "GFX_infantry_equipment_text_icon"
			position = {{ x = 168 y = 18 }}
			scale = 0.42
			alwaystransparent = yes
		}}
		instantTextboxType = {{
			name = "dd_{cat}_row_name"
			position = {{ x = 12 y = 6 }}
			font = "hoi_18mbs"
			text = "DD_MARKET_ROW_{cat.upper()}_NAME"
			maxWidth = 300
			maxHeight = 20
			format = left
			alwaystransparent = yes
		}}
		instantTextboxType = {{
			name = "dd_{cat}_row_stock"
			position = {{ x = 12 y = 28 }}
			font = "hoi_16mbs"
			text = "DD_MARKET_ROW_{cat.upper()}_STOCK"
			maxWidth = 300
			maxHeight = 18
			format = left
			alwaystransparent = yes
		}}
		iconType = {{
			name = "dd_{cat}_row_cash"
			spriteType = "GFX_dd_icon_cash"
			position = {{ x = 12 y = 68 }}
			alwaystransparent = yes
		}}
		instantTextboxType = {{
			name = "dd_{cat}_row_price"
			position = {{ x = 40 y = 70 }}
			font = "hoi_18mbs"
			text = "DD_MARKET_ROW_{cat.upper()}_PRICE"
			maxWidth = 220
			maxHeight = 20
			format = left
			alwaystransparent = yes
		}}
		buttonType = {{
			name = "dd_{cat}_row_buy"
			quadTextureSprite = "GFX_diplo_filter_entry"
			buttonText = "DD_MARKET_BUY"
			buttonFont = "hoi_16mbs"
			position = {{ x = 360 y = 18 }}
			clicksound = click_default
			pdx_tooltip = "DD_MARKET_BUY_SLOT_TT"
		}}
		buttonType = {{
			name = "dd_{cat}_row_sell"
			quadTextureSprite = "GFX_diplo_filter_entry"
			buttonText = "DD_MARKET_SELL"
			buttonFont = "hoi_16mbs"
			position = {{ x = 360 y = 18 }}
			clicksound = click_default
			pdx_tooltip = "DD_MARKET_SELL_SLOT_TT"
		}}
		buttonType = {{
			name = "dd_{cat}_row_ask_down"
			quadTextureSprite = "GFX_diplo_filter_entry"
			buttonText = "DD_MARKET_ASK_DOWN"
			buttonFont = "hoi_16mbs"
			position = {{ x = 268 y = 58 }}
			clicksound = click_default
			pdx_tooltip = "DD_ASK_DOWN_TT"
		}}
		buttonType = {{
			name = "dd_{cat}_row_ask_up"
			quadTextureSprite = "GFX_diplo_filter_entry"
			buttonText = "DD_MARKET_ASK_UP"
			buttonFont = "hoi_16mbs"
			position = {{ x = 360 y = 58 }}
			clicksound = click_default
			pdx_tooltip = "DD_ASK_UP_TT"
		}}
	}}"""
        )
    text = "guiTypes = {" + "".join(windows) + "".join(rows) + "\n}\n"
    (ROOT / "interface" / "doomsday_market_buy.gui").write_text(text, encoding="utf-8")


def cat_visible(cat: str) -> str:
    if cat == "land":
        return """			has_country_flag = dd_show_arms_market
			NOT = { has_country_flag = dd_market_air_tab }
			NOT = { has_country_flag = dd_market_navy_tab }"""
    if cat == "air":
        return """			has_country_flag = dd_show_arms_market
			has_country_flag = dd_market_air_tab"""
    return """			has_country_flag = dd_show_arms_market
			has_country_flag = dd_market_navy_tab"""


def write_scripted_gui(by_cat: dict) -> None:
    blocks = []
    for cat in by_cat:
        blocks.append(
            f"""
	dd_market_buy_{cat}_ui = {{
		context_type = player_context
		parent_window_token = decision_tab
		window_name = "dd_market_buy_{cat}"
		visible = {{
{cat_visible(cat)}
		}}

		dynamic_lists = {{
			dd_market_{cat}_grid = {{
				array = global.dd_buy_{cat}_slots
				value = dd_eq
				index = dd_row
				change_scope = no
				entry_container = "dd_market_{cat}_row"
			}}
		}}

		effects = {{
			dd_{cat}_row_buy_click = {{
				set_variable = {{ global.dd_active_list = global.dd_{cat}_row_list^dd_row }}
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_buy_{cat}_picked = yes
			}}
			dd_{cat}_row_buy_shift_click = {{
				set_variable = {{ global.dd_active_list = global.dd_{cat}_row_list^dd_row }}
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_buy_all_{cat}_picked = yes
			}}
			dd_{cat}_row_sell_click = {{
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_sell_{cat}_picked = yes
			}}
			dd_{cat}_row_sell_shift_click = {{
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_sell_all_{cat}_picked = yes
			}}
			dd_{cat}_row_ask_up_click = {{
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_ask_up_{cat}_picked = yes
			}}
			dd_{cat}_row_ask_down_click = {{
				set_temp_variable = {{ dd_pick = dd_eq }}
				dd_ask_down_{cat}_picked = yes
			}}
		}}

		triggers = {{
			dd_{cat}_row_buy_visible = {{
				NOT = {{ has_country_flag = dd_market_sell_tab }}
			}}
			dd_{cat}_row_sell_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_{cat}_row_ask_up_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_{cat}_row_ask_down_visible = {{
				has_country_flag = dd_market_sell_tab
			}}
			dd_{cat}_row_buy_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_ask^dd_row > 0 }}
				NOT = {{ check_variable = {{ treasury < global.dd_{cat}_row_ask^dd_row }} }}
				check_variable = {{ global.dd_{cat}_row_pool^dd_row > global.dd_{cat}_row_need^dd_row }}
			}}
			dd_{cat}_row_buy_shift_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_ask^dd_row > 0 }}
				NOT = {{ check_variable = {{ treasury < global.dd_{cat}_row_ask^dd_row }} }}
				check_variable = {{ global.dd_{cat}_row_pool^dd_row > global.dd_{cat}_row_need^dd_row }}
			}}
			dd_{cat}_row_sell_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_stock^dd_row > global.dd_{cat}_row_need^dd_row }}
			}}
			dd_{cat}_row_sell_shift_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_stock^dd_row > global.dd_{cat}_row_need^dd_row }}
			}}
			dd_{cat}_row_ask_up_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_ask^dd_row < 999 }}
			}}
			dd_{cat}_row_ask_down_click_enabled = {{
				check_variable = {{ global.dd_{cat}_row_ask^dd_row > 1 }}
			}}
		}}

		properties = {{
			dd_{cat}_row_icon = {{
				image = "[dd_market_{cat}_icon]"
			}}
		}}
	}}"""
        )
    text = "scripted_gui = {" + "".join(blocks) + "\n}\n"
    (ROOT / "common" / "scripted_guis" / "doomsday_market_buy.txt").write_text(
        text, encoding="utf-8"
    )


if __name__ == "__main__":
    main()


