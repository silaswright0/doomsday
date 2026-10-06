# -*- coding: utf-8 -*-
"""HOI4 portraits via ImageOps.fit (reliable face centering)."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

# Optional pre-crop (L,T,R,B fractions) then fit with centering (x,y) in 0-1.
FIX = {
    # AOC: full frame, slight upward bias
    "EAS": ("eas_aoc.jpg", None, (0.50, 0.32)),
    # Dual portrait: keep both
    "SFT": ("sft_thiel_yarvin.webp", None, (0.55, 0.42)),
    # Abbott: cut raised hand (right side), keep face/shoulders
    "TXG": ("txg_abbott.jpg", (0.00, 0.00, 0.52, 0.78), (0.55, 0.28)),
    # DeSantis: slight left shift of centering to put nose on axis
    "FLO": ("flo_desantis.webp", None, (0.48, 0.30)),
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
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def main() -> None:
    prev = ROOT / "tools" / "_portrait_preview"
    for tag, (fname, precrop, center) in FIX.items():
        port = make(Image.open(SRC / fname), precrop, center)
        save_dds(ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds", port)
        port.convert("RGB").save(prev / f"{tag}.png")
        print(tag, "ok")


if __name__ == "__main__":
    main()
