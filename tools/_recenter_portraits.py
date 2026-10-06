# -*- coding: utf-8 -*-
"""Recenter off-center USA CW leader portraits."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

# (file, crop LTRB as fractions) — tighter face-centered boxes
FIX = {
    "EAS": ("eas_aoc.jpg", (0.34, 0.00, 0.78, 0.78)),
    "SFT": ("sft_thiel_yarvin.webp", (0.08, 0.02, 0.92, 0.98)),
    "TXG": ("txg_abbott.jpg", (0.38, 0.00, 0.82, 0.88)),
    "FLO": ("flo_desantis.webp", (0.30, 0.00, 0.76, 0.92)),
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
    # Bias upward so eyes sit in the upper third of the HOI4 frame.
    top = max(0, int((nh - H) * 0.15))
    if top + H > nh:
        top = max(0, nh - H)
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
    for tag, (fname, box) in FIX.items():
        port = to_portrait(Image.open(SRC / fname), box)
        out = ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds"
        save_dds(out, port)
        port.convert("RGB").save(prev / f"{tag}.png")
        print("recentered", tag)


if __name__ == "__main__":
    main()
