"""Fix CW portrait DDS pitch (HOI4 expects full buffer size), zoom out Babu, wire NYF pic, AOG Oregon."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "gfx/leaders/CAN/Portrait_CAN_leader.dds").read_bytes()[:128]
W, H = 156, 210
# Paradox HOI4 leader DDS uses pitch = width * height * 4 (full buffer), not scanline.
PITCH = W * H * 4

CW_TAGS = [
    "ABR", "ACA", "AOG", "ASK", "DES", "EAS", "EBC", "ETX", "FDS", "FLO", "FVA",
    "NYF", "PTF", "RBL", "RBM", "SCN", "SFT", "TXG", "TXO", "TXR", "VIR", "VNM", "WCL",
]


def fix_pitch(path: Path) -> bool:
    raw = bytearray(path.read_bytes())
    if raw[:4] != b"DDS " or len(raw) < 128 + PITCH:
        return False
    old = struct.unpack_from("<I", raw, 20)[0]
    if old == PITCH:
        return False
    struct.pack_into("<I", raw, 12, H)
    struct.pack_into("<I", raw, 16, W)
    struct.pack_into("<I", raw, 20, PITCH)
    struct.pack_into("<I", raw, 24, 0)
    path.write_bytes(bytes(raw))
    return True


def save_dds(path: Path, image: Image.Image) -> None:
    hdr = bytearray(TEMPLATE)
    struct.pack_into("<I", hdr, 12, H)
    struct.pack_into("<I", hdr, 16, W)
    struct.pack_into("<I", hdr, 20, PITCH)
    struct.pack_into("<I", hdr, 24, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(hdr) + image.convert("RGBA").tobytes("raw", "BGRA"))


def remake_babu() -> None:
    src = ROOT / "tools/_leader_src/abr_babu.jpg"
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    # Source is already a tight headshot — pad so the face sits smaller in frame.
    pad = int(min(im.size) * 0.28)
    canvas = Image.new("RGB", (im.size[0] + pad * 2, im.size[1] + pad * 2), (32, 36, 32))
    canvas.paste(im, (pad, pad))
    out = ImageOps.fit(canvas, (W, H), method=Image.Resampling.LANCZOS, centering=(0.50, 0.38))
    out = ImageEnhance.Sharpness(out).enhance(1.08)
    dds = ROOT / "gfx/leaders/ABR/Portrait_ABR_leader.dds"
    save_dds(dds, out)
    prev = ROOT / "tools/_portrait_preview"
    prev.mkdir(exist_ok=True)
    out.save(prev / "ABR.png")
    print("ABR zoomed out")


def fix_nyf_history() -> None:
    path = ROOT / "history/countries/NYF - New York Finance.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "picture = GFX_portrait_unknown",
        "picture = GFX_portrait_NYF_leader",
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    print("NYF picture wired")


def fix_aog_oregon() -> None:
    path = ROOT / "common/scripted_effects/doomsday_usa_war.txt"
    text = path.read_text(encoding="utf-8")
    old = "\t\tAOG = { dd_usa_control_east_washington = yes }\n\t}"
    new = (
        "\t\tAOG = {\n"
        "\t\t\tdd_usa_control_east_washington = yes\n"
        "\t\t\tdd_usa_control_aog_oregon = yes\n"
        "\t\t}\n"
        "\t}"
    )
    if old not in text:
        if "dd_usa_control_aog_oregon = yes" in text:
            print("AOG oregon already called")
            return
        raise SystemExit("AOG control call site missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    print("AOG oregon occupation wired")


def main() -> None:
    fixed = 0
    for tag in CW_TAGS:
        p = ROOT / "gfx/leaders" / tag / f"Portrait_{tag}_leader.dds"
        if p.exists() and fix_pitch(p):
            fixed += 1
            print("pitch", tag)
    print(f"fixed pitch on {fixed} portraits")
    remake_babu()
    # ensure babu also has correct pitch (save_dds already does)
    fix_nyf_history()
    fix_aog_oregon()

    # sanity
    abr = (ROOT / "gfx/leaders/ABR/Portrait_ABR_leader.dds").read_bytes()
    assert struct.unpack_from("<I", abr, 20)[0] == PITCH
    war = (ROOT / "common/scripted_effects/doomsday_usa_war.txt").read_text(encoding="utf-8")
    assert "dd_usa_control_aog_oregon = yes" in war
    nyf = (ROOT / "history/countries/NYF - New York Finance.txt").read_text(encoding="utf-8")
    assert "GFX_portrait_NYF_leader" in nyf
    print("done")


if __name__ == "__main__":
    main()
