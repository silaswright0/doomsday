# -*- coding: utf-8 -*-
"""Second-pass face centering for EAS/SFT/TXG/FLO."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

# Face-only boxes (fractions of source). TXG excludes raised hand.
FIX = {
    "EAS": ("eas_aoc.jpg", (0.32, 0.06, 0.68, 0.82)),
    "SFT": ("sft_thiel_yarvin.webp", (0.12, 0.00, 0.88, 0.92)),
    "TXG": ("txg_abbott.jpg", (0.12, 0.00, 0.48, 0.72)),
    "FLO": ("flo_desantis.webp", (0.38, 0.00, 0.82, 0.88)),
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
    top = max(0, int((nh - H) * 0.12))
    if top + H > nh:
        top = max(0, nh - H)
    out = crop.crop((left, top, left + W, top + H))
    return ImageEnhance.Sharpness(out).enhance(1.12).convert("RGBA")


def save_dds(path: Path, image: Image.Image) -> None:
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def main() -> None:
    prev = ROOT / "tools" / "_portrait_preview"
    for tag, (fname, box) in FIX.items():
        port = to_portrait(Image.open(SRC / fname), box)
        save_dds(ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds", port)
        port.convert("RGB").save(prev / f"{tag}.png")
        print(tag, "ok")


if __name__ == "__main__":
    main()
