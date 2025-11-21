import colorsys

def rgb_to_hls_wrapper(r, g, b):
    """
    Convert RGB (0-255) to HLS (0-1).
    """
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    return h, l, s

def hls_to_rgb_wrapper(h, l, s):
    """
    Convert HLS (0-1) to RGB (0-255).
    """
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    # Clamp values to 0-255 in case of float errors
    r = max(0, min(255, int(r * 255)))
    g = max(0, min(255, int(g * 255)))
    b = max(0, min(255, int(b * 255)))
    return r, g, b

def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"

def rgb_to_cmyk(r, g, b):
    """
    Convert RGB to CMYK (0-100).
    """
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100

    # rgb [0,1]
    r = r / 255.0
    g = g / 255.0
    b = b / 255.0

    k = 1 - max(r, g, b)
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)

    return (round(c * 100), round(m * 100), round(y * 100), round(k * 100))

def rgb_to_hsl_string(r, g, b):
    h, l, s = rgb_to_hls_wrapper(r, g, b)
    return f"hsl({round(h*360)}, {round(s*100)}%, {round(l*100)}%)"

def rotate_hue(h, degrees):
    """
    Rotate hue by degrees.
    """
    return (h + degrees/360.0) % 1.0

def get_monochromatic(h, l, s):
    """
    Monochromatic (5 tones + shades)
    Modify L (lightness).
    """
    variations = [
        (h, l - 0.30, s),
        (h, l - 0.15, s),
        (h, l,       s),
        (h, l + 0.15, s),
        (h, l + 0.30, s),
    ]

    palette = []
    for vh, vl, vs in variations:
        # Clamp L between 0–1
        vl = max(0.0, min(1.0, vl))
        palette.append((vh, vl, vs))
    return palette

def get_analogous(h, l, s):
    """
    Analogous (±30° hue shift)
    Returns: [base, +30, -30]
    """
    ana1 = rotate_hue(h, 30)
    ana2 = rotate_hue(h, -30)
    return [(h, l, s), (ana1, l, s), (ana2, l, s)]

def get_complementary(h, l, s):
    """
    Complementary (180° shift)
    Returns: [base, complementary]
    """
    complement = rotate_hue(h, 180)
    return [(h, l, s), (complement, l, s)]

def get_split_complementary(h, l, s):
    """
    Split-Complementary (180° ± 30°)
    Returns: [base, split1, split2]
    """
    opp = rotate_hue(h, 180)
    split1 = rotate_hue(opp, 30)
    split2 = rotate_hue(opp, -30)
    return [(h, l, s), (split1, l, s), (split2, l, s)]

def get_triadic(h, l, s):
    """
    Triadic (±120°)
    Returns: [base, +120, -120]
    """
    tri1 = rotate_hue(h, 120)
    tri2 = rotate_hue(h, -120)
    return [(h, l, s), (tri1, l, s), (tri2, l, s)]

def get_tetradic(h, l, s):
    """
    Tetradic (Rectangle scheme)
    c1 = h
    c2 = rotate_hue(h, 180)
    c3 = rotate_hue(h, 60)
    c4 = rotate_hue(c2, 60)
    """
    c1 = h
    c2 = rotate_hue(h, 180)
    c3 = rotate_hue(h, 60)
    c4 = rotate_hue(c2, 60)
    return [(c1, l, s), (c2, l, s), (c3, l, s), (c4, l, s)]

def generate_palettes(r, g, b):
    h, l, s = rgb_to_hls_wrapper(r, g, b)

    palettes = {
        "Monochromatic": get_monochromatic(h, l, s),
        "Analogous": get_analogous(h, l, s),
        "Complementary": get_complementary(h, l, s),
        "Split Complementary": get_split_complementary(h, l, s),
        "Triadic": get_triadic(h, l, s),
        "Tetradic": get_tetradic(h, l, s)
    }

    # Convert all back to RGB hex for display
    hex_palettes = {}
    for name, colors in palettes.items():
        hex_colors = []
        for ch, cl, cs in colors:
            r_out, g_out, b_out = hls_to_rgb_wrapper(ch, cl, cs)
            hex_colors.append({
                "hex": rgb_to_hex(r_out, g_out, b_out),
                "rgb": (r_out, g_out, b_out)
            })
        hex_palettes[name] = hex_colors

    return hex_palettes
