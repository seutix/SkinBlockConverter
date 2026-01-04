from PIL import Image
from collections import Counter, defaultdict

# Load skin and output
skin = Image.open('your_skin.png').convert('RGBA')
output = Image.open('output_unique.png').convert('RGBA')

# Map each skin color to all block samples
skin_to_blocks = defaultdict(set)

for y in range(64):
    for x in range(64):
        skin_color = skin.getpixel((x, y))
        if skin_color[3] < 128:
            continue
        
        rgb = skin_color[:3]
        
        # Get the corresponding 16x16 block from output
        output_x = x * 16
        output_y = y * 16
        
        # Sample multiple pixels from the block to identify it
        block_signature = []
        for dy in [0, 8, 15]:
            for dx in [0, 8, 15]:
                px = output.getpixel((output_x + dx, output_y + dy))[:3]
                block_signature.append(px)
        
        skin_to_blocks[rgb].add(tuple(block_signature))

print("=== CHECKING FOR DUPLICATE BLOCKS ===\n")

# Check if any skin color maps to multiple different blocks
errors = []
for skin_color, block_sigs in skin_to_blocks.items():
    if len(block_sigs) > 1:
        errors.append((skin_color, block_sigs))
        print(f"✗ Skin RGB{skin_color} maps to {len(block_sigs)} different blocks!")

if not errors:
    print("✓ Each skin color consistently maps to the same block")

# Check if different skin colors map to the same block
print("\n=== CHECKING FOR SHARED BLOCKS ===\n")

block_to_colors = defaultdict(list)
for skin_color, block_sigs in skin_to_blocks.items():
    # Use first signature (should be only one)
    block_sig = list(block_sigs)[0]
    block_to_colors[block_sig].append(skin_color)

shared_blocks = {block: colors for block, colors in block_to_colors.items() if len(colors) > 1}

if shared_blocks:
    print(f"✗ Found {len(shared_blocks)} blocks shared by multiple colors:\n")
    for block_sig, colors in shared_blocks.items():
        print(f"Block signature {block_sig[:2]}... used by:")
        for color in colors:
            print(f"  - RGB{color}")
        print()
else:
    print("✓ Each block is used by only one skin color")

print(f"\n=== SUMMARY ===")
print(f"Unique skin colors: {len(skin_to_blocks)}")
print(f"Unique blocks used: {len(block_to_colors)}")
print(f"Expected: {len(skin_to_blocks)} colors = {len(skin_to_blocks)} blocks")

if len(block_to_colors) == len(skin_to_blocks):
    print("\n✓✓✓ SUCCESS: Perfect 1-to-1 mapping!")
else:
    print(f"\n✗✗✗ PROBLEM: Mismatch in mapping")
