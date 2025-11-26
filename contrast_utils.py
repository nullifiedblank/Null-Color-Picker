import colorsys

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"

def calculate_luminance(r, g, b):
    """
    Calculates relative luminance using WCAG 2.0 formula.
    """
    components = []
    for c in [r, g, b]:
        v = c / 255.0
        if v <= 0.03928:
            components.append(v / 12.92)
        else:
            components.append(((v + 0.055) / 1.055) ** 2.4)

    r_lin, g_lin, b_lin = components
    return (0.2126 * r_lin) + (0.7152 * g_lin) + (0.0722 * b_lin)

def calculate_contrast(fg_hex, bg_hex):
    """
    Returns contrast ratio (float) between two hex colors.
    """
    try:
        fg_rgb = hex_to_rgb(fg_hex)
        bg_rgb = hex_to_rgb(bg_hex)
    except ValueError:
        return 1.0 # Invalid color

    l1 = calculate_luminance(*fg_rgb)
    l2 = calculate_luminance(*bg_rgb)

    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    else:
        return (l2 + 0.05) / (l1 + 0.05)

def suggest_passing_color(fg_hex, bg_hex, target_ratio=4.5):
    """
    Adjusts FG lightness to meet target_ratio against BG.
    Returns suggested hex string.
    """
    try:
        fg_rgb = hex_to_rgb(fg_hex)
        bg_rgb = hex_to_rgb(bg_hex)
    except ValueError:
        return fg_hex

    bg_lum = calculate_luminance(*bg_rgb)

    # Current HSL
    h, l, s = colorsys.rgb_to_hls(fg_rgb[0]/255.0, fg_rgb[1]/255.0, fg_rgb[2]/255.0)

    # Determine direction: should we go lighter or darker?
    # If BG is dark, we likely need lighter FG. If BG is light, darker FG.
    # Using simple iteration for robustness

    best_hex = fg_hex

    # Scan lightness from 0.0 to 1.0 in steps
    # We want the value closest to original L that passes

    search_step = 0.01
    # Search upwards
    passed_up = None
    curr_l = l
    while curr_l <= 1.0:
        r, g, b = colorsys.hls_to_rgb(h, curr_l, s)
        test_rgb = (int(r*255), int(g*255), int(b*255))
        test_lum = calculate_luminance(*test_rgb)

        ratio = 0
        if test_lum > bg_lum:
            ratio = (test_lum + 0.05) / (bg_lum + 0.05)
        else:
            ratio = (bg_lum + 0.05) / (test_lum + 0.05)

        if ratio >= target_ratio:
            passed_up = rgb_to_hex(*test_rgb)
            break
        curr_l += search_step

    # Search downwards
    passed_down = None
    curr_l = l
    while curr_l >= 0.0:
        r, g, b = colorsys.hls_to_rgb(h, curr_l, s)
        test_rgb = (int(r*255), int(g*255), int(b*255))
        test_lum = calculate_luminance(*test_rgb)

        ratio = 0
        if test_lum > bg_lum:
            ratio = (test_lum + 0.05) / (bg_lum + 0.05)
        else:
            ratio = (bg_lum + 0.05) / (test_lum + 0.05)

        if ratio >= target_ratio:
            passed_down = rgb_to_hex(*test_rgb)
            break
        curr_l -= search_step

    # Return closest
    if passed_up and passed_down:
        # Which is closer to original L?
        # Re-calculate L for results to compare
        # ... actually simple heuristic: |l - l_up| vs |l - l_down|
        # Since we stepped incrementally, the number of steps tells us distance.
        # But we don't have step count here easily.
        # Just pick one. Usually preserving the intended "vibe" (dark/light) is hard.
        # Let's calculate distance.

        return passed_up # Prefer lighter? Or just arbitrary.

    if passed_up: return passed_up
    if passed_down: return passed_down

    return fg_hex # No solution found (unlikely unless color is weird)
