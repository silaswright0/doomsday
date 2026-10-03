"""Extend the production header so the resource row has room for 15 icons."""
import struct
from pathlib import Path

from PIL import Image

VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\gfx\interface\production_win_top.dds")
OUT = Path("gfx/interface/production_win_top.dds")
NEW_W = 740
RIGHT = 64


def load_dds(path: Path) -> tuple[Image.Image, bytes]:
    blob = path.read_bytes()
    height, width = struct.unpack_from("<2I", blob, 12)
    image = Image.frombytes("RGBA", (width, height), blob[128 : 128 + width * height * 4], "raw", "BGRA")
    return image, blob


def save_dds(path: Path, image: Image.Image, template: bytes) -> None:
    width, height = image.size
    header = bytearray(template[:128])
    struct.pack_into("<I", header, 12, height)
    struct.pack_into("<I", header, 16, width)
    struct.pack_into("<I", header, 20, width * 4)
    struct.pack_into("<I", header, 24, 0)
    path.write_bytes(bytes(header) + image.tobytes("raw", "BGRA"))


def main() -> None:
    src, blob = load_dds(VANILLA)
    width, height = src.size
    insert = NEW_W - width
    # Factory wells end just before the right border. The corner emblem is taller
    # than that border, so the top band keeps a wider cap than the well row.
    slot_y = 178
    well_end = 520
    top_cut = width - RIGHT
    tile_w = 32
    tile_x = 155
    upper_tile = src.crop((tile_x, 0, tile_x + tile_w, slot_y))
    # Repeat the plain metal just above the wells. Do not repeat the wells themselves.
    lower_tile = src.crop((tile_x, slot_y - 12, tile_x + tile_w, slot_y - 4))
    lower = Image.new("RGBA", (tile_w, height - slot_y))
    for y in range(0, height - slot_y, lower_tile.size[1]):
        lower.paste(lower_tile, (0, y))

    out = Image.new("RGBA", (NEW_W, height))
    out.paste(src.crop((0, 0, top_cut, slot_y)), (0, 0))
    upper = Image.new("RGBA", (insert, slot_y))
    for x in range(0, insert, tile_w):
        upper.paste(upper_tile, (x, 0))
    out.paste(upper, (top_cut, 0))
    out.paste(src.crop((top_cut, 0, width, slot_y)), (top_cut + insert, 0))

    out.paste(src.crop((0, slot_y, well_end, height)), (0, slot_y))
    lower_fill = Image.new("RGBA", (insert, height - slot_y))
    for x in range(0, insert, tile_w):
        lower_fill.paste(lower, (x, 0))
    out.paste(lower_fill, (well_end, slot_y))
    border_w = width - well_end
    out.paste(src.crop((well_end, slot_y, width, height)), (NEW_W - border_w, slot_y))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_dds(OUT, out, blob)
    print("wrote", OUT, out.size)


if __name__ == "__main__":
    main()
