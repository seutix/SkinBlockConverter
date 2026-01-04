from PIL import Image
from collections import Counter

print("=== COMPARING OLD vs NEW APPROACH ===\n")

# Load outputs
old = Image.open('output_improved.png').convert('RGBA')
new = Image.open('output_unique.png').convert('RGBA')

# Sample blocks from both
old_blocks = set()
new_blocks = set()

for y in range(64):
    for x in range(64):
        ox = x * 16
        oy = y * 16
        
        # Sample 9 pixels from each block to create signature
        old_sig = tuple(old.getpixel((ox + dx, oy + dy))[:3] 
                       for dy in [0, 8, 15] for dx in [0, 8, 15])
        new_sig = tuple(new.getpixel((ox + dx, oy + dy))[:3] 
                       for dy in [0, 8, 15] for dx in [0, 8, 15])
        
        # Only count non-transparent blocks
        if old.getpixel((ox + 8, oy + 8))[3] >= 128:
            old_blocks.add(old_sig)
        if new.getpixel((ox + 8, oy + 8))[3] >= 128:
            new_blocks.add(new_sig)

print(f"OLD approach (output_improved.png):")
print(f"  Unique blocks used: {len(old_blocks)}")

print(f"\nNEW approach (output_unique.png):")
print(f"  Unique blocks used: {len(new_blocks)}")

# Load skin to count unique colors
skin = Image.open('your_skin.png').convert('RGBA')
skin_colors = set()
for y in range(64):
    for x in range(64):
        p = skin.getpixel((x, y))
        if p[3] >= 128:
            skin_colors.add(p[:3])

print(f"\nSkin unique colors: {len(skin_colors)}")

print("\n" + "="*50)
if len(new_blocks) == len(skin_colors):
    print("✓✓✓ NEW: Perfect mapping - each color has unique block!")
else:
    print(f"✗ NEW: {len(skin_colors)} colors but {len(new_blocks)} blocks")

if len(old_blocks) < len(skin_colors):
    print(f"✗ OLD: Only {len(old_blocks)} unique blocks for {len(skin_colors)} colors")
    print(f"    ({len(skin_colors) - len(old_blocks)} colors shared blocks)")
