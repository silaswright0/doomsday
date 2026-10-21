"""HOI4-style icons for every doomsday research tech and equipment.

Vanilla art is used only when it depicts that object. Everything else is a
shaded silhouette drawn at the size of the card it sits on. A bar on the
right marks the tier.
"""
import re
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

MOD = Path(r"c:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\mod\doomsday")
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\gfx\interface\technologies")
OUT = MOD / "gfx" / "interface" / "technologies" / "dd"
HEADER = bytearray((VANILLA / "infantry_weapons.dds").read_bytes()[:128])

INK = (52, 40, 30, 255)
MID = (92, 74, 54, 255)
DARK = (28, 20, 14, 255)
EDGE = (96, 78, 58, 255)


def load_dds(path):
    data = path.read_bytes()
    height, width = struct.unpack_from("<II", data, 12)
    need = 128 + width * height * 4
    if len(data) < need or width > 512 or height > 512:
        return None
    raw = Image.frombytes("RGBA", (width, height), data[128:need])
    b, g, r, a = raw.split()
    return Image.merge("RGBA", (r, g, b, a))


def save_dds(image, path):
    image = image.convert("RGBA")
    width, height = image.size
    r, g, b, a = image.split()
    bgra = Image.merge("RGBA", (b, g, r, a))
    header = bytearray(HEADER)
    struct.pack_into("<III", header, 12, height, width, width * height * 4)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(header) + bgra.tobytes())


def tier_of(name):
    nums = re.findall(r"\d+", name)
    if not nums:
        return 1
    return max(1, min(9, int(nums[-1])))


def stamp_tier(image, tier):
    draw = ImageDraw.Draw(image)
    width, height = image.size
    margin = max(1, round(height * 0.06))
    bar_w = max(2, round(min(width, height) * 0.08))
    span = max(2, height - margin * 2)
    bar_h = max(2, round(span * tier / 9))
    x1 = width - 1
    x0 = max(0, x1 - bar_w)
    y1 = height - margin
    y0 = max(0, y1 - bar_h)
    draw.rectangle((x0, y0, x1, y1), fill=EDGE)


def fit_vanilla(src, tier):
    image = src.copy()
    stamp_tier(image, tier)
    return image



def punch(image, box=None, ellipse=None, poly=None):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    if box is not None:
        draw.rectangle(box, fill=255)
    if ellipse is not None:
        draw.ellipse(ellipse, fill=255)
    if poly is not None:
        draw.polygon(poly, fill=255)
    image.putalpha(ImageChops.subtract(image.getchannel("A"), mask))


def shade(image):
    alpha = image.getchannel("A")
    rim = ImageChops.subtract(alpha, ImageChops.offset(alpha, 1, 2))
    foot = ImageChops.subtract(alpha, ImageChops.offset(alpha, -1, -2))
    highlight = Image.new("RGBA", image.size, (140, 116, 88, 255))
    highlight.putalpha(rim)
    shadow = Image.new("RGBA", image.size, (20, 14, 10, 230))
    shadow.putalpha(foot)
    image.alpha_composite(highlight)
    image.alpha_composite(shadow)


def wheel(image, cx, cy, radius):
    draw = ImageDraw.Draw(image)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=INK)
    inner = max(2, radius - 3)
    punch(image, ellipse=(cx - inner, cy - inner, cx + inner, cy + inner))
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=DARK)


def tracked_hull(draw, width):
    draw.polygon(
        [(16, 26), (width - 28, 24), (width - 16, 32), (width - 14, 44), (12, 44), (10, 34)],
        fill=INK,
    )
    draw.rounded_rectangle((8, 32, width - 12, 50), radius=7, fill=INK)


def draw_uav(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(6, 24), (70, 16), (144, 22), (144, 28), (70, 32), (6, 30)], fill=INK)
    draw.polygon([(48, 14), (108, 14), (116, 20), (112, 34), (44, 34), (36, 22)], fill=INK)
    draw.polygon([(100, 16), (124, 8), (128, 14), (104, 20)], fill=INK)
    draw.polygon([(100, 30), (124, 40), (128, 34), (104, 28)], fill=INK)
    draw.ellipse((40, 30, 52, 42), fill=INK)
    punch(image, ellipse=(43, 33, 49, 39))
    draw.polygon([(108, 18), (118, 18), (116, 30), (106, 30)], fill=MID)
    draw.line((18, 22, 132, 24), fill=MID, width=1)


def draw_uav_strike(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(8, 26), (74, 10), (146, 24), (146, 30), (74, 38), (8, 32)], fill=INK)
    draw.polygon([(62, 16), (92, 14), (96, 22), (90, 34), (58, 32)], fill=INK)
    draw.polygon([(78, 8), (86, 8), (84, 16), (76, 16)], fill=INK)
    punch(image, ellipse=(70, 18, 82, 26))
    draw.polygon([(40, 28), (52, 30), (48, 36)], fill=DARK)
    draw.polygon([(96, 28), (108, 30), (100, 36)], fill=DARK)


