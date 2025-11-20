
import sys
import os
import platform
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout,
                               QScrollArea, QSizePolicy, QDialog, QComboBox, QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QCursor, QIcon, QPixmap, QGuiApplication, QAction

from styles import STYLESHEET
from color_logic import generate_palettes, rgb_to_hex
from icon_gen import create_app_icon, create_gear_icon
from widgets import ToggleSwitch, CopyLabel, FlashFrame, PaletteItem

# --- Platform Specific Imports ---
IS_WINDOWS = platform.system() == 'Windows'
if IS_WINDOWS:
    import ctypes
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

# --- Screen Sampler ---

class ScreenSampler:
    @staticmethod
    def get_cursor_pos():
        return QCursor.pos()

    @staticmethod
    def get_pixel_color(x, y):
        if IS_WINDOWS:
            try:
                hdc = user32.GetDC(0)
                color = gdi32.GetPixel(hdc, x, y)
                user32.ReleaseDC(0, hdc)

                if color == -1: # Failed to get pixel
                    return 0, 0, 0

                r = color & 0xff
                g = (color >> 8) & 0xff
                b = (color >> 16) & 0xff
                return r, g, b
            except Exception:
                # Fallback if ctypes fails
                return ScreenSampler.get_pixel_qt(x, y)
        else:
            return ScreenSampler.get_pixel_qt(x, y)

    @staticmethod
    def get_pixel_qt(x, y):
        # Qt fallback - significantly slower for real-time but functional cross-platform
        screen = QApplication.primaryScreen()
        # Grab a 1x1 pixel
        pixmap = screen.grabWindow(0, x, y, 1, 1)
        image = pixmap.toImage()
        c = image.pixelColor(0, 0)
        return c.red(), c.green(), c.blue()

    @staticmethod
    def grab_area(x, y, width, height):
        screen = QApplication.primaryScreen()
        # grabWindow(windowId, x, y, width, height). 0 is root window.
        return screen.grabWindow(0, x, y, width, height)

    @staticmethod
    def get_average_color(x, y, size):
        """
        Calculates the average color of a square area of 'size' centered at (x, y).
        """
        if size <= 1:
            return ScreenSampler.get_pixel_color(x, y)

        # Determine top-left corner
        start_x = x - (size // 2)
        start_y = y - (size // 2)

        # Grab the area
        pixmap = ScreenSampler.grab_area(start_x, start_y, size, size)
        if pixmap.isNull():
            return 0, 0, 0

        image = pixmap.toImage()

        total_r, total_g, total_b = 0, 0, 0
        count = 0

        for i in range(image.width()):
            for j in range(image.height()):
                c = image.pixelColor(i, j)
                total_r += c.red()
                total_g += c.green()
                total_b += c.blue()
                count += 1

        if count == 0:
            return 0, 0, 0

        return (
            int(total_r / count),
            int(total_g / count),
            int(total_b / count)
        )

# --- UI Components ---

class SettingsDialog(QDialog):
    settings_changed = Signal(dict)

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 200)

        self.settings = current_settings or {}

        layout = QVBoxLayout()
        layout.setSpacing(15)
        self.setLayout(layout)

        # Sample Size Group
        sample_group = QGroupBox("Sample Size")
        sample_layout = QVBoxLayout()

        self.sample_combo = QComboBox()
        self.sample_combo.addItems(["Point Sample (1x1)", "3x3 Average", "5x5 Average", "7x7 Average"])

        # Set current index
        current_size = self.settings.get("sample_size", 1)
        index_map = {1: 0, 3: 1, 5: 2, 7: 3}
        self.sample_combo.setCurrentIndex(index_map.get(current_size, 0))

        sample_layout.addWidget(self.sample_combo)
        sample_group.setLayout(sample_layout)
        layout.addWidget(sample_group)

        # Window Options
        window_group = QGroupBox("Window Options")
        window_layout = QHBoxLayout() # Use HBox for Toggle
        window_layout.setAlignment(Qt.AlignLeft)

        lbl = QLabel("Always on Top")
        self.toggle_switch = ToggleSwitch()
        self.toggle_switch.setChecked(self.settings.get("always_on_top", False))

        window_layout.addWidget(lbl)
        window_layout.addWidget(self.toggle_switch)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_settings(self):
        size_text = self.sample_combo.currentText()
        size = 1
        if "3x3" in size_text: size = 3
        elif "5x5" in size_text: size = 5
        elif "7x7" in size_text: size = 7

        new_settings = {
            "sample_size": size,
            "always_on_top": self.toggle_switch.isChecked()
        }

        self.settings_changed.emit(new_settings)
        self.accept()

class MagnifierWindow(QWidget):
    color_selected = Signal(tuple) # r, g, b

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 200)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)

        self.current_color = (0, 0, 0)
        self.sample_size = 1 # Default

        self.zoom_level = 10
        self.grab_size = 20

        self.is_active = False

    def set_sample_size(self, size):
        self.sample_size = size

    def start(self):
        self.is_active = True
        self.setMouseTracking(True)
        self.timer.start(16) # ~60 FPS
        self.show()
        self.grabKeyboard()
        self.grabMouse()

    def stop(self):
        self.is_active = False
        self.timer.stop()
        self.releaseKeyboard()
        self.releaseMouse()
        self.hide()

    def update_view(self):
        if not self.is_active:
            return

        pos = QCursor.pos()
        # Offset to bottom-right
        self.move(pos.x() + 30, pos.y() + 30)

        grab_x = pos.x() - (self.grab_size // 2)
        grab_y = pos.y() - (self.grab_size // 2)

        self.pixmap = ScreenSampler.grab_area(grab_x, grab_y, self.grab_size, self.grab_size)

        self.current_color = ScreenSampler.get_average_color(pos.x(), pos.y(), self.sample_size)

        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw zoomed image
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            target_rect = self.rect()
            painter.drawPixmap(target_rect, self.pixmap)

        # Draw Crosshair / Sample Box
        center_x = self.width() // 2
        center_y = self.height() // 2

        pixel_visual_size = self.zoom_level
        sample_visual_size = self.sample_size * pixel_visual_size

        # Draw box around sampled area
        box_x = center_x - (sample_visual_size // 2)
        box_y = center_y - (sample_visual_size // 2)

        # Contrast border (White)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(box_x - 1, box_y - 1, sample_visual_size + 2, sample_visual_size + 2)

        # Black border
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(box_x, box_y, sample_visual_size, sample_visual_size)

        # Outer border
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        painter.drawRect(0, 0, self.width(), self.height())


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.color_selected.emit(self.current_color)
            self.stop()
        elif event.button() == Qt.RightButton:
            self.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.stop()

class PaletteRow(QWidget):
    def __init__(self, title, colors):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2) # Reduced spacing
        self.setLayout(layout)

        # Removed external title label as requested

        container = QFrame()
        container.setObjectName("PaletteBox")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)
        container.setLayout(container_layout)

        # Inner Title
        inner_title = QLabel(title)
        inner_title.setObjectName("PaletteTitle")
        inner_title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(inner_title)

        # Items
        items_layout = QHBoxLayout()
        items_layout.setSpacing(10)
        items_layout.setAlignment(Qt.AlignCenter)
        container_layout.addLayout(items_layout)

        for c_data in colors:
            item = PaletteItem(*c_data['rgb'])
            items_layout.addWidget(item)

        layout.addWidget(container)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Null Color Picker")
        # Fixed window size - 600px width to accommodate palette items comfortably, 800px height
        self.setFixedSize(600, 800)

        # Set App Icon
        self.setWindowIcon(create_app_icon())

        # Logic
        self.history = []
        self.current_color = (255, 255, 255)
        self.app_settings = {
            "sample_size": 1,
            "always_on_top": False
        }

        # UI Setup
        self.setup_ui()

        # Magnifier
        self.magnifier = MagnifierWindow()
        self.magnifier.color_selected.connect(self.add_color)

        # Initial State
        self.update_ui_with_color((255, 255, 255))

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10) # Reduced spacing
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Top Bar: Settings + Eyedropper + Preview
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Settings Button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(create_gear_icon())
        self.settings_btn.setObjectName("IconButton")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)

        # Eyedropper Button
        self.eyedropper_btn = QPushButton(" Eyedropper")
        self.eyedropper_btn.setIcon(create_app_icon())
        self.eyedropper_btn.setObjectName("EyedropperButton")
        self.eyedropper_btn.setCursor(Qt.PointingHandCursor)
        self.eyedropper_btn.clicked.connect(self.activate_eyedropper)
        top_bar.addWidget(self.eyedropper_btn)

        # Selected Color Info
        self.selected_preview = QFrame()
        self.selected_preview.setObjectName("PreviewFrame")
        self.selected_preview.setFixedSize(70, 70) # Slightly smaller
        self.selected_preview.setStyleSheet(f"background-color: #FFFFFF; border: 1px solid #333; border-radius: 10px;")
        top_bar.addWidget(self.selected_preview)

        self.color_info_layout = QVBoxLayout()
        self.color_info_layout.setSpacing(0)
        self.hex_label = CopyLabel("#FFFFFF")
        self.hex_label.setStyleSheet("font-size: 22px; font-weight: bold; font-family: monospace; color: #ffffff;")
        self.rgb_label = CopyLabel("rgb(255, 255, 255)")
        self.rgb_label.setStyleSheet("font-size: 13px; color: #aaaaaa;")

        self.color_info_layout.addWidget(self.hex_label)
        self.color_info_layout.addWidget(self.rgb_label)
        top_bar.addLayout(self.color_info_layout)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # 2. History
        history_label = QLabel("History")
        history_label.setObjectName("SectionTitle")
        main_layout.addWidget(history_label)

        self.history_container = QHBoxLayout()
        self.history_container.setAlignment(Qt.AlignLeft)
        self.history_container.setSpacing(5)
        main_layout.addLayout(self.history_container)

        # 3. Color Theory Palettes (Scrollable)
        # Removed "Color Theory" label as requested

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.palette_content = QWidget()
        self.palette_content.setObjectName("PaletteContainer")
        self.palette_layout = QVBoxLayout(self.palette_content)
        self.palette_layout.setSpacing(5)
        self.palette_layout.setContentsMargins(0,0,0,0)
        scroll.setWidget(self.palette_content)

        main_layout.addWidget(scroll)

    def open_settings(self):
        dlg = SettingsDialog(self, self.app_settings)
        dlg.settings_changed.connect(self.apply_settings)
        dlg.exec()

    def apply_settings(self, settings):
        self.app_settings = settings

        # Apply Always on Top
        if settings["always_on_top"]:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show() # Need to show again after changing flags

        # Apply Sample Size
        self.magnifier.set_sample_size(settings["sample_size"])

    def activate_eyedropper(self):
        self.magnifier.start()

    def add_color(self, color):
        if len(self.history) >= 15:
            self.history.pop(0)
        self.history.append(color)

        self.update_history_ui()
        self.update_ui_with_color(color)

        self.raise_()
        self.activateWindow()

    def update_history_ui(self):
        while self.history_container.count():
            child = self.history_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for c in reversed(self.history):
            hex_val = rgb_to_hex(*c)
            # History uses FlashFrame directly
            swatch = FlashFrame(hex_val, is_history=True)
            swatch.setFixedSize(30, 30)
            swatch.clicked.connect(lambda col=c: self.update_ui_with_color(col))
            swatch.setToolTip(f"RGB: {c[0]},{c[1]},{c[2]}\nHEX: {hex_val}")
            self.history_container.addWidget(swatch)

    def update_ui_with_color(self, color):
        r, g, b = color
        self.current_color = color
        hex_val = rgb_to_hex(r, g, b)
        rgb_str = f"rgb({r}, {g}, {b})"

        self.selected_preview.setStyleSheet(f"background-color: {hex_val}; border: 1px solid #333; border-radius: 10px;")
        self.hex_label.setText(hex_val)
        self.rgb_label.setText(rgb_str)

        self.generate_and_show_palettes(r, g, b)

    def generate_and_show_palettes(self, r, g, b):
        while self.palette_layout.count():
            child = self.palette_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        palettes = generate_palettes(r, g, b)
        order = ["Monochromatic", "Analogous", "Complementary", "Split Complementary", "Triadic", "Tetradic"]

        for name in order:
            if name in palettes:
                row = PaletteRow(name, palettes[name])
                self.palette_layout.addWidget(row)
        self.palette_layout.addStretch()

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
