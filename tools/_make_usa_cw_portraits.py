# -*- coding: utf-8 -*-
"""Convert USA CW leader photos to HOI4 156x210 BGRA DDS portraits."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "_leader_src"
TEMPLATE = ROOT / "gfx" / "leaders" / "CAN" / "Portrait_CAN_leader.dds"
W, H = 156, 210

# tag -> (source file, name for history, ideology already set, crop box as 0-1 fractions LTRB)
LEADERS = {
    "PTF": ("ptf_rousseau.webp", "Thomas Rousseau", (0.28, 0.00, 0.78, 0.95)),
    "SFT": ("sft_thiel_yarvin.webp", "Peter Thiel", (0.00, 0.00, 1.00, 1.00)),
    "VIR": ("vir_rockefeller.jpg", "David Rockefeller", (0.05, 0.00, 0.95, 0.55)),
    "WCL": ("wcl_newsom.jpg", "Gavin Newsom", (0.30, 0.00, 0.72, 0.95)),
    "NYF": ("nyf_wallst.webp", "Finance Board", (0.15, 0.00, 0.85, 1.00)),
    "EAS": ("eas_aoc.jpg", "Alexandria Ocasio-Cortez", (0.28, 0.00, 0.78, 0.85)),
    "RBM": ("rbm_rubio.jpg", "Marco Rubio", (0.32, 0.00, 0.72, 0.90)),
    "VNM": ("vnm_vance.jpg", "JD Vance", (0.10, 0.00, 0.90, 0.95)),
}


def load_template() -> bytes:
    return TEMPLATE.read_bytes()[:128]


def to_portrait(im: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    l, t, r, b = box
    crop = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    # Cover 156x210
    cw, ch = crop.size
    scale = max(W / cw, H / ch)
    nw, nh = max(1, int(cw * scale + 0.5)), max(1, int(ch * scale + 0.5))
    crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - W) // 2
    top = max(0, (nh - H) // 5)  # bias slightly upward for faces
    if top + H > nh:
        top = nh - H
    out = crop.crop((left, top, left + W, top + H))
    # Mild sharpen for small DDS
    out = ImageEnhance.Sharpness(out).enhance(1.15)
    return out.convert("RGBA")


def save_dds(path: Path, image: Image.Image, header: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    hdr = bytearray(header)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, W * H * 4)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.tobytes("raw", "BGRA"))


def main() -> None:
    header = load_template()
    preview = ROOT / "tools" / "_portrait_preview"
    preview.mkdir(exist_ok=True)
    for tag, (fname, _name, box) in LEADERS.items():
        src = SRC / fname
        im = Image.open(src)
        port = to_portrait(im, box)
        out = ROOT / "gfx" / "leaders" / tag / f"Portrait_{tag}_leader.dds"
        save_dds(out, port, header)
        port.convert("RGB").save(preview / f"{tag}.png")
        print(f"{tag}: {out.relative_to(ROOT)} from {fname}")


if __name__ == "__main__":
    main()
