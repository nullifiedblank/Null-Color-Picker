
import sys
import os
import platform
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout,
                               QScrollArea, QSizePolicy, QDialog, QComboBox, QCheckBox, QGroupBox,
                               QTabWidget)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QPoint, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QCursor, QIcon, QPixmap, QGuiApplication, QAction

from styles import STYLESHEET
from color_logic import generate_palettes, rgb_to_hex, rgb_to_cmyk, rgb_to_hsl_string
from icon_gen import create_app_icon, create_gear_icon
from widgets import ToggleSwitch, CopyLabel, FlashFrame, PaletteItem
from contrast_ui import ContrastCheckerDialog
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
        # Qt grabWindow(0) usually works fine even with overlays if the overlay is transparent
        # or if we grab strictly under the mouse where we are NOT drawing.
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

class MagnifierOverlay(QWidget):
    """
    Full-screen transparent overlay for capturing clicks and drawing the magnifier.
    """
    color_selected = Signal(tuple)

    def __init__(self):
        super().__init__()
        # Use Tool + Frameless + StayOnTop.
        # TranslucentBackground allows drawing on top of desktop.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # Removed WA_TranslucentBackground to avoid transparency issues with grabbing.
        # We will paint opaque but emulate transparency by drawing screenshot.
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.timer = QTimer(self)
        # self.timer.timeout.connect(self.update_view) # Not using timer loop for grabbing anymore

        self.current_color = (0, 0, 0)
        self.sample_size = 1
        self.zoom_level = 10
        self.is_active = False

        self.screenshots = [] # List of (rect, pixmap)

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

        # 1. Capture all screens (Snapshot)
        self.screenshots = []
        total_rect = QRect()
        screens = QApplication.screens()

        # Briefly process events to ensure UI is updated before grab if needed
        QApplication.processEvents()

        for screen in screens:
            geo = screen.geometry()
            # Grab the screen content
            pix = screen.grabWindow(0)
            self.screenshots.append((geo, pix))
            total_rect = total_rect.united(geo)

        # 2. Set overlay geometry to cover everything
        self.setGeometry(total_rect)

        # 3. Show and Activate
        self.show()
        self.raise_()
        self.activateWindow()

        # 4. Grab Input
        QApplication.processEvents() # Ensure window is mapped
        self.setFocus()
        self.grabKeyboard()
        self.grabMouse()

    def stop(self):
        self.is_active = False
        self.releaseKeyboard()
        self.releaseMouse()
        self.hide()
        self.screenshots = [] # Clear memory

    def get_color_at(self, global_pos):
        # Find which screenshot contains the point
        for geo, pix in self.screenshots:
            if geo.contains(global_pos):
                local_pos = global_pos - geo.topLeft()

                # If sample size > 1, we should average.
                # For simplicity/speed in snapshot mode, getting single pixel or small area from QPixmap is fast.

                if self.sample_size <= 1:
                    c = pix.toImage().pixelColor(local_pos)
                    return c.red(), c.green(), c.blue()
                else:
                    # Average
                    start_x = local_pos.x() - (self.sample_size // 2)
                    start_y = local_pos.y() - (self.sample_size // 2)
                    copy = pix.copy(start_x, start_y, self.sample_size, self.sample_size).toImage()

                    total_r, total_g, total_b, count = 0, 0, 0, 0
                    for i in range(copy.width()):
                        for j in range(copy.height()):
                            c = copy.pixelColor(i, j)
                            total_r += c.red(); total_g += c.green(); total_b += c.blue()
                            count += 1
                    if count == 0: return 0, 0, 0
                    return (int(total_r / count), int(total_g / count), int(total_b / count))

        return 0, 0, 0

    def get_magnifier_pixmap(self, global_pos):
        # Grab 20x20 area around cursor from screenshots
        # We might bridge across screens, but handling that perfectly is complex.
        # We'll grab from the screen containing the center.

        grab_rect = QRect(global_pos.x() - 10, global_pos.y() - 10, 20, 20)

        for geo, pix in self.screenshots:
            if geo.contains(global_pos):
                # Crop relative to this screen
                # If edge case (near border), this truncates.
                # For 'Pixel Perfect', fixing border crossing is nice but secondary to functionality.

                local_rect = grab_rect.translated(-geo.topLeft())
                return pix.copy(local_rect)

        return QPixmap(20, 20) # Empty if off-screen

    def paintEvent(self, event):
        if not self.is_active or not self.screenshots: return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # 1. Draw Background (The Screenshots)
        # This effectively "freezes" the screen visually
        for geo, pix in self.screenshots:
            # Convert global geo to local overlay coordinates
            # Since overlay geometry == total_rect, we need to map.
            # Actually, if overlay is at (0,0) of virtual desktop (typical),
            # but usually total_rect topLeft might be negative (multi monitor).
            # painter uses widget coordinates.
            # We need to map screen geo to widget coords.

            draw_pos = self.mapFromGlobal(geo.topLeft())
            painter.drawPixmap(draw_pos, pix)

        # 2. Draw Magnifier UI
        pos = QCursor.pos()
        local_pos = self.mapFromGlobal(pos)

        box_x = local_pos.x() + 30
        box_y = local_pos.y() + 30

        # Draw Box Background
        target_rect = QRect(box_x, box_y, 200, 200)
        painter.fillRect(target_rect, Qt.black)

        # Get Zoom Content
        zoomed_pix = self.get_magnifier_pixmap(pos)
        if not zoomed_pix.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            painter.drawPixmap(target_rect, zoomed_pix)

        # Update current color for emission (not drawing text, just internal state)
        raw_color = self.get_color_at(pos)
        if self.color_managed and self.icc_path:
            self.current_color = convert_to_srgb(*raw_color, self.icc_path)
        else:
            self.current_color = raw_color

        # Draw Crosshair / Grid
        center_x = box_x + 100
        center_y = box_y + 100

        pixel_vis = self.zoom_level
        sample_vis = self.sample_size * pixel_vis

        offset_pixels = self.sample_size // 2
        draw_x = center_x - (offset_pixels * self.zoom_level)
        draw_y = center_y - (offset_pixels * self.zoom_level)

        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(draw_x - 1, draw_y - 1, sample_vis + 2, sample_vis + 2)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(draw_x, draw_y, sample_vis, sample_vis)
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        painter.drawRect(target_rect)

    def mouseMoveEvent(self, event):
        # Force repaint to follow mouse
        self.update()

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
    def __init__(self, title, colors, settings):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        container = QFrame()
        container.setObjectName("PaletteBox")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(5)
        container.setLayout(container_layout)

        inner_title = QLabel(title)
        inner_title.setObjectName("PaletteTitle")
        inner_title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(inner_title)

        items_layout = QHBoxLayout()
        items_layout.setSpacing(0)
        items_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addLayout(items_layout)

        items_layout.addStretch(1)
        for i, c_data in enumerate(colors):
            if i > 0:
                vline = QFrame()
                vline.setFrameShape(QFrame.VLine)
                vline.setFrameShadow(QFrame.Sunken)
                vline.setFixedWidth(1)
                vline.setStyleSheet("background-color: #333333;")
                vline.setFixedHeight(40)
                items_layout.addSpacing(10)
                items_layout.addWidget(vline)
                items_layout.addSpacing(10)

            item = PaletteItem(*c_data['rgb'], settings)
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

        self.setup_ui()

        # Use the new Overlay Magnifier
        self.magnifier = MagnifierOverlay()
        self.magnifier.set_sample_size(self.app_settings["sample_size"])
        self.magnifier.set_color_managed(self.app_settings["color_managed"])
        self.magnifier.color_selected.connect(self.add_color)

        self.contrast_dialog = None

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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(create_gear_icon())
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)

        self.contrast_btn = QPushButton(" Contrast")
        self.contrast_btn.setIcon(QIcon.fromTheme("applications-graphics"))
        self.contrast_btn.setObjectName("EyedropperButton")
        self.contrast_btn.setCursor(Qt.PointingHandCursor)
        self.contrast_btn.clicked.connect(self.open_contrast_checker)
        top_bar.addWidget(self.contrast_btn)

        self.eyedropper_btn = QPushButton(" Eyedropper")
        self.eyedropper_btn.setIcon(load_icon())
        self.eyedropper_btn.setObjectName("EyedropperButton")
        self.eyedropper_btn.setCursor(Qt.PointingHandCursor)
        self.eyedropper_btn.clicked.connect(self.activate_eyedropper)
        top_bar.addWidget(self.eyedropper_btn)

        top_bar.addStretch()

        self.color_info_layout = QVBoxLayout()
        self.color_info_layout.setSpacing(0)
        self.color_info_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_bar.addLayout(self.color_info_layout)

        self.selected_preview = QFrame()
        self.selected_preview.setObjectName("PreviewFrame")
        self.selected_preview.setFixedSize(70, 70)
        self.selected_preview.setStyleSheet(f"background-color: #FFFFFF; border: 1px solid #333; border-radius: 10px;")
        top_bar.addWidget(self.selected_preview)

        main_layout.addLayout(top_bar)

        history_label = QLabel("History")
        history_label.setObjectName("SectionTitle")
        main_layout.addWidget(history_label)

        self.history_container = QHBoxLayout()
        self.history_container.setAlignment(Qt.AlignCenter)
        self.history_container.setSpacing(5)
        main_layout.addLayout(self.history_container)

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

        # Update Top Bar
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
