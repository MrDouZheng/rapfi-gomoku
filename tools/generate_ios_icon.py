# SPDX-FileCopyrightText: 2026 MrDouZheng and contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Generate the deterministic DouYi iOS app icon."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ios" / "DouYi" / "Assets.xcassets" / "AppIcon.appiconset" / "AppIcon-1024.png"


def main() -> None:
    size = 1024
    image = Image.new("RGB", (size, size), "#101416")
    draw = ImageDraw.Draw(image)

    # A warm wooden board crossed by two opposing stones: 斗而有弈。
    draw.rounded_rectangle((104, 104, 920, 920), radius=150, fill="#d49a50")
    for step in range(7):
        coordinate = 210 + step * 101
        draw.line((210, coordinate, 816, coordinate), fill="#76502a", width=10)
        draw.line((coordinate, 210, coordinate, 816), fill="#76502a", width=10)

    draw.ellipse((252, 252, 522, 522), fill="#090b0c", outline="#41494d", width=12)
    draw.ellipse((502, 502, 772, 772), fill="#f4f0e8", outline="#b9b7b0", width=12)
    draw.ellipse((712, 210, 806, 304), fill="#e8af4a")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", optimize=True)


if __name__ == "__main__":
    main()