def draw_aew(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(18, 22), (132, 20), (148, 24), (146, 32), (22, 34), (12, 28)], fill=INK)
    draw.polygon([(36, 20), (128, 16), (132, 22), (40, 26)], fill=INK)
    draw.ellipse((52, 24, 66, 34), fill=DARK)
    draw.ellipse((96, 24, 110, 34), fill=DARK)
    draw.polygon([(124, 12), (140, 14), (132, 24), (120, 22)], fill=INK)
    draw.rectangle((78, 8, 82, 20), fill=INK)
    draw.ellipse((62, 2, 100, 16), fill=INK)
    punch(image, ellipse=(70, 5, 92, 13))
    draw.rectangle((74, 18, 88, 22), fill=MID)


def draw_mpa(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(10, 22), (140, 18), (156, 24), (150, 32), (16, 34), (8, 28)], fill=INK)
    draw.polygon([(28, 18), (136, 14), (140, 22), (32, 26)], fill=INK)
    for x in (48, 66, 92, 110):
        draw.ellipse((x, 22, x + 14, 34), fill=DARK)
    draw.polygon([(128, 10), (146, 12), (138, 24), (122, 22)], fill=INK)
    draw.polygon([(146, 24), (160, 26), (146, 30)], fill=INK)
    draw.ellipse((22, 20, 36, 30), fill=MID)
    punch(image, ellipse=(24, 22, 32, 28))


def draw_attack_heli(image):
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 12, 144, 16), fill=INK)
    draw.rectangle((70, 8, 76, 20), fill=INK)
    draw.polygon([(22, 26), (48, 20), (96, 22), (118, 28), (124, 36), (36, 40), (22, 34)], fill=INK)
    draw.polygon([(96, 28), (140, 30), (140, 36), (96, 36)], fill=INK)
    draw.rectangle((128, 20, 144, 24), fill=INK)
    draw.rectangle((132, 18, 136, 40), fill=INK)
    draw.polygon([(52, 32), (92, 32), (90, 38), (54, 38)], fill=DARK)
    draw.rectangle((58, 36, 62, 42), fill=DARK)
    draw.rectangle((80, 36, 84, 42), fill=DARK)
    draw.polygon([(24, 34), (40, 36), (36, 42), (22, 40)], fill=INK)
    draw.line((30, 40, 118, 44), fill=INK, width=2)
    draw.line((36, 46, 110, 50), fill=INK, width=2)
    draw.line((34, 40, 40, 50), fill=INK, width=2)
    draw.line((108, 44, 114, 50), fill=INK, width=2)
    punch(image, ellipse=(28, 24, 46, 34))
    draw.ellipse((30, 26, 42, 32), outline=MID)


def draw_manpad(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(16, 30), (28, 26), (108, 8), (116, 14), (36, 32)], fill=INK)
    draw.polygon([(22, 28), (34, 32), (30, 42), (18, 38)], fill=INK)
    draw.rectangle((26, 30, 32, 44), fill=DARK)
    draw.polygon([(70, 14), (86, 10), (88, 16), (72, 20)], fill=MID)
    draw.ellipse((100, 4, 118, 16), fill=INK)
    punch(image, ellipse=(106, 7, 114, 13))
    draw.polygon([(14, 28), (24, 26), (22, 32), (12, 34)], fill=MID)


def draw_mortar(image):
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 34, 78, 48), fill=INK)
    punch(image, ellipse=(28, 38, 68, 46))
    draw.line((36, 40, 22, 22), fill=INK, width=3)
    draw.line((58, 40, 78, 18), fill=INK, width=3)
    draw.polygon([(40, 36), (52, 38), (88, 8), (78, 6)], fill=INK)
    draw.ellipse((82, 2, 96, 14), fill=MID)
    draw.rectangle((46, 34, 52, 42), fill=DARK)


def draw_spaa(image):
    draw = ImageDraw.Draw(image)
    tracked_hull(draw, 131)
    for cx in (24, 40, 56, 72, 88, 104):
        wheel(image, cx, 42, 6)
    draw.polygon([(48, 18), (86, 16), (92, 28), (44, 30)], fill=INK)
    draw.polygon([(78, 18), (112, 4), (116, 8), (82, 22)], fill=INK)
    draw.polygon([(74, 20), (108, 8), (112, 12), (78, 24)], fill=DARK)
    draw.ellipse((58, 18, 74, 30), fill=MID)
    punch(image, ellipse=(62, 21, 70, 27))


def draw_shorad(image):
    draw = ImageDraw.Draw(image)
    tracked_hull(draw, 131)
    for cx in (26, 46, 66, 86, 106):
        wheel(image, cx, 42, 6)
    draw.polygon([(36, 22), (96, 20), (100, 32), (32, 34)], fill=INK)
    for x in (44, 56, 68, 80):
        draw.polygon([(x, 22), (x + 8, 20), (x + 12, 6), (x + 6, 6)], fill=DARK)
    draw.rectangle((40, 16, 92, 22), fill=MID)


def draw_spg(image):
    draw = ImageDraw.Draw(image)
    tracked_hull(draw, 131)
    for cx in (24, 42, 60, 78, 96, 112):
        wheel(image, cx, 42, 6)
    draw.polygon([(34, 16), (78, 14), (84, 30), (30, 32)], fill=INK)
    draw.polygon([(70, 16), (122, 12), (124, 18), (74, 22)], fill=INK)
    draw.rectangle((116, 10, 124, 20), fill=MID)
    punch(image, box=(40, 18, 58, 26))
    draw.rectangle((44, 28, 70, 32), fill=DARK)


