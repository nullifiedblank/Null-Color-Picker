
import sys
import os
import platform
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout,
                               QScrollArea, QSizePolicy, QDialog, QComboBox, QCheckBox, QGroupBox,
                               QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QCursor, QIcon, QPixmap, QGuiApplication, QAction

from styles import STYLESHEET
from color_logic import generate_palettes, rgb_to_hex, rgb_to_cmyk, rgb_to_hsl_string
from icon_gen import create_app_icon, create_gear_icon
from widgets import ToggleSwitch, CopyLabel, FlashFrame, PaletteItem
from contrast_ui import ContrastCheckerDialog # Restored Dialog import
from icc_utils import get_system_monitor_profile_path, convert_to_srgb

# --- Constants ---
SETTINGS_FILE = "settings.json"

def load_icon():
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    for name in ["icon.ico", "icon.png"]:
        path = os.path.join(base_path, name)
        if os.path.exists(path):
            return QIcon(path)
    return create_app_icon()

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
                if color == -1: return 0, 0, 0
                r = color & 0xff
                g = (color >> 8) & 0xff
                b = (color >> 16) & 0xff
                return r, g, b
            except:
                return ScreenSampler.get_pixel_qt(x, y)
        else:
            return ScreenSampler.get_pixel_qt(x, y)

    @staticmethod
    def get_pixel_qt(x, y):
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0, x, y, 1, 1)
        c = pixmap.toImage().pixelColor(0, 0)
        return c.red(), c.green(), c.blue()

    @staticmethod
    def grab_area(x, y, width, height):
        screen = QApplication.primaryScreen()
        return screen.grabWindow(0, x, y, width, height)

    @staticmethod
    def get_average_color(x, y, size):
        if size <= 1:
            return ScreenSampler.get_pixel_color(x, y)
        start_x = x - (size // 2)
        start_y = y - (size // 2)
        pixmap = ScreenSampler.grab_area(start_x, start_y, size, size)
        if pixmap.isNull(): return 0, 0, 0
        image = pixmap.toImage()
        total_r, total_g, total_b, count = 0, 0, 0, 0
        for i in range(image.width()):
            for j in range(image.height()):
                c = image.pixelColor(i, j)
                total_r += c.red(); total_g += c.green(); total_b += c.blue()
                count += 1
        if count == 0: return 0, 0, 0
        return (int(total_r / count), int(total_g / count), int(total_b / count))

# --- UI Components ---

class SettingsDialog(QDialog):
    settings_changed = Signal(dict)

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 400)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)

        self.settings = current_settings or {}

        layout = QVBoxLayout()
        layout.setSpacing(15)
        self.setLayout(layout)

        # 1. Sample Size
        sample_group = QGroupBox("Sample Size")
        sample_layout = QVBoxLayout()
        self.sample_combo = QComboBox()
        self.sample_combo.addItems(["Point Sample (1x1)", "3x3 Average", "5x5 Average", "7x7 Average"])
        idx_map = {1: 0, 3: 1, 5: 2, 7: 3}
        self.sample_combo.setCurrentIndex(idx_map.get(self.settings.get("sample_size", 1), 0))
        sample_layout.addWidget(self.sample_combo)
        sample_group.setLayout(sample_layout)
        layout.addWidget(sample_group)

        # 2. Color Management
        icc_group = QGroupBox("Color Management")
        icc_layout = QHBoxLayout()
        icc_layout.addWidget(QLabel("Enable ICC Correction"))
        self.icc_toggle = ToggleSwitch()
        self.icc_toggle.setChecked(self.settings.get("color_managed", True))
        icc_layout.addWidget(self.icc_toggle)
        icc_group.setLayout(icc_layout)
        layout.addWidget(icc_group)

        # 3. Visible Systems
        vis_group = QGroupBox("Visible Color Systems")
        vis_layout = QGridLayout()
        self.vis_toggles = {}
        systems = ["HEX", "RGB", "HSL", "CMYK"]
        for i, sys_name in enumerate(systems):
            lbl = QLabel(sys_name)
            tgl = ToggleSwitch()
            tgl.setChecked(self.settings.get(f"show_{sys_name.lower()}", True))
            self.vis_toggles[sys_name.lower()] = tgl
            vis_layout.addWidget(lbl, i, 0)
            vis_layout.addWidget(tgl, i, 1)
        vis_group.setLayout(vis_layout)
        layout.addWidget(vis_group)

        # 4. Window Options
        window_group = QGroupBox("Window Options")
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Always on Top"))
        self.aot_toggle = ToggleSwitch()
        self.aot_toggle.setChecked(self.settings.get("always_on_top", False))
        window_layout.addWidget(self.aot_toggle)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        layout.addStretch()

    def save_settings(self):
        size_text = self.sample_combo.currentText()
        size = 1
        if "3x3" in size_text: size = 3
        elif "5x5" in size_text: size = 5
        elif "7x7" in size_text: size = 7

        new_settings = {
            "sample_size": size,
            "color_managed": self.icc_toggle.isChecked(),
            "always_on_top": self.aot_toggle.isChecked(),
            "show_hex": self.vis_toggles["hex"].isChecked(),
            "show_rgb": self.vis_toggles["rgb"].isChecked(),
            "show_hsl": self.vis_toggles["hsl"].isChecked(),
            "show_cmyk": self.vis_toggles["cmyk"].isChecked(),
        }
        self.settings_changed.emit(new_settings)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

