
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

/* Icon Button (Settings) */
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
"""
