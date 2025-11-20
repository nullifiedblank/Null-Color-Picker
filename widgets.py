from PySide6.QtWidgets import (QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
                               QAbstractButton, QApplication)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QSize, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QClipboard, QCursor

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

    handle_position = property(get_handle_position, set_handle_position)

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
    """
    hovered = Signal(bool)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("CodeLabel")
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)

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

    def flash_effect(self):
        # Simple flash: change color to white then back
        self.setStyleSheet("color: #ffffff; font-weight: bold;")
        self.flash_timer.start(150)

    def reset_style(self):
        self.setStyleSheet("")

class FlashFrame(QFrame):
    """
    A frame that can flash its border and supports external hover states.
    """
    clicked = Signal()

    def __init__(self, color_hex, parent=None, is_history=False):
        super().__init__(parent)
        self.color_hex = color_hex
        self.is_history = is_history

        obj_name = "HistorySwatch" if is_history else "Swatch"
        self.setObjectName(obj_name)

        self.default_style = f"background-color: {self.color_hex};"
        self.setStyleSheet(self.default_style)

        if is_history:
            self.setCursor(Qt.PointingHandCursor)

        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.reset_style)
        self.flash_timer.setSingleShot(True)

    def set_outline(self, active):
        if active:
            self.setStyleSheet(f"background-color: {self.color_hex}; border: 2px solid #ffffff;")
        else:
            self.setStyleSheet(self.default_style)

    def enterEvent(self, event):
        if self.is_history:
            self.set_outline(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.is_history:
            self.set_outline(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.flash_effect()
            self.clicked.emit()

    def flash_effect(self):
        # Flash border black -> white -> normal
        # We set white border temporarily
        self.setStyleSheet(f"background-color: {self.color_hex}; border: 3px solid #ffffff;")
        self.flash_timer.start(100)

    def reset_style(self):
        # Check if still hovered?
        if self.underMouse() and self.is_history:
             self.setStyleSheet(f"background-color: {self.color_hex}; border: 2px solid #ffffff;")
        else:
             self.setStyleSheet(self.default_style)

class PaletteItem(QWidget):
    """
    Composite widget: Color Box + Hex + RGB
    Handles synced hover effects.
    """
    def __init__(self, r, g, b):
        super().__init__()
        self.hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.rgb_val = f"rgb({r}, {g}, {b})"

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Color Box
        self.box = FlashFrame(self.hex_val)
        self.box.setFixedSize(40, 40)
        # If clicked, maybe set main color? (Not required by prompt for palette items, only history.
        # But 'copy color code' is required)

        # Labels
        self.hex_lbl = CopyLabel(self.hex_val)
        self.rgb_lbl = CopyLabel(self.rgb_val)

        layout.addWidget(self.box)
        layout.addWidget(self.hex_lbl)
        layout.addWidget(self.rgb_lbl)

        # Connect Hover Signals
        self.hex_lbl.hovered.connect(self.on_label_hover)
        self.rgb_lbl.hovered.connect(self.on_label_hover)

    def on_label_hover(self, hovered):
        self.box.set_outline(hovered)
        # Also outline the label itself?
        # CopyLabel handles its own hover text color change via stylesheet (CodeLabel:hover)
        # But the prompt said: "outline the corresponding color box too" -> Done.
        # "outline to the hovered color code" -> Done via :hover style (color change to white is typical for dark mode focus).
        # Or actual border? Text with border looks bad. Changing color to bright white is cleaner.
        # The prompt asked for "Add an outline to the hovered color code".
        # I'll stick to text color change for cleanliness, but if outline is strictly required, I'd need a frame around the label.
        # Let's assume visual highlighting is the goal.