def draw_laser(image):
    draw = ImageDraw.Draw(image)
    tracked_hull(draw, 131)
    for cx in (28, 48, 68, 88, 108):
        wheel(image, cx, 42, 6)
    draw.polygon([(46, 14), (84, 12), (90, 30), (42, 32)], fill=INK)
    draw.ellipse((54, 8, 78, 28), fill=INK)
    punch(image, ellipse=(60, 12, 74, 24))
    draw.ellipse((64, 15, 72, 22), fill=MID)
    draw.polygon([(78, 16), (120, 12), (120, 16), (78, 20)], fill=MID)


def draw_hpm(image):
    draw = ImageDraw.Draw(image)
    tracked_hull(draw, 131)
    for cx in (28, 50, 72, 94, 112):
        wheel(image, cx, 42, 5)
    draw.rectangle((24, 18, 46, 34), fill=INK)
    draw.polygon([(46, 22), (78, 6), (92, 14), (58, 30)], fill=INK)
    punch(image, ellipse=(58, 10, 84, 26))
    draw.arc((60, 12, 82, 28), 300, 80, fill=MID, width=2)
    draw.rectangle((18, 22, 26, 32), fill=MID)


def draw_vls(image):
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=4, fill=INK)
    for col in range(3):
        for row in range(3):
            x = 14 + col * 14
            y = 14 + row * 14
            draw.rounded_rectangle((x, y, x + 10, y + 10), radius=2, fill=DARK)
            punch(image, ellipse=(x + 2, y + 2, x + 8, y + 8))
            draw.ellipse((x + 3, y + 3, x + 7, y + 7), outline=MID)


def draw_ciws(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(10, 48), (54, 48), (48, 36), (16, 36)], fill=INK)
    draw.ellipse((18, 22, 46, 46), fill=INK)
    punch(image, ellipse=(24, 26, 40, 40))
    draw.ellipse((28, 30, 36, 38), fill=MID)
    for i in range(6):
        y = 16 + i * 3
        draw.line((36, 30, 58, y), fill=DARK, width=2)
    draw.rectangle((34, 14, 58, 18), fill=INK)


def draw_cyber(image):
    draw = ImageDraw.Draw(image)
    nodes = ((32, 32), (12, 14), (50, 12), (14, 50), (52, 48), (32, 8), (32, 54))
    for cx, cy in nodes[1:]:
        draw.line((cx, cy, 32, 32), fill=INK, width=2)
    for cx, cy in nodes:
        r = 8 if (cx, cy) == (32, 32) else 5
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK)
        punch(image, ellipse=(cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2))
        draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=MID)


def draw_satellite(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(6, 22), (24, 26), (24, 38), (6, 42)], fill=INK)
    draw.polygon([(58, 22), (40, 26), (40, 38), (58, 42)], fill=INK)
    for x in (8, 14, 20, 42, 48, 54):
        draw.line((x, 26, x, 38), fill=MID, width=1)
    draw.rounded_rectangle((26, 22, 40, 42), radius=2, fill=INK)
    draw.rectangle((30, 10, 34, 22), fill=INK)
    draw.ellipse((24, 4, 40, 16), fill=INK)
    punch(image, ellipse=(28, 7, 36, 13))
    draw.rectangle((28, 28, 38, 30), fill=MID)
    draw.rectangle((28, 34, 38, 36), fill=MID)


def draw_nv(image):
    draw = ImageDraw.Draw(image)
    draw.arc((8, 10, 56, 28), 200, 340, fill=INK, width=3)
    draw.rounded_rectangle((6, 24, 28, 46), radius=8, fill=INK)
    draw.rounded_rectangle((36, 24, 58, 46), radius=8, fill=INK)
    draw.rectangle((26, 30, 38, 38), fill=INK)
    punch(image, ellipse=(10, 28, 24, 42))
    punch(image, ellipse=(40, 28, 54, 42))
    draw.ellipse((14, 32, 20, 38), fill=MID)
    draw.ellipse((44, 32, 50, 38), fill=MID)
    draw.rectangle((18, 18, 22, 26), fill=INK)
    draw.rectangle((42, 18, 46, 26), fill=INK)


def draw_usv(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(16, 28), (200, 26), (214, 34), (196, 44), (28, 44), (8, 36)], fill=INK)
    draw.polygon([(70, 16), (130, 14), (136, 28), (64, 30)], fill=INK)
    punch(image, box=(84, 18, 112, 26))
    draw.rectangle((96, 6, 100, 16), fill=INK)
    draw.ellipse((88, 2, 108, 12), fill=INK)
    punch(image, ellipse=(94, 4, 104, 10))
    draw.polygon([(150, 20), (168, 16), (166, 28), (148, 28)], fill=DARK)
    draw.line((24, 34, 190, 32), fill=MID, width=1)


def draw_uuv(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(16, 12), (150, 10), (176, 16), (150, 24), (16, 22), (8, 16)], fill=INK)
    draw.polygon([(20, 12), (8, 4), (16, 12)], fill=INK)
    draw.polygon([(20, 22), (8, 30), (16, 22)], fill=INK)
    draw.ellipse((168, 12, 186, 22), fill=DARK)
    for y in (6, 26):
        draw.polygon([(120, 14), (132, y), (140, 16)], fill=INK)
    punch(image, ellipse=(28, 14, 40, 20))
    draw.ellipse((148, 13, 158, 21), fill=MID)


