from pathlib import Path
from PIL import Image, ImageOps

src = Path("tools/_leader_src")
out = Path("tools/_portrait_preview")
for name in ["eas_aoc.jpg", "txg_abbott.jpg", "flo_desantis.webp", "sft_thiel_yarvin.webp"]:
    im = ImageOps.exif_transpose(Image.open(src / name)).convert("RGB")
    print(name, im.size)
    thumb = im.copy()
    thumb.thumbnail((400, 400))
    thumb.save(out / f"src_{Path(name).stem}.png")
