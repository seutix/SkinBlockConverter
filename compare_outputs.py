from PIL import Image
from collections import Counter

# Load both outputs
old = Image.open('output_fixed.png').convert('RGBA')
new = Image.open('output_improved.png').convert('RGBA')

# Get pixel data
old_pixels = list(old.getdata())
new_pixels = list(new.getdata())

# Count opaque pixels
old_opaque = [p[:3] for p in old_pixels if p[3] > 128]
new_opaque = [p[:3] for p in new_pixels if p[3] > 128]

# Get most common colors
old_colors = Counter(old_opaque)
new_colors = Counter(new_opaque)

print("=== OLD OUTPUT (output_fixed.png) ===")
print("Top 10 colors:")
for i, (color, count) in enumerate(old_colors.most_common(10), 1):
    r, g, b = color
    warmth = (r + g) / 2 - b
    saturation = max(r, g, b) - min(r, g, b)
    print(f"{i:2d}. RGB{str(color):20s} count={count:5d} warmth={warmth:6.1f} sat={saturation:3d}")

print("\n=== NEW OUTPUT (output_improved.png) ===")
print("Top 10 colors:")
for i, (color, count) in enumerate(new_colors.most_common(10), 1):
    r, g, b = color
    warmth = (r + g) / 2 - b
    saturation = max(r, g, b) - min(r, g, b)
    print(f"{i:2d}. RGB{str(color):20s} count={count:5d} warmth={warmth:6.1f} sat={saturation:3d}")

# Compare
print("\n=== COMPARISON ===")
print(f"Old average warmth: {sum((r+g)/2-b for r,g,b in old_opaque)/len(old_opaque):.1f}")
print(f"New average warmth: {sum((r+g)/2-b for r,g,b in new_opaque)/len(new_opaque):.1f}")
print(f"Old average saturation: {sum(max(r,g,b)-min(r,g,b) for r,g,b in old_opaque)/len(old_opaque):.1f}")
print(f"New average saturation: {sum(max(r,g,b)-min(r,g,b) for r,g,b in new_opaque)/len(new_opaque):.1f}")
