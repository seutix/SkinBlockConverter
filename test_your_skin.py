from minecraft_skin_pixelart.color_matcher import ColorMatcher
from minecraft_skin_pixelart.block_palette import BlockPalette

# Your main skin colors
skin_colors = [
    (183, 160, 149),  # Most common
    (160, 138, 133),  # Second
    (102, 80, 76),    # Third
]

palette = BlockPalette('block')
palette.load_blocks()

print("=== TESTING YOUR SKIN COLORS ===\n")

for skin_color in skin_colors:
    print(f"Skin color RGB{skin_color}")
    r, g, b = skin_color
    warmth = (r + g) / 2 - b
    saturation = max(r, g, b) - min(r, g, b)
    print(f"  Warmth: {warmth:.1f}, Saturation: {saturation}")
    
    # Find all blocks and their distances
    all_blocks = palette.get_all_blocks()
    distances = []
    
    for block_name, block_color in all_blocks:
        dist = ColorMatcher.color_distance_ciede2000(skin_color, block_color)
        distances.append((block_name, block_color, dist))
    
    # Sort by distance
    distances.sort(key=lambda x: x[2])
    
    print(f"\n  Top 10 closest blocks:")
    for i, (block_name, block_color, dist) in enumerate(distances[:10], 1):
        br, bg, bb = block_color
        block_warmth = (br + bg) / 2 - bb
        block_sat = max(br, bg, bb) - min(br, bg, bb)
        print(f"    {i:2d}. {block_name:35s} RGB{block_color} dist={dist:5.1f} warmth={block_warmth:5.1f} sat={block_sat:3d}")
    
    print()