def draw_bike(image):
    draw = ImageDraw.Draw(image)
    wheel(image, 22, 36, 12)
    wheel(image, 78, 36, 12)
    draw.line((22, 36, 48, 28), fill=INK, width=3)
    draw.line((48, 28, 78, 36), fill=INK, width=3)
    draw.line((48, 28, 40, 18), fill=INK, width=3)
    draw.line((34, 16, 52, 16), fill=INK, width=3)
    draw.polygon([(40, 14), (52, 12), (56, 22), (44, 26)], fill=INK)
    draw.ellipse((46, 6, 58, 16), fill=INK)
    punch(image, ellipse=(49, 8, 55, 14))
    draw.line((22, 36, 58, 30), fill=DARK, width=2)


def draw_harbor(image):
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 30, 200, 36), fill=INK)
    for x in (16, 52, 88, 124, 160):
        draw.rectangle((x, 34, x + 28, 46), fill=INK)
        draw.line((x + 6, 36, x + 6, 44), fill=MID, width=1)
        draw.line((x + 14, 36, x + 14, 44), fill=MID, width=1)
    draw.rectangle((168, 12, 174, 32), fill=INK)
    draw.line((174, 14, 198, 22), fill=INK, width=2)
    draw.line((188, 20, 188, 30), fill=DARK, width=1)


def draw_tender(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(12, 28), (200, 24), (214, 34), (190, 44), (24, 44), (8, 36)], fill=INK)
    draw.polygon([(70, 12), (132, 12), (138, 28), (64, 28)], fill=INK)
    draw.rectangle((40, 16, 62, 30), fill=DARK)
    draw.rectangle((148, 8, 154, 28), fill=INK)
    draw.line((154, 10, 184, 18), fill=INK, width=2)
    draw.line((170, 16, 170, 28), fill=DARK, width=1)
    punch(image, box=(80, 16, 100, 24))
    punch(image, box=(106, 16, 124, 24))
    draw.line((20, 34, 196, 32), fill=MID, width=1)


def draw_buzz(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(12, 20), (96, 16), (108, 22), (96, 28), (12, 26), (6, 22)], fill=INK)
    draw.polygon([(28, 18), (112, 14), (116, 20), (32, 24)], fill=INK)
    draw.polygon([(78, 8), (108, 10), (100, 20), (74, 18)], fill=INK)
    draw.rectangle((92, 6, 104, 16), fill=DARK)
    draw.polygon([(70, 12), (86, 4), (90, 10), (74, 16)], fill=MID)
    draw.ellipse((8, 18, 20, 28), fill=MID)


def draw_armor(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(8, 28), (78, 10), (112, 18), (112, 34), (18, 36)], fill=INK)
    for x in (28, 44, 60, 76):
        draw.rectangle((x, 16, x + 12, 26), fill=DARK)
        draw.rectangle((x + 2, 18, x + 10, 24), fill=MID)
    draw.polygon([(86, 8), (104, 4), (108, 16), (90, 18)], fill=INK)
    draw.ellipse((96, 6, 106, 14), fill=MID)
    draw.rectangle((10, 32, 108, 36), fill=DARK)


def draw_sight(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(8, 24), (96, 20), (100, 28), (8, 30)], fill=INK)
    draw.rectangle((92, 18, 112, 30), fill=DARK)
    draw.rounded_rectangle((28, 8, 62, 24), radius=3, fill=INK)
    punch(image, ellipse=(36, 11, 54, 22))
    draw.ellipse((40, 13, 50, 20), fill=MID)
    draw.polygon([(62, 12), (108, 6), (108, 10), (64, 16)], fill=MID)
    draw.rectangle((18, 26, 24, 34), fill=INK)


def draw_shell(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(16, 16), (28, 6), (36, 16), (40, 50), (12, 50)], fill=INK)
    draw.polygon([(18, 14), (26, 8), (30, 16)], fill=MID)
    draw.rectangle((12, 28, 40, 32), fill=DARK)
    draw.rectangle((14, 48, 38, 56), fill=INK)
    draw.rectangle((18, 40, 34, 44), fill=MID)


DRAW_SIZE = {
    "uav": (150, 48),
    "uav_strike": (150, 48),
    "aew": (164, 46),
    "mpa": (164, 46),
    "attack_heli": (150, 54),
    "manpad": (124, 46),
    "mortar": (110, 50),
    "spaa": (131, 52),
    "shorad": (131, 52),
    "spg": (131, 52),
    "laser": (131, 52),
    "hpm": (131, 52),
    "vls": (64, 64),
    "ciws": (64, 64),
    "cyber": (64, 64),
    "satellite": (64, 64),
    "nv": (64, 64),
    "usv": (220, 50),
    "uuv": (190, 34),
    "bike": (100, 52),
    "harbor": (206, 50),
    "tender": (220, 48),
    "buzz": (120, 36),
    "shell": (48, 64),
    "armor": (120, 40),
    "sight": (120, 36),
}

