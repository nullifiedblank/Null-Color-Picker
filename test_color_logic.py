from color_logic import generate_palettes, rgb_to_hls_wrapper, hls_to_rgb_wrapper

def test_logic():
    # Test red color
    r, g, b = 255, 0, 0
    print(f"Testing Red: ({r}, {g}, {b})")
    palettes = generate_palettes(r, g, b)

    for name, colors in palettes.items():
        print(f"\n{name}:")
        for c in colors:
            print(f"  {c['hex']} - {c['rgb']}")

    # Sanity check HLS conversion
    h, l, s = rgb_to_hls_wrapper(255, 0, 0)
    print(f"\nRed HLS: {h}, {l}, {s}") # Should be 0, 0.5, 1.0

    r2, g2, b2 = hls_to_rgb_wrapper(h, l, s)
    print(f"Red RGB back: {r2}, {g2}, {b2}")
    assert (r, g, b) == (r2, g2, b2)
    print("RGB->HLS->RGB cycle passed.")

if __name__ == "__main__":
    test_logic()
