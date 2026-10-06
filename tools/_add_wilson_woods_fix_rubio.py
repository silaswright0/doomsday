# -*- coding: utf-8 -*-
"""Recenter Rubio; add Doug Wilson (AOG) and Darren Woods (TXO)."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

# tag -> (file, optional precrop LTRB, fit centering)
PORTRAITS = {
    # Rubio solo shot — nudge centering so face sits on axis
    "RBM": ("rbm_rubio.jpg", None, (0.48, 0.30)),
    # Doug Wilson is the bearded man at the podium (right side of duo shot)
    "AOG": ("aog_doug_wilson.webp", (0.42, 0.00, 0.92, 0.95), (0.55, 0.28)),
    # Darren Woods / Exxon
    "TXO": ("txo_darren_woods.png", None, (0.50, 0.32)),
}


def make(im: Image.Image, precrop, center) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    if precrop is not None:
        w, h = im.size
        l, t, r, b = precrop
        im = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    out = ImageOps.fit(im, (W, H), method=Image.Resampling.LANCZOS, centering=center)
    return ImageEnhance.Sharpness(out).enhance(1.08).convert("RGBA")


def save_dds(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def ensure_gfx(tags: list[str]) -> None:
    path = ROOT / "interface" / "doomsday_portraits.gfx"
    text = path.read_text(encoding="utf-8")
    block = []
    for tag in tags:
        name = f"GFX_portrait_{tag}_leader"
        if name in text:
            continue
        block.append(
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "gfx/leaders/{tag}/Portrait_{tag}_leader.dds"\n'
            "\t}\n"
        )
    if block:
        idx = text.rfind("}")
        path.write_text(text[:idx] + "".join(block) + text[idx:], encoding="utf-8", newline="\n")
        print("gfx added", len(block))


def patch_txo() -> None:
    path = next((ROOT / "history" / "countries").glob("TXO - *.txt"))
    text = path.read_text(encoding="utf-8")

    def repl(m: re.Match[str]) -> str:
        return (
            "create_country_leader = {\n"
            '\tname = "Darren Woods"\n'
            "\tpicture = GFX_portrait_TXO_leader\n"
            f"\tideology = {m.group(1)}\n"
            "}"
        )

    text2, n = re.subn(
        r'create_country_leader = \{\s*name = "[^"]+"\s*picture = GFX_portrait_\w+\s*ideology = (\S+)\s*\}',
        repl,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"TXO history patch failed ({n})")
    path.write_text(text2, encoding="utf-8", newline="\n")
    print("TXO leader Darren Woods")


def patch_aog_character() -> None:
    path = ROOT / "common" / "characters" / "doomsday_usa_splinters.txt"
    text = path.read_text(encoding="utf-8")
    new = """characters = {
	AOG_doug_wilson = {
		name = "Doug Wilson"
		portraits = {
			civilian = { large = GFX_portrait_AOG_leader }
			army = { large = GFX_portrait_AOG_leader small = GFX_portrait_AOG_leader }
		}
		country_leader = {
			ideology = theocrat
			expire = "1965.1.1"
		}
		corps_commander = {
			skill = 1
			attack_skill = 1
			defense_skill = 1
			planning_skill = 1
			logistics_skill = 1
		}
	}
}
"""
    path.write_text(new, encoding="utf-8", newline="\n")
    print("AOG character Doug Wilson")

    hist = ROOT / "history" / "countries" / "AOG - Army of God.txt"
    ht = hist.read_text(encoding="utf-8")
    if "AOG_pete_hegseth" in ht:
        hist.write_text(ht.replace("AOG_pete_hegseth", "AOG_doug_wilson"), encoding="utf-8", newline="\n")
        print("AOG history recruit updated")

    eff = ROOT / "common" / "scripted_effects" / "doomsday_usa.txt"
    et = eff.read_text(encoding="utf-8")
    old = (
        "create_country_leader = {\n"
        '\t\t\t\tname = "Pete Hegseth"\n'
        "\t\t\t\tpicture = GFX_portrait_unknown\n"
        "\t\t\t\tideology = theocrat\n"
        "\t\t\t}"
    )
    new_block = (
        "create_country_leader = {\n"
        '\t\t\t\tname = "Doug Wilson"\n'
        "\t\t\t\tpicture = GFX_portrait_AOG_leader\n"
        "\t\t\t\tideology = theocrat\n"
        "\t\t\t}"
    )
    if old in et:
        eff.write_text(et.replace(old, new_block), encoding="utf-8", newline="\n")
        print("AOG war-spawn leader updated")
    else:
        print("WARN: Hegseth create_country_leader block not found")


def main() -> None:
    prev = ROOT / "tools" / "_portrait_preview"
    prev.mkdir(exist_ok=True)
    for tag, (fname, precrop, center) in PORTRAITS.items():
        port = make(Image.open(SRC / fname), precrop, center)
        save_dds(ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds", port)
        port.convert("RGB").save(prev / f"{tag}.png")
        print("portrait", tag)
    ensure_gfx(["AOG", "TXO"])
    # RBM gfx already exists
    patch_txo()
    patch_aog_character()


if __name__ == "__main__":
    main()