DRAWN = {
    "uav": draw_uav,
    "uav_strike": draw_uav_strike,
    "aew": draw_aew,
    "mpa": draw_mpa,
    "attack_heli": draw_attack_heli,
    "manpad": draw_manpad,
    "mortar": draw_mortar,
    "spaa": draw_spaa,
    "shorad": draw_shorad,
    "spg": draw_spg,
    "laser": draw_laser,
    "hpm": draw_hpm,
    "vls": draw_vls,
    "ciws": draw_ciws,
    "cyber": draw_cyber,
    "satellite": draw_satellite,
    "nv": draw_nv,
    "usv": draw_usv,
    "uuv": draw_uuv,
    "bike": draw_bike,
    "harbor": draw_harbor,
    "tender": draw_tender,
    "buzz": draw_buzz,
    "shell": draw_shell,
    "armor": draw_armor,
    "sight": draw_sight,
}

# Wide air weapons and attackers were covering the one-line title.
ICON_LIMIT = {
    "cas": (100, 30),
    "guided": (100, 28),
}

VANILLA_FILE = {
    "rifle": "infantry_weapons.dds",
    "truck": "motorized_equipment_1.dds",
    "apc": "mechanized_equipment_1.dds",
    "car": "ger_armored_car_equipment_2.dds",
    "support_vehicle": "generic_armored_support_vehicle.dds",
    "amphib_tank": "generic_amphibious_tank_2.dds",
    "amphib_mech": "generic_amphibious_mech_2.dds",
    "flame": "generic_medium_flame_tank.dds",
    "support": "support_weapons.dds",
    "at": "anti_tank_equipment.dds",
    "aa_towed": "anti_air_equipment.dds",
    "lighttank": "basic_light_tank.dds",
    "medium": "basic_medium_tank.dds",
    "heavy": "basic_heavy_tank.dds",
    "superheavy": "super_heavy_tank.dds",
    "mbt": "generic_modern_tank.dds",
    "landcruiser": "generic_land_cruiser_chassis.dds",
    "gwtank": "gwtank.dds",
    "fcs": "basic_fire_control_system.dds",
    "td": "GER_modern_td.dds",
    "gun": "artillery_equipment.dds",
    "railway": "generic_super_heavy_artillery.dds",
    "rocket": "rocket_artillery_equipment.dds",
    "sam": "sam_missile_equipment.dds",
    "guided": "guided_missile_2.dds",
    "ballistic": "ballistic_missile_equipment_2.dds",
    "nuclear_missile": "nuclear_missile_equipment_1.dds",
    "fighter": "fighter2.dds",
    "heavy_fighter": "heavy_fighter2.dds",
    "jet": "generic_supersonic_jet_plane.dds",
    "cas": "CAS3.dds",
    "tac": "tactical_bomber2.dds",
    "jet_tac": "jet_tactical_bomber2.dds",
    "bomber": "strategic_bomber2.dds",
    "jet_strat": "jet_strategic_bomber1.dds",
    "scout": "generic_scout_plane_2_2.dds",
    "nav": "naval_bomber2.dds",
    "rocket_plane": "rocket_interceptor_2.dds",
    "heli": "generic_helicopter.dds",
    "destroyer": "basic_destroyer.dds",
    "destroyer_mod": "modern_destroyer.dds",
    "cruiser": "basic_light_cruiser.dds",
    "cruiser_hvy": "basic_heavy_cruiser.dds",
    "cruiser_mod": "modern_heavy_cruiser.dds",
    "battleship": "basic_battleship.dds",
    "battleship_mod": "modern_battleship.dds",
    "battlecruiser": "basic_battlecruiser.dds",
    "carrier": "basic_carrier.dds",
    "carrier_mod": "modern_carrier.dds",
    "escort_carrier": "ship_hull_escort_carrier.dds",
    "super_carrier": "ship_hull_super_carrier.dds",
    "sub": "basic_submarine.dds",
    "sub_mod": "modern_submarine.dds",
    "nuclear_sub": "generic_ship_hull_nuclear_powered_submarine.dds",
    "ssbn": "generic_ship_hull_nuclear_powered_submarine.dds",
    "midget": "ship_hull_midget_submarine.dds",
    "fleet_sub": "ship_hull_fleet_submarine.dds",
    "cruiser_sub": "generic_ship_hull_cruiser_submarine.dds",
    "landing": "tank_landing_craft.dds",
    "transport": "generic_transport_plane_equipment_1.dds",
    "super_spg": "generic_self_propelled_super_heavy_artillery.dds",
    "convoy": "convoy.dds",
    "train": "train_equipment_2.dds",
    "ngun": "basic_medium_battery.dds",
    "torpedo": "basic_torpedo.dds",
    "sonar": "sonar.dds",
    "engine": "bba_tech_engines_2.dds",
    "radar": "centimetric_radar.dds",
    "radio": "radio.dds",
    "cpu": "computing_machine.dds",
    "lock": "basic_encryption.dds",
    "nuke": "atomic_research.dds",
    "factory": "concentrated_industry.dds",
    "excavator": "excavation2.dds",
    "oil": "oil_processing.dds",
    "construction": "basic_construction.dds",
    "fuel": "synth_oil_experiments.dds",
    "hospital": "tech_field_hospital.dds",
    "logistics": "tech_logistics_company.dds",
    "mp": "tech_military_police.dds",
    "signal": "tech_signal_company.dds",
    "mountain": "rangers_tech2.dds",
    "engineer": "engineers2.dds",
    "sf": "tech_special_forces.dds",
    "binoculars": "recon2.dds",
}

