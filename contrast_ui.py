from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFrame, QGridLayout, QApplication)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QIcon, QClipboard

from contrast_utils import calculate_contrast, suggest_passing_color, rgb_to_hex, hex_to_rgb
from widgets import FlashFrame, CopyLabel

class ContrastCheckerDialog(QDialog):
    request_color_pick = Signal(bool) # True for FG, False for BG

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contrast Checker")
        self.resize(500, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint) # Standard Dialog

        # Colors
        self.fg_color = "#FFFFFF"
        self.bg_color = "#000000"

        self.setup_ui()
        self.update_results()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.setLayout(layout)

        # --- 1. Inputs Area ---
        inputs_layout = QHBoxLayout()

        # FG Input
        self.fg_input = self.create_color_input("Foreground", self.fg_color, True)
        inputs_layout.addWidget(self.fg_input)

        # Swap Button
        swap_btn = QPushButton("↔")
        swap_btn.setFixedSize(40, 40)
        swap_btn.clicked.connect(self.swap_colors)
        inputs_layout.addWidget(swap_btn)

        # BG Input
        self.bg_input = self.create_color_input("Background", self.bg_color, False)
        inputs_layout.addWidget(self.bg_input)

        layout.addLayout(inputs_layout)

        # --- 2. Preview Area ---
        preview_group = QFrame()
        preview_group.setObjectName("PreviewBox")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_lbl = QLabel("The quick brown fox jumps over the lazy dog\n1234567890")
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold;")
        preview_layout.addWidget(self.preview_lbl)

        layout.addWidget(preview_group)

        # --- 3. Results Area ---
        results_grid = QGridLayout()
        results_grid.setSpacing(10)

        # Ratio
        self.ratio_lbl = QLabel("Ratio: 21.00:1")
        self.ratio_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        results_grid.addWidget(self.ratio_lbl, 0, 0, 1, 2, Qt.AlignCenter)

        # Normal Text
        results_grid.addWidget(QLabel("Normal Text", objectName="ResultLabel"), 1, 0)
        self.normal_aa = self.create_pass_fail_label()
        self.normal_aaa = self.create_pass_fail_label()
        results_grid.addWidget(self.normal_aa, 1, 1)
        results_grid.addWidget(self.normal_aaa, 1, 2)

        # Large Text
        results_grid.addWidget(QLabel("Large Text", objectName="ResultLabel"), 2, 0)
        self.large_aa = self.create_pass_fail_label()
        self.large_aaa = self.create_pass_fail_label()
        results_grid.addWidget(self.large_aa, 2, 1)
        results_grid.addWidget(self.large_aaa, 2, 2)

        layout.addLayout(results_grid)

        # --- 4. Suggestion Area ---
        self.suggestion_frame = QFrame()
        suggestion_layout = QHBoxLayout(self.suggestion_frame)
        suggestion_layout.setContentsMargins(0,0,0,0)

        lbl = QLabel("Suggestion (AA): ", objectName="SuggestionLabel")
        self.suggestion_val = CopyLabel("#AAAAAA")
        self.suggestion_apply = QPushButton("Apply")
        self.suggestion_apply.clicked.connect(self.apply_suggestion)

        suggestion_layout.addWidget(lbl)
        suggestion_layout.addWidget(self.suggestion_val)
        suggestion_layout.addWidget(self.suggestion_apply)
        suggestion_layout.addStretch()

        layout.addWidget(self.suggestion_frame)
        layout.addStretch()

    def create_color_input(self, title, default_hex, is_fg):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(0,0,0,0)

        # Title
        vbox.addWidget(QLabel(title))

        # Input Row: Edit + Picker + Copy
        hbox = QHBoxLayout()

        # Hex Edit
        le = QLineEdit(default_hex)
        le.setMaxLength(7)
        le.textChanged.connect(lambda t: self.on_hex_changed(t, is_fg))
        if is_fg: self.fg_le = le
        else: self.bg_le = le
        hbox.addWidget(le)

        # Picker Btn
        pick_btn = QPushButton()
        pick_btn.setIcon(QIcon.fromTheme("color-picker"))
        pick_btn.setText("🖊")
        pick_btn.setFixedSize(30, 30)
        pick_btn.clicked.connect(lambda: self.request_color_pick.emit(is_fg))
        hbox.addWidget(pick_btn)

        vbox.addLayout(hbox)

        # Swatches
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(5)
        presets = ["#FFFFFF", "#000000", "#808080", "#404040"]
        for p in presets:
            s = FlashFrame(p)
            s.setFixedSize(20, 20)
            s.setCursor(Qt.PointingHandCursor)
            s.clicked.connect(lambda c=p: self.set_color(c, is_fg))
            swatch_row.addWidget(s)
        swatch_row.addStretch()
        vbox.addLayout(swatch_row)

        return widget

    def create_pass_fail_label(self):
        lbl = QLabel("PASS AA")
        lbl.setObjectName("PassFail")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def set_color(self, hex_val, is_fg):
        # Normalize
        if not hex_val.startswith('#'): hex_val = '#' + hex_val
        hex_val = hex_val.upper()

        if is_fg:
            self.fg_color = hex_val
            self.fg_le.setText(hex_val)
        else:
            self.bg_color = hex_val
            self.bg_le.setText(hex_val)

        self.update_results()

    def on_hex_changed(self, text, is_fg):
        # Basic validation
        if len(text) == 7 and text.startswith('#'):
            try:
                hex_to_rgb(text) # Check valid
                if is_fg: self.fg_color = text
                else: self.bg_color = text
                self.update_results()
            except:
                pass

    def swap_colors(self):
        fg, bg = self.fg_color, self.bg_color
        self.set_color(bg, True)
        self.set_color(fg, False)

    def update_results(self):
        ratio = calculate_contrast(self.fg_color, self.bg_color)
        self.ratio_lbl.setText(f"Ratio: {ratio:.2f}:1")

        # Update Preview
        self.preview_lbl.setStyleSheet(f"background-color: {self.bg_color}; color: {self.fg_color}; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 6px;")

        # Update Labels
        def set_lbl(lbl, passed, text):
            lbl.setText(text)
            color = "#4CAF50" if passed else "#F44336"
            lbl.setStyleSheet(f"background-color: {color}; color: #ffffff; border-radius: 4px; padding: 2px 6px;")

        set_lbl(self.normal_aa, ratio >= 4.5, "AA Pass" if ratio >= 4.5 else "AA Fail")
        set_lbl(self.normal_aaa, ratio >= 7.0, "AAA Pass" if ratio >= 7.0 else "AAA Fail")
        set_lbl(self.large_aa, ratio >= 3.0, "AA Pass" if ratio >= 3.0 else "AA Fail")
        set_lbl(self.large_aaa, ratio >= 4.5, "AAA Pass" if ratio >= 4.5 else "AAA Fail")

        # Suggestions
        if ratio < 4.5:
            self.suggestion_frame.show()
            better = suggest_passing_color(self.fg_color, self.bg_color)
            self.suggestion_val.setText(better)
        else:
            self.suggestion_frame.hide()

    def apply_suggestion(self):
        self.set_color(self.suggestion_val.text(), True)

    def receive_picked_color(self, hex_val, is_fg):
        self.set_color(hex_val, is_fg)
        # Bring dialog to front
        self.raise_()
        self.activateWindow()
