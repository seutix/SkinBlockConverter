from PIL import Image
from collections import Counter

# Load skin and output
skin = Image.open('your_skin.png').convert('RGBA')
output = Image.open('output_unique.png').convert('RGBA')

# Get unique colors from skin
skin_pixels = list(skin.getdata())
skin_colors = set()
for p in skin_pixels:
    if p[3] >= 128:  # Opaque
        skin_colors.add(p[:3])

print(f"=== SKIN ANALYSIS ===")
print(f"Unique colors in skin: {len(skin_colors)}")

# Count frequency of each color
color_freq = Counter()
for p in skin_pixels:
    if p[3] >= 128:
        color_freq[p[:3]] += 1

print("\nTop 10 most common colors:")
for i, (color, count) in enumerate(color_freq.most_common(10), 1):
    print(f"{i:2d}. RGB{color} - {count} pixels")

# Now check output - each 16x16 block should be unique for unique input colors
print(f"\n=== OUTPUT ANALYSIS ===")

# Map each skin pixel to its output block
skin_to_block = {}
for y in range(64):
    for x in range(64):
        skin_color = skin.getpixel((x, y))
        if skin_color[3] < 128:
            continue
        
        rgb = skin_color[:3]
        
        # Get the corresponding 16x16 block from output
        output_x = x * 16
        output_y = y * 16
        
        # Sample the center pixel of the block
        block_sample = output.getpixel((output_x + 8, output_y + 8))[:3]
        
        if rgb not in skin_to_block:
            skin_to_block[rgb] = block_sample
        else:
            # Verify it's the same block
            if skin_to_block[rgb] != block_sample:
                print(f"ERROR: Color RGB{rgb} mapped to different blocks!")
                print(f"  First: RGB{skin_to_block[rgb]}")
                print(f"  Now:   RGB{block_sample}")

print(f"Unique blocks used: {len(set(skin_to_block.values()))}")
print(f"Unique colors in skin: {len(skin_to_block)}")

if len(set(skin_to_block.values())) == len(skin_to_block):
    print("\n✓ SUCCESS: Each unique color has a unique block!")
else:
    print(f"\n✗ PROBLEM: {len(skin_to_block)} colors but only {len(set(skin_to_block.values()))} unique blocks")

# Show mapping
print("\n=== COLOR TO BLOCK MAPPING ===")
sorted_mapping = sorted(skin_to_block.items(), key=lambda x: color_freq[x[0]], reverse=True)
for i, (skin_color, block_color) in enumerate(sorted_mapping[:15], 1):
    freq = color_freq[skin_color]
    print(f"{i:2d}. Skin RGB{skin_color} ({freq:4d} px) -> Block RGB{block_color}")
