
# Null Color Picker

A modern, dark-mode Windows desktop color picker built with Python and PySide6.

## Features
- **Global Eyedropper:** Pick colors from anywhere on your screen with a magnified preview.
- **Color History:** Keeps track of your last 15 picked colors.
- **Color Theory:** Automatically generates Monochromatic, Analogous, Complementary, and other palettes.
- **Contrast Checker:** Check WCAG contrast compliance between two colors.
- **ICC Profile Support:** Correctly handles color profiles for accurate sampling.

## Installation

1. **Install Python 3.10+**
2. **Install Dependencies:**
   ```bash
   pip install PySide6 Pillow pyinstaller
   ```
   *(Note: `Pillow` is required for ICC profile management)*

## Running the App
```bash
python main.py
```

## Compiling to .exe
To build a standalone executable:
```bash
pyinstaller --noconfirm --windowed --onefile --name "NullColorPicker" --add-data "icon.ico;." main.py
```
*(Ensure you have an `icon.ico` file, or remove the `--add-data` and icon flags)*
