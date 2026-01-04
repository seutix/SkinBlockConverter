from PIL import Image
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher
from collections import Counter

# Load skin
skin = Image.open('your_skin.png').convert('RGBA')

# Get unique colors
unique_colors = set()
color_frequency = {}
for y in range(64):
    for x in range(64):
        pixel_color = skin.getpixel((x, y))
        if len(pixel_color) >= 4 and pixel_color[3] >= 128:
            rgb = pixel_color[:3]
            unique_colors.add(rgb)
            color_frequency[rgb] = color_frequency.get(rgb, 0) + 1

# Sort by frequency
sorted_colors = sorted(unique_colors, key=lambda c: color_frequency[c], reverse=True)

print(f"Total unique colors: {len(sorted_colors)}")

# Load palette
palette = BlockPalette('block')
palette.load_blocks()
matcher = ColorMatcher(palette)

print(f"Total available blocks: {len(palette.blocks)}")

# Simulate assignment
color_to_block = {}
used_blocks = set()

for i, color in enumerate(sorted_colors, 1):
    # Find best unused block
    all_blocks = palette.get_all_blocks()
    candidates = []
    
    for block_name, block_color in all_blocks:
        if block_name not in used_blocks:
            distance = matcher.color_distance_ciede2000(color, block_color)
            candidates.append((distance, block_name, block_color))
    
    if candidates:
        candidates.sort(key=lambda x: x[0])
        best_distance, best_block, best_color = candidates[0]
        color_to_block[color] = best_block
        used_blocks.add(best_block)
        
        if i <= 15:
            print(f"{i:2d}. RGB{color} ({color_frequency[color]:3d} px) -> {best_block:30s} RGB{best_color} dist={best_distance:.1f}")
    else:
        print(f"{i:2d}. RGB{color} - NO BLOCKS AVAILABLE!")

print(f"\nAssigned {len(color_to_block)} colors to {len(used_blocks)} unique blocks")

# Check for duplicates
block_usage = Counter(color_to_block.values())
duplicates = {block: count for block, count in block_usage.items() if count > 1}
if duplicates:
    print(f"\n✗ DUPLICATES FOUND:")
    for block, count in duplicates.items():
        print(f"  {block} used {count} times")
        colors_using = [c for c, b in color_to_block.items() if b == block]
        for c in colors_using:
            print(f"    - RGB{c}")
else:
    print("\n✓ No duplicates - all unique!")
