
STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
    color: #000000;
}

QWidget {
    font-family: 'Inter', 'Roboto', 'Segoe UI', monospace;
    font-size: 14px;
}

/* Labels */
QLabel {
    color: #000000;
}

QLabel#SectionTitle {
    font-weight: bold;
    font-size: 16px;
    margin-top: 10px;
    margin-bottom: 5px;
}

/* Buttons */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #dddddd;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #f0f0f0;
    border-color: #cccccc;
}

QPushButton:pressed {
    background-color: #e0e0e0;
}

/* Big Eyedropper Button */
QPushButton#EyedropperButton {
    background-color: #000000;
    color: #ffffff;
    border-radius: 12px;
    padding: 12px;
    font-size: 16px;
}

QPushButton#EyedropperButton:hover {
    background-color: #333333;
}

/* Color Swatches */
QFrame#Swatch {
    border-radius: 6px;
    border: 1px solid #eeeeee;
}

QFrame#HistorySwatch {
    border-radius: 4px;
    border: 1px solid #eeeeee;
}

/* Palette Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QWidget#PaletteContainer {
    background-color: #ffffff;
}

QFrame#PaletteBox {
    border: 1px solid #eeeeee;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 10px;
    background-color: #fafafa;
}

QLabel#HexLabel {
    font-family: monospace;
    font-size: 12px;
    color: #555555;
}
"""