TECH_FAMILY = [
    ("dd_truck", "truck"),
    ("dd_mech", "apc"),
    ("dd_supkit", "support"),
    ("dd_sup", "support"),
    ("dd_inf", "rifle"),
    ("dd_atg", "at"),
    ("dd_at", "at"),
    ("dd_manpad", "manpad"),
    ("dd_nv", "nv"),
    ("dd_sf", "sf"),
    ("dd_lt", "lighttank"),
    ("dd_mbt", "mbt"),
    ("dd_prot", "armor"),
    ("dd_fcs", "sight"),
    ("dd_td", "td"),
    ("dd_spaa", "spaa"),
    ("dd_tow", "gun"),
    ("dd_spg", "spg"),
    ("dd_mor", "mortar"),
    ("dd_rkt", "rocket"),
    ("dd_shorad", "shorad"),
    ("dd_sam", "sam"),
    ("dd_dew", "laser"),
    ("dd_cvf", "jet"),
    ("dd_ftr", "jet"),
    ("dd_cas", "cas"),
    ("dd_tac", "jet_tac"),
    ("dd_str", "jet_strat"),
    ("dd_uav", "uav"),
    ("dd_hel", "heli"),
    ("dd_isr", "scout"),
    ("dd_wpn", "guided"),
    ("dd_nbm", "mpa"),
    ("dd_mpa", "mpa"),
    ("dd_ssbn", "ssbn"),
    ("dd_ssn", "nuclear_sub"),
    ("dd_ssk", "sub_mod"),
    ("dd_usv", "usv"),
    ("dd_amph", "landing"),
    ("dd_esc", "destroyer_mod"),
    ("dd_cg", "cruiser_mod"),
    ("dd_cv", "carrier_mod"),
    ("dd_ngun", "ngun"),
    ("dd_vls", "vls"),
    ("dd_ciws", "ciws"),
    ("dd_torp", "torpedo"),
    ("dd_son", "sonar"),
    ("dd_neng", "engine"),
    ("dd_nav", "radar"),
    ("dd_dc", "construction"),
    ("dd_tol", "factory"),
    ("dd_con", "construction"),
    ("dd_dis", "factory"),
    ("dd_fuel", "fuel"),
    ("dd_syn", "oil"),
    ("dd_mat", "factory"),
    ("dd_bld", "construction"),
    ("dd_ext", "excavator"),
    ("dd_nrg", "oil"),
    ("dd_slot", "factory"),
    ("dd_rad", "radio"),
    ("dd_rdr", "radar"),
    ("dd_cpu", "cpu"),
    ("dd_cry", "lock"),
    ("dd_cyb", "cyber"),
    ("dd_ew", "radar"),
    ("dd_spc", "satellite"),
    ("dd_nuke", "nuke"),
    ("dd_eng", "engineer"),
    ("dd_rec", "binoculars"),
    ("dd_hos", "hospital"),
    ("dd_log", "logistics"),
    ("dd_mp", "mp"),
    ("dd_sig", "signal"),
    ("dd_mnt", "mountain"),
    ("dd_ewc", "cyber"),
    ("dd_irregulars", "rifle"),
]

