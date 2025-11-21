
import sys
import os
import platform
from PIL import ImageCms, Image

IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    # Define necessary constants and structures for Windows ICM
    MIG_ALL_DISPLAY_PROFILES = 2

    # Function prototypes would go here if we were doing complex enumeration
    # But for now we will rely on mscms WcsGetDefaultColorProfile or similar.
    # Or easier: Standard GetICMProfile from GDI.

    gdi32 = ctypes.windll.gdi32
    user32 = ctypes.windll.user32
    mscms = ctypes.windll.mscms

def get_system_monitor_profile_path():
    """
    Attempts to retrieve the ICC profile path for the primary monitor on Windows.
    Returns None on failure or non-Windows (fallback to sRGB/standard).
    """
    if not IS_WINDOWS:
        # Linux/Mac implementation would require colord or ColorSync interaction
        # For now, return None to imply standard handling
        return None

    try:
        # Get Device Context for screen
        hdc = user32.GetDC(0)

        # GetICMProfile
        # BOOL GetICMProfileA(HDC hdc, LPDWORD pBufSize, LPSTR pszFilename);
        # We use the W (Unicode) version

        MAX_PATH = 260
        filename_buffer = ctypes.create_unicode_buffer(MAX_PATH)
        lpcbName = ctypes.c_ulong(MAX_PATH)

        # checking return
        res = gdi32.GetICMProfileW(hdc, ctypes.byref(lpcbName), filename_buffer)

        user32.ReleaseDC(0, hdc)

        if res:
            return filename_buffer.value
        else:
            # Error or no profile associated
            return None

    except Exception as e:
        print(f"ICC Error: {e}")
        return None

def convert_to_srgb(r, g, b, source_profile_path=None):
    """
    Converts an RGB tuple (0-255) from source_profile to sRGB.
    If source_profile_path is None, assumes raw/sRGB (no-op).
    """
    if not source_profile_path or not os.path.exists(source_profile_path):
        return r, g, b

    try:
        # Create a 1x1 image
        im = Image.new("RGB", (1, 1), (r, g, b))

        # Create transform
        # We cache this in a real app, but for simplicity here we recreate
        # Or better, rely on Pillow's built-in conversion if we load the profile

        # Target sRGB
        srgb_profile = ImageCms.createProfile("sRGB")
        source_profile = ImageCms.getOpenProfile(source_profile_path)

        # Transform
        out_im = ImageCms.profileToProfile(im, source_profile, srgb_profile, outputMode='RGB')

        # Get pixel
        return out_im.getpixel((0, 0))

    except Exception as e:
        print(f"Conversion Error: {e}")
        return r, g, b
