
STYLESHEET = """
QMainWindow {
    background-color: #121212;
    color: #e0e0e0;
}

QWidget {
    font-family: 'Inter', 'Roboto', 'Segoe UI', monospace;
    font-size: 14px;
    color: #e0e0e0;
}

/* Labels */
QLabel {
    color: #e0e0e0;
}

QLabel#SectionTitle {
    font-weight: bold;
    font-size: 16px;
    margin-top: 10px;
    margin-bottom: 5px;
    color: #ffffff;
}

/* Buttons */
QPushButton {
    background-color: #1e1e1e;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 8px 16px;
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
    border-radius: 12px;
    padding: 12px;
    font-size: 16px;
}

QPushButton#EyedropperButton:hover {
    background-color: #dddddd;
}

/* Icon Button (Settings) */
QPushButton#IconButton {
    background-color: transparent;
    border: none;
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
    padding: 10px;
    margin-bottom: 10px;
    background-color: #1e1e1e;
}

QLabel#HexLabel {
    font-family: monospace;
    font-size: 12px;
    color: #aaaaaa;
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
    margin-top: 10px;
    color: #e0e0e0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #aaaaaa;
}
"""