# First matching needle wins. Specific gear comes before the generic word it contains.
EQUIP_RULES = [
    ("train_equipment", "train"),
    ("motorbike", "bike"),
    ("floating_harbor", "harbor"),
    ("explosive_ammo", "shell"),
    ("mothership", "jet_strat"),
    ("hypersonic", "guided"),
    ("nuclear_missile_submarine", "ssbn"),
    ("rocket_submarine", "ssbn"),
    ("nuclear_missile", "nuclear_missile"),
    ("ballistic_missile", "ballistic"),
    ("guided_missile", "guided"),
    ("prsm", "ballistic"),
    ("mrc_", "ballistic"),
    ("loitering", "uav_strike"),
    ("strike_uav", "uav_strike"),
    ("cca_strike", "uav_strike"),
    ("recon_uav", "uav"),
    ("hale_uav", "uav"),
    ("cca_", "uav"),
    ("uav", "uav"),
    ("manpads", "manpad"),
    ("manpad", "manpad"),
    ("dew_", "laser"),
    ("hpm_", "hpm"),
    ("shorad", "shorad"),
    ("ifpc", "sam"),
    ("sam_", "sam"),
    ("attack_heli", "attack_heli"),
    ("transport_heli", "heli"),
    ("helicopter", "heli"),
    ("aew_", "aew"),
    ("mpa_", "mpa"),
    ("maritime", "mpa"),
    ("nav_bomber", "nav"),
    ("naval_bomber", "nav"),
    ("strat_bomber_equipment_cw", "jet_strat"),
    ("intercontinental", "jet_strat"),
    ("jet_strat", "jet_strat"),
    ("strat_bomber", "bomber"),
    ("tac_bomber_equipment_cw", "jet_tac"),
    ("jet_tac", "jet_tac"),
    ("tac_bomber", "tac"),
    ("jet_fighter", "jet"),
    ("supersonic", "jet"),
    ("fighter_equipment_cw", "jet"),
    ("heavy_fighter", "heavy_fighter"),
    ("scout_plane", "scout"),
    ("rocket_interceptor", "rocket_plane"),
    ("rocket_suicide", "buzz"),
    ("suicide", "buzz"),
    ("cas", "cas"),
    ("transport_plane", "transport"),
    ("land_cruiser", "landcruiser"),
    ("tank_destroyer", "td"),
    ("td_equipment", "td"),
    ("self_propelled_super_heavy", "super_spg"),
    ("mega_carrier", "super_carrier"),
    ("modern_carrier", "carrier_mod"),
    ("ship_hull_ssbn", "ssbn"),
    ("ssbn", "ssbn"),
    ("midget_submarine", "midget"),
    ("cruiser_submarine", "cruiser_sub"),
    ("fleet_submarine", "fleet_sub"),
    ("ship_hull_nuclear", "nuclear_sub"),
    ("nuclear_submarine", "nuclear_sub"),
    ("ship_hull_submarine_cw", "sub_mod"),
    ("ship_hull_submarine_diesel", "sub_mod"),
    ("uuv", "uuv"),
    ("submarine", "sub"),
    ("ship_hull_usv", "usv"),
    ("usv", "usv"),
    ("ship_hull_amphib", "landing"),
    ("amphibious_mechanized", "amphib_mech"),
    ("amphibious_tank", "amphib_tank"),
    ("tank_amphibious", "amphib_tank"),
    ("ship_hull_mega", "super_carrier"),
    ("ship_hull_super_carrier", "super_carrier"),
    ("escort_carrier", "escort_carrier"),
    ("ship_hull_carrier_cw", "carrier_mod"),
    ("ship_hull_carrier_modern", "carrier_mod"),
    ("carrier", "carrier"),
    ("modern_battleship", "battleship_mod"),
    ("battle_cruiser", "battlecruiser"),
    ("battleship", "battleship"),
    ("ship_hull_heavy_modern", "battleship_mod"),
    ("ship_hull_pre_dreadnought", "battleship"),
    ("ship_hull_heavy", "battleship"),
    ("ship_hull_super_heavy", "battleship"),
    ("torpedo_cruiser", "cruiser"),
    ("heavy_cruiser", "cruiser_hvy"),
    ("light_cruiser", "cruiser"),
    ("ship_hull_cruiser_cw", "cruiser_mod"),
    ("ship_hull_cruiser", "cruiser"),
    ("cruiser", "cruiser"),
    ("ship_hull_light_cw", "destroyer_mod"),
    ("destroyer", "destroyer"),
    ("ship_hull_light", "destroyer"),
    ("convoy", "convoy"),
    ("repair_ship", "tender"),
    ("support_ship", "tender"),
    ("flame", "flame"),
    ("tank_aa", "spaa"),
    ("spaa", "spaa"),
    ("tank_artillery", "spg"),
    ("land_cruiser", "landcruiser"),
    ("super_heavy_tank", "superheavy"),
    ("gw_tank", "gwtank"),
    ("mbt_", "mbt"),
    ("modern_tank", "mbt"),
    ("heavy_tank", "heavy"),
    ("medium_tank", "medium"),
    ("light_tank", "lighttank"),
    ("tank_destroyer", "td"),
    ("td_equipment", "td"),
    ("spg_", "spg"),
    ("railway_gun", "railway"),
    ("super_heavy_railway", "railway"),
    ("super_heavy_artillery", "railway"),
    ("mortar", "mortar"),
    ("rocket_artillery", "rocket"),
    ("motorized_rocket", "rocket"),
    ("artillery", "gun"),
    ("infantry_at", "manpad"),
    ("armored_car_at", "car"),
    ("anti_tank", "at"),
    ("anti_air", "aa_towed"),
    ("mechanized", "apc"),
    ("bmd_", "apc"),
    ("armored_car", "car"),
    ("armored_support", "support_vehicle"),
    ("motorized", "truck"),
    ("infantry", "rifle"),
    ("support_equipment", "support"),
    ("large_plane_maritime", "mpa"),
    ("medium_plane_scout", "scout"),
    ("medium_plane_fighter", "heavy_fighter"),
    ("small_plane_naval", "nav"),
    ("small_plane_cas", "cas"),
    ("small_plane_suicide", "buzz"),
    ("cas_airframe", "cas"),
    ("naval_bomber_airframe", "nav"),
    ("large_plane", "bomber"),
    ("medium_plane", "tac"),
    ("small_plane", "fighter"),
    ("fighter", "fighter"),
    ("airframe", "fighter"),
]


def family_for_tech(tech):
    for prefix, family in sorted(TECH_FAMILY, key=lambda item: -len(item[0])):
        if tech == prefix or tech.startswith(prefix + "_"):
            return family
    return "rifle"


def family_for_equipment(name):
    low = name.lower()
    for needle, family in EQUIP_RULES:
        if needle in low:
            return family
    return "rifle"


_CACHE = {}


