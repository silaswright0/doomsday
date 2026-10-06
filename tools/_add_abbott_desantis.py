# -*- coding: utf-8 -*-
"""Add Greg Abbott (TXG) and Ron DeSantis (FLO) portraits."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

LEADERS = {
    "TXG": ("txg_abbott.jpg", "Greg Abbott", (0.28, 0.00, 0.78, 0.92)),
    "FLO": ("flo_desantis.webp", "Ron DeSantis", (0.22, 0.00, 0.78, 0.95)),
}


def to_portrait(im: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    l, t, r, b = box
    crop = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    cw, ch = crop.size
    scale = max(W / cw, H / ch)
    nw, nh = max(1, int(cw * scale + 0.5)), max(1, int(ch * scale + 0.5))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, (nh - H) // 5)
    if top + H > nh:
        top = nh - H
    out = crop.crop((left, top, left + W, top + H))
    return ImageEnhance.Sharpness(out).enhance(1.15).convert("RGBA")


def save_dds(path: Path, image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def main() -> None:
    prev = ROOT / "tools" / "_portrait_preview"
    prev.mkdir(exist_ok=True)
    for tag, (fname, name, box) in LEADERS.items():
        port = to_portrait(Image.open(SRC / fname), box)
        out = ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds"
        save_dds(out, port)
        port.convert("RGB").save(prev / f"{tag}.png")

        hist = list((ROOT / "history" / "countries").glob(f"{tag} - *.txt"))
        if not hist:
            raise SystemExit(f"no history for {tag}")
        path = hist[0]
        text = path.read_text(encoding="utf-8")
        gfx = f"GFX_portrait_{tag}_leader"

        def repl(m: re.Match[str], name=name, gfx=gfx) -> str:
            return (
                "create_country_leader = {\n"
                f'\tname = "{name}"\n'
                f"\tpicture = {gfx}\n"
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
            raise SystemExit(f"history fail {tag} {n}")
        path.write_text(text2, encoding="utf-8", newline="\n")
        print("OK", tag, path.name)

    gpath = ROOT / "interface" / "doomsday_portraits.gfx"
    gtext = gpath.read_text(encoding="utf-8")
    block = []
    for tag in LEADERS:
        name = f"GFX_portrait_{tag}_leader"
        if name in gtext:
            print("gfx exists", name)
            continue
        block.append(
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "gfx/leaders/{tag}/Portrait_{tag}_leader.dds"\n'
            "\t}\n"
        )
    if block:
        idx = gtext.rfind("}")
        gpath.write_text(gtext[:idx] + "".join(block) + gtext[idx:], encoding="utf-8", newline="\n")
        print("gfx added", len(block))


if __name__ == "__main__":
    main()
