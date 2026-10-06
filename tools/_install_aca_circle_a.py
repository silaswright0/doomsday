"""Install Circle-A art as ACA flag (all sizes/ideos) and leader portrait."""
from __future__ import annotations

import shutil
import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"C:\Users\siwri\AppData\Roaming\Cursor\User\workspaceStorage"
    r"\28f191d0c07fc98606a8f327f332d274\images"
    r"\anarchist-bdb6160c-9a8d-4389-900e-5ccc3cf68eb9.webp"
)
TEMPLATE = (ROOT / "gfx/leaders/CAN/Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210
PITCH = W * H * 4

IDEOS = [
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


def save_tga(path: Path, im: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flipped = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert("RGBA")
    w, h = flipped.size
    header = bytearray(18)
    header[2] = 2
    header[12] = w & 0xFF
    header[13] = (w >> 8) & 0xFF
    header[14] = h & 0xFF
    header[15] = (h >> 8) & 0xFF
    header[16] = 32
    header[17] = 8
    path.write_bytes(bytes(header) + flipped.tobytes("raw", "BGRA"))


def save_dds(path: Path, image: Image.Image) -> None:
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, PITCH)
    struct.pack_into("<I", hdr, 24, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(hdr) + image.convert("RGBA").tobytes("raw", "BGRA"))


def flag_crop(im: Image.Image, tw: int, th: int) -> Image.Image:
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
    return im.resize((tw, th), Image.Resampling.LANCZOS)


def portrait_from_flag(im: Image.Image) -> Image.Image:
    # Cover 156x210 so the Circle-A fills the frame
    out = ImageOps.fit(im, (W, H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    # Slight punch so the A reads at small size
    out = ImageEnhance.Contrast(out).enhance(1.08)
    out = ImageEnhance.Sharpness(out).enhance(1.15)
    return out


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    im = ImageOps.exif_transpose(Image.open(SRC)).convert("RGB")

    flag_src = ROOT / "tools/_flag_src/aca_flag.webp"
    lead_src = ROOT / "tools/_leader_src/aca_anarchist.webp"
    flag_src.parent.mkdir(parents=True, exist_ok=True)
    lead_src.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, flag_src)
    shutil.copy2(SRC, lead_src)

    sizes = {
        ROOT / "gfx/flags": (82, 52),
        ROOT / "gfx/flags/medium": (41, 26),
        ROOT / "gfx/flags/small": (10, 7),
    }
    written = 0
    for folder, size in sizes.items():
        flag = flag_crop(im, *size)
        for ideo in IDEOS:
            name = "ACA.tga" if not ideo else f"ACA_{ideo}.tga"
            save_tga(folder / name, flag)
            written += 1

    port = portrait_from_flag(im)
    save_dds(ROOT / "gfx/leaders/ACA/Portrait_ACA_leader.dds", port)
    prev = ROOT / "tools/_portrait_preview"
    prev.mkdir(exist_ok=True)
    port.save(prev / "ACA.png")
    flag_crop(im, 82, 52).save(prev / "ACA_flag.png")

    # War start still creates Commune Council with unknown in one branch — keep portrait wired in history.
    print(f"wrote {written} ACA flags + portrait")


if __name__ == "__main__":
    main()
