"""Rebuild the 15-frame resource strips. Oil stays frame 1, coal moves to frame 15."""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / "gfx" / "interface"
ICONS = ROOT / "tools" / "data" / "resource_icons"
FRAME = 27
HEADER = 128


def load_dds(path: Path) -> Image.Image:
    blob = path.read_bytes()
    _size, _flags, height, width, _pitch = struct.unpack_from("<5I", blob, 4)
    pixels = blob[HEADER : HEADER + width * height * 4]
    image = Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
    return image


def save_dds(path: Path, image: Image.Image, template: bytes) -> None:
    width, height = image.size
    header = bytearray(template[:HEADER])
    struct.pack_into("<I", header, 12, height)
    struct.pack_into("<I", header, 16, width)
    struct.pack_into("<I", header, 20, width * 4)
    struct.pack_into("<I", header, 24, 0)
    raw = image.tobytes("raw", "BGRA")
    path.write_bytes(bytes(header) + raw)


def _inside(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    crossed = False
    j = len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            crossed = not crossed
        j = i
    return crossed


def draw_titanium() -> Image.Image:
    # Isometric ingot. The old fill covered the whole upper frame, so it read as a white square.
    top = [(13, 4), (22, 9), (13, 14), (4, 9)]
    left = [(4, 9), (13, 14), (13, 22), (4, 17)]
    right = [(22, 9), (13, 14), (13, 22), (22, 17)]
    cube = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    px = cube.load()
    for y in range(FRAME):
        for x in range(FRAME):
            point = (x + 0.5, y + 0.5)
            if _inside(*point, top):
                px[x, y] = (214, 216, 222, 255)
            elif _inside(*point, left):
                px[x, y] = (156, 158, 166, 255)
            elif _inside(*point, right):
                px[x, y] = (92, 94, 102, 255)
    outlined = cube.copy()
    src = cube.load()
    out = outlined.load()
    for y in range(FRAME):
        for x in range(FRAME):
            if src[x, y][3] == 0:
                continue
            edge = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or ny < 0 or nx >= FRAME or ny >= FRAME or src[nx, ny][3] == 0:
                    edge = True
            if edge:
                out[x, y] = (36, 38, 42, 255)
    return outlined


def draw_icons() -> dict[str, Image.Image]:
    icons = {}
    icons["titanium"] = draw_titanium()

    chip = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    px = chip.load()
    for y in range(8, 19):
        for x in range(8, 19):
            edge = x in (8, 18) or y in (8, 18)
            core = 11 <= x <= 15 and 11 <= y <= 15
            if edge or core:
                px[x, y] = (236, 236, 236, 255)
    for pin in range(10, 17, 3):
        for x in (5, 6, 20, 21):
            px[x, pin] = (236, 236, 236, 255)
        for y in (5, 6, 20, 21):
            px[pin, y] = (236, 236, 236, 255)
    icons["microchips"] = chip

    cart = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    px = cart.load()
    for y in range(8, 16):
        for x in range(6, 21):
            px[x, y] = (244, 208, 40, 255)
    for y in range(15, 21):
        for x in range(5, 22):
            px[x, y] = (150, 154, 160, 255)
    for cx in (10, 17):
        for y in range(19, 25):
            for x in range(cx - 2, cx + 3):
                if (x - cx) ** 2 + (y - 21) ** 2 <= 5:
                    px[x, y] = (40, 40, 44, 255)
    px[13, 11] = (20, 20, 20, 255)
    for x, y in ((11, 10), (15, 10), (10, 13), (16, 13), (13, 9), (13, 14)):
        px[x, y] = (20, 20, 20, 255)
    icons["uranium"] = cart
    return icons


def fit_icon(path: Path, kind: str) -> Image.Image:
    source = Image.open(path).convert("RGBA")
    pixels = source.load()
    width, height = source.size
    if kind == "chip":
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if max(r, g, b) < 210:
                    pixels[x, y] = (0, 0, 0, 0)
    elif kind == "cube":
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if (r + g + b) / 3 < 96:
                    pixels[x, y] = (0, 0, 0, 0)
    elif kind == "cart":
        seen = [[False] * width for _ in range(height)]
        stack = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
        while stack:
            x, y = stack.pop()
            if x < 0 or y < 0 or x >= width or y >= height or seen[y][x]:
                continue
            r, g, b, a = pixels[x, y]
            if r < 235 or g < 235 or b < 235:
                continue
            seen[y][x] = True
            pixels[x, y] = (0, 0, 0, 0)
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    bbox = source.getbbox()
    if bbox:
        source = source.crop(bbox)
    source.thumbnail((22, 22), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    tile.paste(source, ((FRAME - source.width) // 2, (FRAME - source.height) // 2), source)
    return tile


def grey(tile: Image.Image) -> Image.Image:
    out = tile.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            tone = int((0.3 * r + 0.59 * g + 0.11 * b) * 0.62)
            pixels[x, y] = (tone, tone, tone, a)
    return out


def assemble(base: Image.Image, inserts: dict[int, Image.Image]) -> Image.Image:
    # Old frames 0-5, titanium, old 7-11, uranium, microchips, old coal frame 6.
    order = [0, 1, 2, 3, 4, 5, "titanium", 7, 8, 9, 10, 11, "uranium", "microchips", 6]
    strip = Image.new("RGBA", (FRAME * len(order), FRAME), (0, 0, 0, 0))
    for index, item in enumerate(order):
        if isinstance(item, str):
            tile = inserts[item]
        else:
            tile = base.crop((item * FRAME, 0, (item + 1) * FRAME, FRAME))
        strip.paste(tile, (index * FRAME, 0))
    return strip


def main() -> None:
    color = load_dds(ICONS / "resources_strip_12.dds")
    missing = load_dds(ICONS / "missing_resources_strip_12.dds")
    icons = draw_icons()
    color_template = (GFX / "resources_strip.dds").read_bytes()
    missing_template = (GFX / "missing_resources_strip.dds").read_bytes()
    save_dds(GFX / "resources_strip.dds", assemble(color, icons), color_template)
    save_dds(
        GFX / "missing_resources_strip.dds",
        assemble(missing, {name: grey(tile) for name, tile in icons.items()}),
        missing_template,
    )
    print("wrote strips")


if __name__ == "__main__":
    main()
