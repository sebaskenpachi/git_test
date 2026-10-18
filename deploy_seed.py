"""Material de prueba visual y narración provisional del editor."""
from pathlib import Path
from PIL import Image, ImageDraw

p = Path("/app/demo_assets")
p.mkdir(parents=True, exist_ok=True)
titles = ["UNA SEÑAL IMPOSIBLE", "UN CORREDOR PERDIDO", "LA EVIDENCIA", "LA TRANSMISIÓN"]
palettes = [(6, 26, 43), (9, 35, 28), (52, 31, 25), (27, 19, 55)]
for i, (title, base_color) in enumerate(zip(titles, palettes), 1):
    im = Image.new("RGB", (1280, 720), base_color)
    d = ImageDraw.Draw(im)
    for j in range(24):
        x = 110 + j * 44
        d.line((x, 80, x - 160, 640), fill=tuple(min(255, c + 18) for c in base_color), width=2)
    d.ellipse((420, 135, 840, 555), outline=(98 + i * 10, 134 + i * 10, 145), width=8)
    d.rectangle((270, 305, 1010, 415), fill=(8, 15, 25))
    d.text((300, 345), title, fill=(225, 234, 224), stroke_width=1)
    im.save(p / f"{i:02d}_demo.jpg", quality=90)
