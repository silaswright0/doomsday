# -*- coding: utf-8 -*-
"""Center portraits on a face point with correct 156:210 aspect."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = (ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210

# tag -> (file, face_cx, face_cy, zoom)  zoom = crop height as fraction of source height
# face coords are fractions of source width/height; eyes should sit ~35% down the frame.
FIX = {
    "EAS": ("eas_aoc.jpg", 0.52, 0.42, 0.72),
    "SFT": ("sft_thiel_yarvin.webp", 0.55, 0.42, 0.95),
    "TXG": ("txg_abbott.jpg", 0.38, 0.32, 0.58),
    "FLO": ("flo_desantis.webp", 0.50, 0.38, 0.70),
}


def to_portrait(im: Image.Image, cx: float, cy: float, zoom: float) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    sw, sh = im.size
    ch = max(32, int(sh * zoom))
    cw = max(32, int(ch * W / H))
    # Prefer keeping full face width if source is narrow.
    if cw > sw:
        cw = sw
        ch = int(cw * H / W)
    fx, fy = int(cx * sw), int(cy * sh)
    # Place face point ~38% from top of crop (typical HOI4 eye line).
    left = fx - cw // 2
    top = fy - int(ch * 0.38)
    left = max(0, min(left, sw - cw))
    top = max(0, min(top, sh - ch))
    crop = im.crop((left, top, left + cw, top + ch))
    out = crop.resize((W, H), Image.Resampling.LANCZOS)
    return ImageEnhance.Sharpness(out).enhance(1.1).convert("RGBA")


def save_dds(path: Path, image: Image.Image) -> None:
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def main() -> None:
    prev = ROOT / "tools" / "_portrait_preview"
    for tag, (fname, cx, cy, zoom) in FIX.items():
        port = to_portrait(Image.open(SRC / fname), cx, cy, zoom)
        save_dds(ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds", port)
        port.convert("RGB").save(prev / f"{tag}.png")
        print(tag, "centered")


if __name__ == "__main__":
    main()
