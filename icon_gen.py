from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPainterPath
from PySide6.QtCore import Qt

def create_app_icon():
    """
    Generates a simple custom icon for the application.
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw a stylized eyedropper/color circle
    # Background circle
    painter.setBrush(QColor("#ffffff"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, 56, 56)

    # Inner circle (black)
    painter.setBrush(QColor("#000000"))
    painter.drawEllipse(12, 12, 40, 40)

    # Droplet shape
    path = QPainterPath()
    path.moveTo(32, 16)
    path.cubicTo(48, 16, 48, 40, 32, 48)
    path.cubicTo(16, 40, 16, 16, 32, 16)

    painter.setBrush(QColor("#ffffff"))
    painter.drawPath(path)

    painter.end()

    return QIcon(pixmap)

def create_gear_icon():
    """
    Generates a gear/settings icon.
    """
    size = 40
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Center
    cx, cy = size / 2, size / 2

    painter.setBrush(QColor("#e0e0e0"))
    painter.setPen(Qt.NoPen)

    # Draw gear teeth (circle with notches)
    # Simplify: Draw a star-like shape or just a ring with teeth

    painter.save()
    painter.translate(cx, cy)

    # Draw 8 teeth
    for i in range(8):
        painter.rotate(45)
        painter.drawRect(-3, -14, 6, 8)

    painter.restore()

    # Main body
    painter.drawEllipse(QPoint(int(cx), int(cy)), 11, 11)

    # Inner hole (transparent/background color)
    painter.setBrush(QColor("#121212")) # Match background or make transparent via CompositionMode
    painter.setCompositionMode(QPainter.CompositionMode_Clear)
    painter.drawEllipse(QPoint(int(cx), int(cy)), 5, 5)

    painter.end()
    return QIcon(pixmap)
