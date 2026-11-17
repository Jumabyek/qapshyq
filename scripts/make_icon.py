"""Draw the Qapshyq logo and save it as PNG, ICO (Windows) and ICNS (macOS).

Run once:  python scripts/make_icon.py      (needs: pip install pillow)
"""
from pathlib import Path
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def draw(size: int = 1024) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size / 1024  # scale factor: the design is made on a 1024 grid

    # Rounded square with a blue -> violet gradient.
    bg = QPainterPath()
    bg.addRoundedRect(QRectF(64 * s, 64 * s, 896 * s, 896 * s), 210 * s, 210 * s)
    gradient = QLinearGradient(QPointF(64 * s, 64 * s), QPointF(960 * s, 960 * s))
    gradient.setColorAt(0, QColor("#5b7cff"))
    gradient.setColorAt(1, QColor("#8b5cf6"))
    p.fillPath(bg, gradient)

    # White box (the "qapshyq" / pouch) with a lid.
    body = QPainterPath()
    body.addRoundedRect(QRectF(262 * s, 400 * s, 500 * s, 400 * s), 56 * s, 56 * s)
    p.fillPath(body, QColor("#ffffff"))
    lid = QPainterPath()
    lid.addRoundedRect(QRectF(232 * s, 300 * s, 560 * s, 140 * s), 48 * s, 48 * s)
    p.fillPath(lid, QColor("#eef1ff"))

    # Zipper teeth down the middle.
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#6d72f6"))
    y = 330
    left = True
    while y < 770:
        x = 486 if left else 512
        p.drawRoundedRect(QRectF(x * s, y * s, 26 * s, 22 * s), 6 * s, 6 * s)
        y += 30
        left = not left
    # Zipper pull.
    p.setBrush(QColor("#4a4fe0"))
    p.drawRoundedRect(QRectF(470 * s, 250 * s, 84 * s, 120 * s), 30 * s, 30 * s)
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(496 * s, 276 * s, 32 * s, 52 * s), 14 * s, 14 * s)
    p.end()
    return img


def main() -> None:
    QGuiApplication(sys.argv)
    ASSETS.mkdir(exist_ok=True)
    png = ASSETS / "icon.png"
    draw(1024).save(str(png))
    from PIL import Image  # pillow

    image = Image.open(png)
    image.save(ASSETS / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                           (64, 64), (128, 128), (256, 256)])
    image.save(ASSETS / "icon.icns")
    print("Saved icon.png, icon.ico, icon.icns to", ASSETS)


if __name__ == "__main__":
    main()
