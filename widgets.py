from PySide6.QtWidgets import (QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
                               QAbstractButton, QApplication, QStyle)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QSize, QTimer, Property
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QClipboard, QCursor

from color_logic import rgb_to_hex, rgb_to_hsl_string, rgb_to_cmyk

class ToggleSwitch(QAbstractButton):
    stateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(50, 26)
        self.setCursor(Qt.PointingHandCursor)

        # Animation
        self._handle_position = 3.0
        self.anim = QPropertyAnimation(self, b"handle_position", self)
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.toggled.connect(self.start_animation)

    def start_animation(self, checked):
        end_pos = self.width() - 23.0 if checked else 3.0
        self.anim.setEndValue(end_pos)
        self.anim.start()
        self.stateChanged.emit(checked)

    def get_handle_position(self):
        return self._handle_position

    def set_handle_position(self, pos):
        self._handle_position = pos
        self.update()

    handle_position = Property(float, get_handle_position, set_handle_position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        rect = self.rect()
        bg_color = QColor("#4CAF50") if self.isChecked() else QColor("#333333")
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 13, 13)

        # Handle
        painter.setBrush(QColor("#ffffff"))
        # x = self._handle_position, y = 3 (centered vertically in 26 height: 26-20=6 / 2 = 3)
        painter.drawEllipse(int(self._handle_position), 3, 20, 20)

class CopyLabel(QLabel):
    """
    A label that copies its text to clipboard on click and signals interactions.
    Uses dynamic property to handle flash styling without resetting font styles.
    """
    hovered = Signal(bool)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("CodeLabel")
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)

        self._flashing = False

        # Flash timer
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.reset_style)
        self.flash_timer.setSingleShot(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.text())
            self.flash_effect()

    def enterEvent(self, event):
        self.hovered.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered.emit(False)
        super().leaveEvent(event)

    def get_flashing(self):
        return self._flashing

    def set_flashing(self, val):
        self._flashing = val
        # Trigger style update
        self.style().unpolish(self)
        self.style().polish(self)

    flashing = Property(bool, get_flashing, set_flashing)

    def flash_effect(self):
        self.set_flashing(True)
        self.flash_timer.start(150)

    def reset_style(self):
        self.set_flashing(False)

class FlashFrame(QFrame):
    """
    A frame that can flash its border and supports external hover states.
    """
    clicked = Signal()

    def __init__(self, color_hex, parent=None, is_history=False, interactive=True):
        super().__init__(parent)
        self.color_hex = color_hex
        self.is_history = is_history
        self.interactive = interactive

        obj_name = "HistorySwatch" if is_history else "Swatch"
        self.setObjectName(obj_name)

        self.default_style = f"background-color: {self.color_hex};"
        self.setStyleSheet(self.default_style)

        if is_history or interactive:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.reset_style)
        self.flash_timer.setSingleShot(True)

    def set_outline(self, active):
        # Only show outline if interactive (or implied requirement to show outline on palette items but not click)
        # The requirement was "Color boxes shouldnt be clickable nor have an onclick flash".
        # But previous requirement "outline to the hovered color box" is likely for palette items too.
        # I will allow outline, but block clicks.
        if active:
            self.setStyleSheet(f"background-color: {self.color_hex}; border: 2px solid #ffffff;")
        else:
            self.setStyleSheet(self.default_style)

    def enterEvent(self, event):
        # Assuming external control or internal? PaletteItem uses set_outline externally.
        # History uses internal hover.
        if self.is_history:
            self.set_outline(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_history:
            self.set_outline(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if not self.interactive:
            return

        if event.button() == Qt.LeftButton:
            self.flash_effect()
            self.clicked.emit()

    def flash_effect(self):
        if not self.interactive: return

        # Flash border black -> white -> normal
        self.setStyleSheet(f"background-color: {self.color_hex}; border: 3px solid #ffffff;")
        self.flash_timer.start(100)

    def reset_style(self):
        # Check if still hovered?
        # Note: palette items are controlled externally via set_outline.
        # History items are internal.
        # If we are resetting flash, we revert to either hover state or default.

        if self.underMouse() and self.is_history:
             self.setStyleSheet(f"background-color: {self.color_hex}; border: 2px solid #ffffff;")
        else:
             self.setStyleSheet(self.default_style)

class PaletteItem(QWidget):
    """
    Composite widget: Color Box + Hex + RGB + HSL + CMYK
    Handles synced hover effects and dynamic label visibility.
    """
    def __init__(self, r, g, b, settings):
        super().__init__()
        self.color_hex = rgb_to_hex(r, g, b)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Color Box - Non-interactive for clicks/flash
        self.box = FlashFrame(self.color_hex, interactive=False)
        self.box.setFixedSize(40, 40)
        layout.addWidget(self.box, 0, Qt.AlignCenter)

        # Create labels based on settings
        self.labels = []

        if settings.get("show_hex", True):
            lbl = CopyLabel(self.color_hex)
            layout.addWidget(lbl, 0, Qt.AlignCenter)
            self.labels.append(lbl)

        if settings.get("show_rgb", True):
            lbl = CopyLabel(f"rgb({r}, {g}, {b})")
            layout.addWidget(lbl, 0, Qt.AlignCenter)
            self.labels.append(lbl)

        if settings.get("show_hsl", True):
            lbl = CopyLabel(rgb_to_hsl_string(r, g, b))
            layout.addWidget(lbl, 0, Qt.AlignCenter)
            self.labels.append(lbl)

        if settings.get("show_cmyk", True):
            c, m, y, k = rgb_to_cmyk(r, g, b)
            lbl = CopyLabel(f"cmyk({c},{m},{y},{k})")
            layout.addWidget(lbl, 0, Qt.AlignCenter)
            self.labels.append(lbl)

        # Connect Hover Signals
        for lbl in self.labels:
            lbl.hovered.connect(self.on_label_hover)

    def on_label_hover(self, hovered):
        self.box.set_outline(hovered)
