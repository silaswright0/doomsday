"""ABR portrait: full-width face plate, vertically centered, black letterbox."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "gfx/leaders/CAN/Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210
PITCH = W * H * 4


def save_dds(path: Path, image: Image.Image) -> None:
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, PITCH)
    struct.pack_into("<I", hdr, 24, 0)
    path.write_bytes(bytes(hdr) + image.convert("RGBA").tobytes("raw", "BGRA"))


def main() -> None:
    src = ImageOps.exif_transpose(Image.open(ROOT / "tools/_leader_src/abr_babu.jpg")).convert("RGB")
    sw, sh = src.size
    # Center square from landscape
    side = sh
    left = (sw - side) // 2
    square = src.crop((left, 0, left + side, sh))

    # Full width, keep square aspect → black bars top/bottom
    face = square.resize((W, W), Image.Resampling.LANCZOS)
    face = ImageEnhance.Sharpness(face).enhance(1.1)

    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    y = (H - W) // 2
    canvas.paste(face, (0, y))

    save_dds(ROOT / "gfx/leaders/ABR/Portrait_ABR_leader.dds", canvas)
    prev = ROOT / "tools/_portrait_preview"
    prev.mkdir(exist_ok=True)
    canvas.save(prev / "ABR.png")
    print(f"ABR centered {W}x{W} at y={y}, black bars {y}px each")


if __name__ == "__main__":
    main()