def limit_icon(image, family):
    cap = ICON_LIMIT.get(family)
    if cap is None or (image.width <= cap[0] and image.height <= cap[1]):
        return image
    fitted = image.copy()
    fitted.thumbnail(cap, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", cap, (0, 0, 0, 0))
    canvas.alpha_composite(fitted, ((cap[0] - fitted.width) // 2, (cap[1] - fitted.height) // 2))
    return canvas


def render(family, tier):
    key = (family, tier)
    if key in _CACHE:
        return _CACHE[key].copy()
    vanilla_name = VANILLA_FILE.get(family)
    src = load_dds(VANILLA / vanilla_name) if vanilla_name and (VANILLA / vanilla_name).exists() else None
    if src is not None:
        image = limit_icon(src, family)
        stamp_tier(image, tier)
    else:
        width, height = DRAW_SIZE.get(family, (64, 64))
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        drawer = DRAWN.get(family, draw_shell)
        drawer(image)
        shade(image)
        stamp_tier(image, tier)
    _CACHE[key] = image
    return image.copy()


def tech_names():
    gfx = (MOD / "interface" / "doomsday_techicons.gfx").read_text(encoding="utf-8")
    names = []
    for match in re.finditer(r'name = "GFX_(dd_[^"]+)"', gfx):
        tech = match.group(1)
        if tech.endswith("_medium") or tech in names:
            continue
        names.append(tech)
    if "dd_irregulars" not in names:
        names.append("dd_irregulars")
    return names


def equipment_names():
    root = MOD / "common" / "units" / "equipment"
    skip_files = {"plane_filters.txt", "tank_filters.txt"}
    found = []
    for path in sorted(root.glob("*.txt")):
        if path.name in skip_files:
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.match(r"\t([A-Za-z][A-Za-z0-9_]*) = \{", line)
            if match:
                found.append(match.group(1))
    return found


def write_gfx(techs, equips):
    lines = ["spriteTypes = {", ""]
    for tech in techs:
        rel = f"gfx/interface/technologies/dd/{tech}.dds"
        for suffix in ("", "_medium"):
            lines.append("\tspriteType = {")
            lines.append(f'\t\tname = "GFX_{tech}{suffix}"')
            lines.append(f'\t\ttexturefile = "{rel}"')
            lines.append("\t}")
            lines.append("")
    for equip in equips:
        rel = f"gfx/interface/technologies/dd/eq_{equip}.dds"
        for suffix in ("", "_medium"):
            lines.append("\tspriteType = {")
            lines.append(f'\t\tname = "GFX_{equip}{suffix}"')
            lines.append(f'\t\ttexturefile = "{rel}"')
            lines.append("\t}")
            lines.append("")
    lines.append("}")
    lines.append("")
    (MOD / "interface" / "doomsday_techicons.gfx").write_text("\n".join(lines), encoding="utf-8")


def stamp_equipment_pictures():
    root = MOD / "common" / "units" / "equipment"
    skip_files = {"plane_filters.txt", "tank_filters.txt"}
    changed = 0
    for path in root.glob("*.txt"):
        if path.name in skip_files:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        out = []
        i = 0
        while i < len(lines):
            match = re.match(r"\t([A-Za-z][A-Za-z0-9_]*) = \{", lines[i])
            if not match:
                out.append(lines[i])
                i += 1
                continue
            name = match.group(1)
            block = [lines[i]]
            depth = lines[i].count("{") - lines[i].count("}")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
            picture_at = None
            for index, line in enumerate(block[1:], start=1):
                if re.match(r"\t\tpicture = ", line) and not line.lstrip().startswith("#"):
                    picture_at = index
                    break
            new_line = f"\t\tpicture = {name}"
            if picture_at is None:
                block.insert(1, new_line)
                changed += 1
            elif block[picture_at].strip() != f"picture = {name}":
                block[picture_at] = new_line
                changed += 1
            out.extend(block)
        newline = "\n" if text.endswith("\n") else ""
        path.write_text("\n".join(out) + newline, encoding="utf-8")
    return changed


def contact_sheet():
    families = list(DRAWN)
    cell_w, cell_h = 240, 70
    cols = 3
    rows = (len(families) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (196, 176, 140))
    for index, family in enumerate(families):
        icon = render(family, 3)
        x = (index % cols) * cell_w + max(0, (cell_w - icon.width) // 2)
        y = (index // cols) * cell_h + max(0, (cell_h - icon.height) // 2)
        sheet.paste(icon, (x, y), icon)
    preview = MOD / "tools" / "_icon_sheet.png"
    sheet.save(preview)
    return preview, families


def main():
    techs = tech_names()
    equips = equipment_names()
    for tech in techs:
        image = render(family_for_tech(tech), tier_of(tech))
        save_dds(image, OUT / f"{tech}.dds")
    for equip in equips:
        image = render(family_for_equipment(equip), tier_of(equip))
        save_dds(image, OUT / f"eq_{equip}.dds")
    write_gfx(techs, equips)
    pictures = stamp_equipment_pictures()
    preview, families = contact_sheet()
    missing_vanilla = [name for name, filename in VANILLA_FILE.items() if not (VANILLA / filename).exists()]
    odd = [name for name in equips if family_for_equipment(name) == "rifle" and "infantry" not in name.lower()]
    print("techs", len(techs), "equipment", len(equips), "pictures", pictures)
    print("families", len(families))
    print("missing vanilla", missing_vanilla)
    print("unmapped", odd)
    print("preview", preview)


if __name__ == "__main__":
    main()
