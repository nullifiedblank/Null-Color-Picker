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

    # 'Null' slash or stylized N?
    # Let's do a simple diagonal split or a droplet.

    # Droplet shape
    path = QPainterPath()
    path.moveTo(32, 16)
    path.cubicTo(48, 16, 48, 40, 32, 48)
    path.cubicTo(16, 40, 16, 16, 32, 16)

    painter.setBrush(QColor("#ffffff"))
    painter.drawPath(path)

    painter.end()

    return QIcon(pixmap)