class MagnifierWindow(QWidget):
    color_selected = Signal(tuple) # r, g, b

    def __init__(self):
        super().__init__()
        # Reverting to 200x200 following window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False) # Standard window
        self.setFixedSize(200, 200)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)

        self.current_color = (0, 0, 0)
        self.sample_size = 1 # Default

        self.zoom_level = 10
        self.is_active = False

        # ICC
        self.color_managed = True
        self.icc_path = get_system_monitor_profile_path()

    def set_sample_size(self, size):
        self.sample_size = size

    def set_color_managed(self, enabled):
        self.color_managed = enabled
        if enabled and not self.icc_path:
            self.icc_path = get_system_monitor_profile_path()

    def start(self):
        self.is_active = True
        self.setMouseTracking(True)

        # Ensure window is ready to grab
        self.show()
        self.activateWindow()
        self.raise_()
        self.setFocus()

        self.timer.start(16) # ~60 FPS
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

        # Follow cursor with offset
        self.move(pos.x() + 30, pos.y() + 30)

        grab_x = pos.x() - 10
        grab_y = pos.y() - 10

        self.pixmap = ScreenSampler.grab_area(grab_x, grab_y, 20, 20)

        self.current_color = ScreenSampler.get_average_color(pos.x(), pos.y(), self.sample_size)

        # Apply ICC if managed
        if self.color_managed and self.icc_path:
            self.current_color = convert_to_srgb(*raw_color, self.icc_path)

        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw zoomed image
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            target_rect = self.rect()
            painter.drawPixmap(target_rect, self.pixmap)

        # Draw Crosshair / Sample Box
        # Align to grid: 200x200 window, 10x zoom.
        # Center pixel (or sample area) should be visually centered.
        # Pixel 0 starts at 0. Pixel 10 starts at 100.
        # Box should start at width // 2 (100).

        box_x = self.width() // 2
        box_y = self.height() // 2

        pixel_visual_size = self.zoom_level
        sample_visual_size = self.sample_size * pixel_visual_size

        # Center logic:
        # If sample size is 1 (10px visual), we want it at 100,100.
        # If sample size is 3 (30px visual), we want it at 90,90 (so 100,100 is center of middle pixel).

        offset_pixels = self.sample_size // 2
        draw_x = box_x - (offset_pixels * self.zoom_level)
        draw_y = box_y - (offset_pixels * self.zoom_level)

        # Contrast border (White)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(draw_x - 1, draw_y - 1, sample_visual_size + 2, sample_visual_size + 2)

        # Black border
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(draw_x, draw_y, sample_visual_size, sample_visual_size)

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
        items_layout.setSpacing(0)
        items_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addLayout(items_layout)

        # Distribute items evenly with stretch and vertical lines
        items_layout.addStretch(1)
        for i, c_data in enumerate(colors):
            # Add Vertical Line Separator if not first item
            if i > 0:
                vline = QFrame()
                vline.setFrameShape(QFrame.VLine)
                vline.setFrameShadow(QFrame.Sunken)
                vline.setFixedWidth(1)
                vline.setStyleSheet("background-color: #333333;") # Faint gray
                vline.setFixedHeight(40) # Height of color box approx

                # Wrap in widget to center vertically if needed, or just add
                # Add spacing around line
                items_layout.addSpacing(10)
                items_layout.addWidget(vline)
                items_layout.addSpacing(10)

            item = PaletteItem(*c_data['rgb'])
            items_layout.addWidget(item)

        items_layout.addStretch(1)

        layout.addWidget(container)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Null Color Picker")
        # Increased width for better layout
        self.setFixedWidth(800)

        # Set App Icon
        self.setWindowIcon(load_icon())

        # Logic: Initialize History with Black and White
        self.history = [(0,0,0), (255,255,255)]
        self.current_color = (255, 255, 255)
        self.load_settings()

        # UI Setup
        self.setup_ui()

        # Magnifier
        self.magnifier = MagnifierWindow()
        self.magnifier.set_sample_size(self.app_settings["sample_size"])
        self.magnifier.set_color_managed(self.app_settings["color_managed"])
        self.magnifier.color_selected.connect(self.add_color)

        self.contrast_dialog = None # Lazy load

        # Initial State
        self.update_ui_with_color((255, 255, 255))

    def load_settings(self):
        self.app_settings = {
            "sample_size": 1, "color_managed": True, "always_on_top": False,
            "show_hex": True, "show_rgb": True, "show_hsl": True, "show_cmyk": True
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.app_settings.update(json.load(f))
            except: pass

    def save_settings_file(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.app_settings, f)
        except: pass

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10) # Reduced spacing
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Top Bar: Settings + Contrast + Eyedropper + Preview
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Settings Button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(create_gear_icon())
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)

        # Contrast Checker Button
        self.contrast_btn = QPushButton(" Contrast")
        # Use simple unicode or standard icon if available
        self.contrast_btn.setIcon(QIcon.fromTheme("applications-graphics"))
        self.contrast_btn.setObjectName("EyedropperButton") # Reuse style
        self.contrast_btn.setCursor(Qt.PointingHandCursor)
        self.contrast_btn.clicked.connect(self.open_contrast_checker)
        top_bar.addWidget(self.contrast_btn)

        # Eyedropper Button
        self.eyedropper_btn = QPushButton(" Eyedropper")
        self.eyedropper_btn.setIcon(load_icon())
        self.eyedropper_btn.setObjectName("EyedropperButton")
        self.eyedropper_btn.setCursor(Qt.PointingHandCursor)
        self.eyedropper_btn.clicked.connect(self.activate_eyedropper)
        top_bar.addWidget(self.eyedropper_btn)

        # Stretch to push text to right
        top_bar.addStretch()

        # Color Info (Right Aligned)
        self.color_info_layout = QVBoxLayout()
        self.color_info_layout.setSpacing(0)
        self.color_info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Labels added dynamically

        top_bar.addLayout(self.color_info_layout)

        # Selected Color Preview (Right most)
        self.selected_preview = QFrame()
        self.selected_preview.setObjectName("PreviewFrame")
        self.selected_preview.setFixedSize(70, 70)
        self.selected_preview.setStyleSheet(f"background-color: #FFFFFF; border: 1px solid #333; border-radius: 10px;")
        top_bar.addWidget(self.selected_preview)

        main_layout.addLayout(top_bar)

        # 2. History
        history_label = QLabel("History")
        history_label.setObjectName("SectionTitle")
        main_layout.addWidget(history_label)

        self.history_container = QHBoxLayout()
        self.history_container.setAlignment(Qt.AlignCenter)
        self.history_container.setSpacing(5)
        main_layout.addLayout(self.history_container)

        # 3. Color Theory Tabs
        theory_label = QLabel("Color Theory")
        theory_label.setObjectName("SectionTitle")
        main_layout.addWidget(theory_label)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; border-radius: 4px; }
            QTabBar::tab { background: #1e1e1e; color: #aaa; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #333; color: #fff; font-weight: bold; }
        """)
        main_layout.addWidget(self.tabs)

        # Add stretch at bottom to allow shrinking
        main_layout.addStretch()

    def open_settings(self):
        dlg = SettingsDialog(self, self.app_settings)
        dlg.settings_changed.connect(self.apply_settings)

        btn_pos = self.settings_btn.mapToGlobal(QPoint(0, self.settings_btn.height()))
        dlg.move(btn_pos)

        dlg.exec()

    def apply_settings(self, settings):
        self.app_settings = settings
        self.save_settings_file()
        QTimer.singleShot(100, self._apply_settings_deferred)

    def _apply_settings_deferred(self):
        current = self.windowFlags()
        new_flags = current
        if self.app_settings["always_on_top"]: new_flags |= Qt.WindowStaysOnTopHint
        else: new_flags &= ~Qt.WindowStaysOnTopHint

        if new_flags != current:
            self.setWindowFlags(new_flags)
            self.show()

        self.magnifier.set_sample_size(self.app_settings["sample_size"])
        self.magnifier.set_color_managed(self.app_settings["color_managed"])

        self.update_ui_with_color(self.current_color)

    def open_contrast_checker(self):
        if not self.contrast_dialog:
            self.contrast_dialog = ContrastCheckerDialog(self)
            self.contrast_dialog.request_color_pick.connect(self.activate_contrast_picker)
        self.contrast_dialog.show()
        self.contrast_dialog.raise_()
        self.contrast_dialog.activateWindow()

    def activate_eyedropper(self):
        try: self.magnifier.color_selected.disconnect(self.return_contrast_color)
        except: pass
        try: self.magnifier.color_selected.disconnect(self.add_color)
        except: pass

        self.magnifier.color_selected.connect(self.add_color)
        self.magnifier.start()

    def activate_contrast_picker(self, is_fg):
        try: self.magnifier.color_selected.disconnect(self.add_color)
        except: pass

        self.contrast_target_is_fg = is_fg
        self.magnifier.color_selected.connect(self.return_contrast_color)
        self.magnifier.start()

    def return_contrast_color(self, color):
        try: self.magnifier.color_selected.disconnect(self.return_contrast_color)
        except: pass
        self.magnifier.color_selected.connect(self.add_color)

        hex_val = rgb_to_hex(*color)
        if self.contrast_dialog:
            self.contrast_dialog.receive_picked_color(hex_val, self.contrast_target_is_fg)

    def add_color(self, color):
        if len(self.history) >= 15:
            self.history.pop(0)
        self.history.append(tuple(color))

        self.update_ui_with_color(tuple(color))
        self.raise_()
        self.activateWindow()

    def update_history_ui(self):
        while self.history_container.count():
            child = self.history_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        display_history = self.history[-15:] if len(self.history) > 15 else self.history

        for c in reversed(display_history):
            hex_val = rgb_to_hex(*c)
            swatch = FlashFrame(hex_val, is_history=True, interactive=True)
            swatch.setFixedSize(35, 35)
            swatch.clicked.connect(lambda col=c: self.update_ui_with_color(col))
            swatch.setToolTip(f"RGB: {c}")
            self.history_container.addWidget(swatch)

    def update_ui_with_color(self, color):
        r, g, b = color
        self.current_color = color
        hex_val = rgb_to_hex(r, g, b)

        self.selected_preview.setStyleSheet(f"background-color: {hex_val}; border: 1px solid #333; border-radius: 10px;")

        # Update Top Bar Info
        while self.color_info_layout.count():
            child = self.color_info_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        s = self.app_settings
        def add_lbl(text):
            lbl = CopyLabel(text)
            lbl.setStyleSheet("font-size: 13px; font-family: monospace; color: #ffffff; padding: 2px 4px;")
            lbl.setAlignment(Qt.AlignRight)
            self.color_info_layout.addWidget(lbl)

        if s.get("show_hex", True):
            lbl = CopyLabel(rgb_to_hex(r, g, b))
            lbl.setStyleSheet("font-size: 20px; font-weight: bold; font-family: monospace; color: #ffffff; padding: 2px 4px;")
            lbl.setAlignment(Qt.AlignRight)
            self.color_info_layout.addWidget(lbl)

        if s.get("show_rgb", True): add_lbl(f"rgb({r}, {g}, {b})")
        if s.get("show_hsl", True): add_lbl(rgb_to_hsl_string(r, g, b))
        if s.get("show_cmyk", True): add_lbl("cmyk" + str(rgb_to_cmyk(r, g, b)))

        self.update_history_ui()
        self.update_theory_tabs(r, g, b)

        # Dynamic Resizing
        QTimer.singleShot(10, self.adjustSize)

    def update_theory_tabs(self, r, g, b):
        current_idx = self.tabs.currentIndex()
        self.tabs.clear()

        palettes = generate_palettes(r, g, b)
        order = ["Monochromatic", "Analogous", "Complementary", "Split Complementary", "Triadic", "Tetradic"]

        for name in order:
            if name in palettes:
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                content = QWidget()
                content.setObjectName("PaletteContainer")
                layout = QHBoxLayout(content)
                layout.setSpacing(10)
                layout.setContentsMargins(10, 20, 10, 20)

                layout.addStretch(1)
                colors = palettes[name]
                for i, c_data in enumerate(colors):
                    if i > 0:
                        vline = QFrame()
                        vline.setFrameShape(QFrame.VLine)
                        vline.setFrameShadow(QFrame.Sunken)
                        vline.setFixedWidth(1)
                        vline.setStyleSheet("background-color: #333333;")
                        vline.setFixedHeight(40)
                        layout.addWidget(vline)

                    item = PaletteItem(*c_data['rgb'], self.app_settings)
                    layout.addWidget(item)

                layout.addStretch(1)
                scroll.setWidget(content)
                self.tabs.addTab(scroll, name)

        if current_idx >= 0 and current_idx < self.tabs.count():
            self.tabs.setCurrentIndex(current_idx)

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
