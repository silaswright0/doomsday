"""Merge NY Island (1125) into NYC; keep contiguous IDs by absorbing into 1125 and shifting 1139-1141."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def write_merged_nyc() -> None:
    merged = """state={
	id=1125
	name="STATE_1125"
	manpower = 9200000
	state_category = megalopolis
	history={
		owner = USA
		add_extra_state_shared_building_slots = 10
		add_core_of = USA
		victory_points = { # New York
			3878 35
		}
		buildings = {
			infrastructure = 5
			industrial_complex = 6
			finance_center = 4
			services_building = 4
			air_base = 1
			3878 = {
				supply_node = 1
				naval_base = 1
				landmark_statue_of_liberty = {
					level = 1
					allowed = { has_dlc = "Gotterdammerung" }
				}
			}
		}
	}
	provinces={
		859 3878 13421 13422
	}
	local_supplies=0.0
}
"""
    out = ROOT / "history/states/1125-New York City.txt"
    out.write_text(merged, encoding="utf-8", newline="\n")
    (ROOT / "history/states/1125-New York Finance.txt").unlink(missing_ok=True)
    (ROOT / "history/states/1138-New York City.txt").unlink(missing_ok=True)


def renumber_metro_states() -> None:
    # Process high→low so temp names do not collide.
    renames = [
        ("1141-National Capital Region.txt", 1140, "1140-National Capital Region.txt"),
        ("1140-Houston.txt", 1139, "1139-Houston.txt"),
        ("1139-Los Angeles.txt", 1138, "1138-Los Angeles.txt"),
    ]
    for old_name, new_id, new_name in renames:
        p = ROOT / "history/states" / old_name
        text = p.read_text(encoding="utf-8")
        text = re.sub(r"id\s*=\s*\d+", f"id={new_id}", text, count=1)
        text = re.sub(r'name\s*=\s*"STATE_\d+"', f'name="STATE_{new_id}"', text, count=1)
        out = ROOT / "history/states" / new_name
        if p.resolve() == out.resolve():
            p.write_text(text, encoding="utf-8", newline="\n")
        else:
            out.write_text(text, encoding="utf-8", newline="\n")
            p.unlink()


def patch_buildings() -> None:
    path = ROOT / "map/buildings.txt"
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if not line or ";" not in line:
            out.append(line)
            continue
        sid, rest = line.split(";", 1)
        if sid == "1138":
            sid = "1125"
        elif sid == "1141":
            sid = "1140"
        elif sid == "1140":
            sid = "1139"
        elif sid == "1139":
            sid = "1138"
        # 1125 rows (island province 859) already correct
        out.append(f"{sid};{rest}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def remap_state_token(text: str, old: int, new: int) -> str:
    reps = [
        (rf"\btransfer_state\s*=\s*{old}\b", f"transfer_state = {new}"),
        (rf"\badd_state_core\s*=\s*{old}\b", f"add_state_core = {new}"),
        (rf"\bowns_state\s*=\s*{old}\b", f"owns_state = {new}"),
        (rf"\bcontrols_state\s*=\s*{old}\b", f"controls_state = {new}"),
        (rf"\bset_capital\s*=\s*\{{\s*state\s*=\s*{old}\b", f"set_capital = {{ state = {new}"),
        (rf"(?m)^capital\s*=\s*{old}\b", f"capital = {new}"),
        (rf"(?m)^(\t+){old}\s*=\s*{{", rf"\g<1>{new} = {{"),
        (rf"(?<!\d){old}\s*=\s*{{\s*create_unit", f"{new} = {{ create_unit"),
        (rf"(?<!\d){old}\s*=\s*{{\s*add_building_construction", f"{new} = {{ add_building_construction"),
        (
            rf"(?<!\d){old}\s*=\s*{{(\s*(?:NOT\s*=\s*{{)?\s*is_owned_by)",
            rf"{new} = {{\1",
        ),
    ]
    for pat, repl in reps:
        text = re.sub(pat, repl, text)
    return text


def patch_gameplay_refs() -> None:
    targets = [
        ROOT / "common/scripted_effects/doomsday_usa.txt",
        ROOT / "common/scripted_effects/doomsday_usa_war.txt",
        ROOT / "history/countries/NYF - New York Finance.txt",
        ROOT / "history/countries/USA - USA.txt",
        ROOT / "history/countries/USB - USB.txt",
        ROOT / "history/countries/FVA - Atlantic Command.txt",
    ]
    # High→low then NYC 1138→1125
    mapping = [(1141, 1140), (1140, 1139), (1139, 1138), (1138, 1125)]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        for old, new in mapping:
            text = remap_state_token(text, old, new)
        path.write_text(text, encoding="utf-8", newline="\n")

    # Clean NYF release: island+city were both transferred; now one state.
    usa = ROOT / "common/scripted_effects/doomsday_usa.txt"
    text = usa.read_text(encoding="utf-8")
    text = re.sub(
        r"(NYF = \{\n\t\t\ttransfer_state = 1125\n\t\t\tadd_state_core = 1125\n)"
        r"\t\t\ttransfer_state = 1125\n\t\t\tadd_state_core = 1125\n",
        r"\1",
        text,
    )
    # cores list: drop duplicate 1125 if island+city both became 1125
    text = text.replace(
        "\t# NY Island + Rhode Island\n\tadd_state_core = 1125\n\tadd_state_core = 1136\n",
        "\t# New York City + Rhode Island\n\tadd_state_core = 1125\n\tadd_state_core = 1136\n",
    )
    usa.write_text(text, encoding="utf-8", newline="\n")

    war = ROOT / "common/scripted_effects/doomsday_usa_war.txt"
    w = war.read_text(encoding="utf-8")
    w = w.replace(
        "# Wall Street owns New York Island (state 1125); no extra province seizes.",
        "# Wall Street owns New York City (state 1125); no extra province seizes.",
    )
    war.write_text(w, encoding="utf-8", newline="\n")


def patch_loc() -> None:
    path = ROOT / "localisation/english/doomsday_usa_l_english.yml"
    text = path.read_text(encoding="utf-8")
    text = text.replace(' STATE_1125:0 "New York Island"', ' STATE_1125:0 "New York City"')
    text = text.replace(' STATE_1138:0 "New York City"', ' STATE_1138:0 "Los Angeles"')
    text = text.replace(' STATE_1139:0 "Los Angeles"', ' STATE_1139:0 "Houston"')
    text = text.replace(' STATE_1140:0 "Houston"', ' STATE_1140:0 "National Capital Region"')
    text = re.sub(r"\n STATE_1141:0 \"National Capital Region\"", "", text)
    path.write_text(text, encoding="utf-8", newline="\n")


def strip_cw_bypass() -> None:
    path = ROOT / "common/national_focus/usa.txt"
    text = path.read_text(encoding="utf-8")
    pat = (
        r"\n\t\tbypass = \{\n"
        r"\t\t\tOR = \{\n"
        r"\t\t\t\thas_country_flag = dd_usa_civil_war\n"
        r"\t\t\t\thas_global_flag = dd_usa_civil_war_started\n"
        r"\t\t\t\}\n"
        r"\t\t\}"
    )
    new, n = re.subn(pat, "", text)
    path.write_text(new, encoding="utf-8", newline="\n")
    print(f"removed {n} CW bypass blocks")


def install_fds_flag() -> None:
    src = ROOT / "tools/_flag_src/fds_flag.jpg"
    if not src.exists():
        raise SystemExit(f"missing {src}")
    im = Image.open(src).convert("RGBA")
    # Center-crop to flag aspect then resize to HOI4 sizes.
    tw, th = 82, 52
    aspect = tw / th
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
    else:
        nh = int(w / aspect)
        top = (h - nh) // 2
        im = im.crop((0, top, w, top + nh))

    sizes = {
        ROOT / "gfx/flags": (82, 52),
        ROOT / "gfx/flags/medium": (41, 26),
        ROOT / "gfx/flags/small": (10, 7),
    }
    ideos = [
        "",
        "social_democracy",
        "social_liberalism",
        "liberal_conservatism",
        "progressive_populism",
        "national_populism",
        "sovereign_democracy",
        "military_junta",
        "absolute_monarchy",
        "state_socialism",
        "left_wing_nationalism",
        "islamic_democracy",
        "theocratic_absolutism",
        "jihadist_fundamentalism",
        "democratic_confederalism",
        "fascism",
        "communism",
        "technocracy",
        "anarcho_communism",
    ]
    written = 0
    for folder, size in sizes.items():
        folder.mkdir(parents=True, exist_ok=True)
        flag = im.resize(size, Image.Resampling.LANCZOS)
        # HOI4 TGA is typically BGRA uncompressed
        raw = flag.tobytes("raw", "BGRA")
        for ideo in ideos:
            name = "FDS.tga" if not ideo else f"FDS_{ideo}.tga"
            path = folder / name
            # Minimal TGA header for uncompressed truecolor 32-bit
            header = bytearray(18)
            header[2] = 2  # uncompressed true-color
            header[12] = size[0] & 0xFF
            header[13] = (size[0] >> 8) & 0xFF
            header[14] = size[1] & 0xFF
            header[15] = (size[1] >> 8) & 0xFF
            header[16] = 32
            header[17] = 8  # alpha bits in attribute; origin bottom-left often 0x20 but HOI4 accepts 0
            # Flip vertically for bottom-left origin
            flipped = flag.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            raw = flipped.tobytes("raw", "BGRA")
            path.write_bytes(bytes(header) + raw)
            written += 1
    print(f"wrote {written} FDS flag TGAs")


def verify_states() -> None:
    ids = []
    for p in (ROOT / "history/states").glob("*.txt"):
        t = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"id\s*=\s*(\d+)", t)
        if m:
            ids.append(int(m.group(1)))
    ids = sorted(ids)
    gaps = [i for i in range(ids[0], ids[-1] + 1) if i not in set(ids)]
    print(f"states count={len(ids)} max={ids[-1]} gaps={gaps[:10]} (n={len(gaps)})")
    nyc = (ROOT / "history/states/1125-New York City.txt").read_text(encoding="utf-8")
    assert "859" in nyc and "3878" in nyc
    assert not (ROOT / "history/states/1138-New York City.txt").exists()
    assert (ROOT / "history/states/1138-Los Angeles.txt").exists()
    assert (ROOT / "history/states/1140-National Capital Region.txt").exists()
    assert not (ROOT / "history/states/1141-National Capital Region.txt").exists()


def main() -> None:
    write_merged_nyc()
    renumber_metro_states()
    patch_buildings()
    patch_gameplay_refs()
    patch_loc()
    strip_cw_bypass()
    install_fds_flag()
    verify_states()
    print("done")


if __name__ == "__main__":
    main()
