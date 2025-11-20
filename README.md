# Null Color Picker

A modern, dark-mode color picker and contrast checker built with Python and PySide6.

## Features
- **Global Eyedropper**: Zoom in and pick colors from anywhere on your screen.
- **Color History**: Keeps track of your recently picked colors.
- **Color Theory**: Automatically generates Monochromatic, Analogous, Complementary, and other palettes.
- **Contrast Checker**: Check WCAG contrast ratios between foreground and background colors.
- **Customizable**: Toggle "Always on Top" and adjust sample size (1x1, 3x3, etc.).

## Prerequisites
- Python 3.8 or higher
- pip

## Installation

1.  **Install Dependencies**
    ```bash
    pip install PySide6 pyinstaller
    ```

2.  **Prepare Your Icon**
    *   Place your icon file in the same folder as `main.py`.
    *   **Windows**: Name it `icon.ico`.
    *   **Mac/Linux**: Name it `icon.png`.

## Build Instructions

To create a standalone executable (e.g., `.exe` on Windows) that includes your custom icon:

### Windows
Run this command in your terminal:
```bash
pyinstaller --noconfirm --windowed --onefile --icon=icon.ico --add-data "icon.ico;." --name "NullColorPicker" main.py
```
*   `--icon=icon.ico`: Sets the file icon (visible in Explorer).
*   `--add-data "icon.ico;."`: Bundles the icon inside the app so the window title bar uses it.

### Linux / macOS
Run this command:
```bash
pyinstaller --noconfirm --windowed --onefile --icon=icon.png --add-data "icon.png:." --name "NullColorPicker" main.py
```
*   Note the separator for `--add-data` is a colon `:` on Unix systems, but a semicolon `;` on Windows.

## Output
The built application will be located in the `dist/` folder.
