"""Deterministic TorchOS home-screen icon (80x80 PNG, BlackBerry OS7 480x640 class)."""
import sys
from PIL import Image, ImageDraw

S = 4  # supersample
W = 80 * S
BG, INK, MINT, AMBER = (16, 29, 40, 255), (237, 244, 247, 255), (130, 227, 194, 255), (255, 179, 71, 255)

img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([2 * S, 2 * S, 78 * S, 78 * S], radius=16 * S, fill=BG, outline=(45, 65, 79, 255), width=2 * S)
# torch flame: outer mint, inner amber
d.polygon([(40 * S, 10 * S), (54 * S, 30 * S), (50 * S, 42 * S), (40 * S, 47 * S), (30 * S, 42 * S), (26 * S, 30 * S)], fill=MINT)
d.polygon([(40 * S, 22 * S), (47 * S, 34 * S), (44 * S, 41 * S), (40 * S, 43 * S), (36 * S, 41 * S), (33 * S, 34 * S)], fill=AMBER)
# torch handle
d.rounded_rectangle([35 * S, 46 * S, 45 * S, 52 * S], radius=2 * S, fill=INK)
# terminal prompt >_
d.line([(18 * S, 58 * S), (26 * S, 64 * S), (18 * S, 70 * S)], fill=MINT, width=4 * S, joint="curve")
d.line([(31 * S, 70 * S), (44 * S, 70 * S)], fill=INK, width=4 * S)
img.resize((80, 80), Image.LANCZOS).save(sys.argv[1], optimize=True)
