
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
        screen = QApplication.screenAt(QPoint(x, y))
        if not screen:
            screen = QApplication.primaryScreen()

        # Convert global x,y to screen-local coordinates
        local_x = x - screen.geometry().x()
        local_y = y - screen.geometry().y()

        pixmap = screen.grabWindow(0, local_x, local_y, 1, 1)
        c = pixmap.toImage().pixelColor(0, 0)
        return c.red(), c.green(), c.blue()

    @staticmethod
    def grab_area(x, y, width, height):
        # Find the screen containing the area
        screen = QApplication.screenAt(QPoint(x, y))
        if not screen:
            screen = QApplication.primaryScreen()

        # Convert global x,y to screen-local coordinates
        # grabWindow(0) on a QScreen uses coordinates relative to that screen's geometry
        local_x = x - screen.geometry().x()
        local_y = y - screen.geometry().y()

        return screen.grabWindow(0, local_x, local_y, width, height)

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
    """
    Window 2: Floating window for VISUALS only.
    Follows mouse with offset. Transparent to mouse events.
    """
    def __init__(self):
        super().__init__()
        # Tool + Frameless + StayOnTop + TransparentForMouse
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Let clicks pass through

        self.sample_size = 1
        self.zoom_level = 10
        self.cursor_pos = QCursor.pos()

        # Visual Size
        self.setFixedSize(200, 200)

    def set_sample_size(self, size):
        self.sample_size = size

    def update_pos(self, pos):
        self.cursor_pos = pos
        # Offset: +30, +30 from cursor
        self.move(pos.x() + 30, pos.y() + 30)
        self.update() # Trigger paint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Background
        painter.fillRect(self.rect(), Qt.black)

        # Capture Specs
        capture_size = 15
        half_size = capture_size // 2 # 7
        preview_size = capture_size * self.zoom_level # 150

        # Center rect inside the 200x200 widget
        box_x = (self.width() - preview_size) // 2
        box_y = (self.height() - preview_size) // 2
        target_rect = QRect(box_x, box_y, preview_size, preview_size)

        # Capture
        pix = ScreenSampler.grab_area(self.cursor_pos.x() - half_size,
                                      self.cursor_pos.y() - half_size,
                                      capture_size, capture_size)

        if not pix.isNull():
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            painter.drawPixmap(target_rect, pix)

        # Grid / Crosshair
        center_x = box_x + (preview_size // 2)
        center_y = box_y + (preview_size // 2)

        sample_vis = self.sample_size * self.zoom_level
        offset = sample_vis / 2

        draw_x = center_x - offset
        draw_y = center_y - offset

        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(int(draw_x) - 1, int(draw_y) - 1, int(sample_vis) + 2, int(sample_vis) + 2)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(int(draw_x), int(draw_y), int(sample_vis), int(sample_vis))

        # Border
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawRect(target_rect)

class BlockerWindow(QWidget):
    """
    Window 3: Floating window for INPUT only.
    Follows mouse CENTERED. Almost Transparent (alpha=1). Consumes clicks.
    """
    clicked = Signal()

    def __init__(self):
        super().__init__()
        # Tool + Frameless + StayOnTop + Translucent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # NOTE: WA_TransparentForMouseEvents is DEFAULT False (which is what we want)

        # Size same as magnifier (approx) to catch clicks reliably
        self.setFixedSize(200, 200)

    def update_pos(self, pos):
        # Center on cursor
        self.move(pos.x() - 100, pos.y() - 100)

    def paintEvent(self, event):
        # IMPORTANT: We must paint something (even if almost transparent)
        # for Windows to register the window as a click target.
        # Fully transparent (alpha=0) windows often pass clicks through.
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept() # Explicitly consume the event
        elif event.button() == Qt.RightButton:
            self.clicked.emit()
            event.accept()

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

        # Helper Objects
        self.magnifier_win = None
        self.blocker_win = None
        self.picker_timer = QTimer()
        self.picker_timer.timeout.connect(self.tick_picker)

        self.contrast_dialog = None

        # ICC
        self.icc_path = get_system_monitor_profile_path()

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

        if self.app_settings["color_managed"] and not self.icc_path:
            self.icc_path = get_system_monitor_profile_path()

        self.update_ui_with_color(self.current_color)

    def open_contrast_checker(self):
        if not self.contrast_dialog:
            self.contrast_dialog = ContrastCheckerDialog(self)
            self.contrast_dialog.request_color_pick.connect(self.activate_contrast_picker)
        self.contrast_dialog.show()
        self.contrast_dialog.raise_()
        self.contrast_dialog.activateWindow()

    # --- Eyedropper Logic ---

    def activate_eyedropper(self):
        # Standard activation for Main UI
        self.start_picker(self.add_color)

    def activate_contrast_picker(self, is_fg):
        self.contrast_target_is_fg = is_fg
        self.start_picker(self.return_contrast_color)

    def start_picker(self, callback):
        # Init windows if needed
        if not self.magnifier_win:
            self.magnifier_win = MagnifierWindow()
        if not self.blocker_win:
            self.blocker_win = BlockerWindow()
            self.blocker_win.clicked.connect(self.on_blocker_clicked)

        # Set settings
        self.magnifier_win.set_sample_size(self.app_settings["sample_size"])

        # Store callback
        self.picker_callback = callback

        # Show Windows
        self.magnifier_win.show()
        self.blocker_win.show()

        # Start Tracking
        self.picker_timer.start(10) # 100Hz update

    def tick_picker(self):
        pos = QCursor.pos()
        if self.magnifier_win and self.magnifier_win.isVisible():
            self.magnifier_win.update_pos(pos)
        if self.blocker_win and self.blocker_win.isVisible():
            self.blocker_win.update_pos(pos)

    def on_blocker_clicked(self):
        # Stop tracking
        self.picker_timer.stop()

        # Hide Overlay Windows BEFORE sampling
        if self.blocker_win: self.blocker_win.hide()
        if self.magnifier_win: self.magnifier_win.hide()

        QApplication.processEvents()

        # Sample
        pos = QCursor.pos()
        size = self.app_settings["sample_size"]

        if size <= 1:
            raw_color = ScreenSampler.get_pixel_color(pos.x(), pos.y())
        else:
            raw_color = ScreenSampler.get_average_color(pos.x(), pos.y(), size)

        # ICC
        if self.app_settings["color_managed"] and self.icc_path:
            final_color = convert_to_srgb(*raw_color, self.icc_path)
        else:
            final_color = raw_color

        # Callback
        if self.picker_callback:
            self.picker_callback(final_color)

    def return_contrast_color(self, color):
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
            lbl.setObjectName("BigHexLabel")
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
