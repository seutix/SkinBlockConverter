from PIL import Image
from collections import Counter

# Load the skin
skin = Image.open('your_skin.png').convert('RGBA')
pixels = list(skin.getdata())

# Filter out transparent pixels
opaque_pixels = [p[:3] for p in pixels if p[3] > 128]

# Get most common colors
color_counts = Counter(opaque_pixels)
print("=== TOP 20 COLORS IN YOUR SKIN ===")
for i, (color, count) in enumerate(color_counts.most_common(20), 1):
    r, g, b = color
    warmth = (r + g) / 2 - b
    saturation = max(r, g, b) - min(r, g, b)
    print(f"{i:2d}. RGB{str(color):20s} count={count:5d} warmth={warmth:6.1f} sat={saturation:3d}")

# Test with color matcher
from minecraft_skin_pixelart.color_matcher import ColorMatcher
from minecraft_skin_pixelart.block_palette import BlockPalette

palette = BlockPalette('block')
palette.load_blocks()
matcher = ColorMatcher(palette)

print("\n=== MATCHING TOP 5 SKIN COLORS TO BLOCKS ===")
for i, (color, count) in enumerate(color_counts.most_common(5), 1):
    block = matcher.find_closest_block(color + (255,))
    block_color = palette.average_colors[block]
    print(f"\n{i}. Skin color RGB{color} -> {block}")
    print(f"   Block color RGB{block_color}")
    print(f"   Distance: {ColorMatcher.color_distance_ciede2000(color, block_color):.1f}")
