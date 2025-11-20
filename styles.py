
STYLESHEET = """
QMainWindow {
    background-color: #121212;
    color: #e0e0e0;
}

QWidget {
    font-family: 'Roboto', 'Inter', 'Segoe UI', monospace;
    font-size: 14px;
    color: #e0e0e0;
}

/* Labels */
QLabel {
    color: #e0e0e0;
}

QLabel#SectionTitle {
    font-weight: bold;
    font-size: 15px;
    margin-top: 8px;
    margin-bottom: 4px;
    color: #ffffff;
}

/* Palette Inner Title */
QLabel#PaletteTitle {
    font-weight: bold;
    font-size: 13px;
    color: #aaaaaa;
    background-color: transparent;
    padding-bottom: 4px;
}

/* Buttons */
QPushButton {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: bold;
    color: #e0e0e0;
}

QPushButton:hover {
    background-color: #2c2c2c;
    border-color: #444444;
}

QPushButton:pressed {
    background-color: #383838;
}

/* Big Eyedropper Button */
QPushButton#EyedropperButton {
    background-color: #ffffff;
    color: #000000;
    border-radius: 10px;
    padding: 10px;
    font-size: 15px;
}

QPushButton#EyedropperButton:hover {
    background-color: #dddddd;
}

/* Settings Button (Updated) */
QPushButton#SettingsButton {
    background-color: transparent;
    border: 1px solid #444444;
    border-radius: 8px;
}
QPushButton#SettingsButton:hover {
    background-color: #2c2c2c;
    border-color: #666666;
}

/* Icon Button (Fallback) */
QPushButton#IconButton {
    background-color: transparent;
    border: none;
    border-radius: 20px;
}
QPushButton#IconButton:hover {
    background-color: #2c2c2c;
}

/* Color Swatches */
QFrame#Swatch {
    border-radius: 6px;
    border: 1px solid #333333;
}

QFrame#HistorySwatch {
    border-radius: 4px;
    border: 1px solid #333333;
}

/* Palette Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QWidget#PaletteContainer {
    background-color: #121212;
}

QFrame#PaletteBox {
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 8px;
    margin-bottom: 8px;
    background-color: #1e1e1e;
}

QLabel#CodeLabel {
    font-family: monospace;
    font-size: 11px;
    color: #aaaaaa;
}
QLabel#CodeLabel:hover {
    color: #ffffff;
}

/* Selected Preview Area */
QFrame#PreviewFrame {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 10px;
}

/* Settings Dialog */
QDialog {
    background-color: #121212;
    color: #e0e0e0;
}
QGroupBox {
    border: 1px solid #333333;
    border-radius: 6px;
    margin-top: 8px;
    color: #e0e0e0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #aaaaaa;
}

/* ComboBox */
QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 5px;
    color: #e0e0e0;
    min-width: 6em;
}

QComboBox:hover {
    border-color: #555555;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-left-color: darkgray;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #e0e0e0;
    selection-background-color: #333333;
    selection-color: #ffffff;
    border: 1px solid #333333;
    outline: none;
}

/* Scrollbar */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #333333;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #555555;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #121212;
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #333333;
    min-width: 20px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #555555;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""
