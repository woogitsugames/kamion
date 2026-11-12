"""Native crops side by side; no image scaling or tone adjustment."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
canvas = Image.new("RGB", (840, 320), (24, 24, 24))
draw = ImageDraw.Draw(canvas)
for index, condition in enumerate(("Low-overcast", "Low-clear", "High-overcast", "High-clear")):
    x = index * 210
    draw.text((x + 2, 3), condition, fill="white")
    for side, phase in enumerate(("before", "after-corrected")):
        draw.text((x + side * 103 + 2, 20), "before" if side == 0 else "after", fill="white")
        with Image.open(root / "review" / f"pier-{phase}" / f"{condition}-column.png") as im:
            canvas.paste(im.convert("RGB"), (x + side * 103 + 2, 43))
canvas.save(root / "review" / "pier-final-native-pair.jpg", quality=95)
