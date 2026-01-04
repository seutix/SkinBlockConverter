from PIL import Image
import os

blocks = {}
block_dir = 'block'

for filename in os.listdir(block_dir):
    if not filename.endswith('.png'):
        continue
    
    img = Image.open(os.path.join(block_dir, filename)).convert('RGBA')
    pixels = list(img.getdata())
    
    r_sum = g_sum = b_sum = weight_sum = 0
    for p in pixels:
        weight = p[3] / 255.0
        r_sum += p[0] * weight
        g_sum += p[1] * weight
        b_sum += p[2] * weight
        weight_sum += weight
    
    if weight_sum > 0:
        avg = (int(r_sum/weight_sum), int(g_sum/weight_sum), int(b_sum/weight_sum))
        blocks[filename] = avg

# Find gray blocks (low saturation, dark)
print("=== DARK GRAY BLOCKS ===")
gray_blocks = [(name, color) for name, color in blocks.items() 
               if abs(color[0]-color[1]) < 15 and abs(color[1]-color[2]) < 15 and color[0] < 100]
for name, color in sorted(gray_blocks, key=lambda x: x[1][0])[:15]:
    print(f"{name:40s} RGB{color}")

# Find beige/tan blocks (warm, medium brightness)
print("\n=== BEIGE/TAN BLOCKS ===")
beige_blocks = [(name, color) for name, color in blocks.items()
                if color[0] > 100 and color[1] > 80 and color[2] < color[1] 
                and (color[0] + color[1])/2 - color[2] > 20]
for name, color in sorted(beige_blocks, key=lambda x: x[1][0])[:15]:
    warmth = (color[0] + color[1])/2 - color[2]
    print(f"{name:40s} RGB{color} warmth={warmth:.1f}")

# Test skin color matching
print("\n=== TESTING SKIN COLOR ===")
skin_color = (194, 154, 123)  # Typical beige skin tone
print(f"Test skin color: RGB{skin_color}")

from minecraft_skin_pixelart.color_matcher import ColorMatcher

# Calculate distances
distances = []
for name, color in blocks.items():
    dist = ColorMatcher.color_distance_ciede2000(skin_color, color)
    distances.append((name, color, dist))

print("\nClosest 10 blocks:")
for name, color, dist in sorted(distances, key=lambda x: x[2])[:10]:
    warmth = (color[0] + color[1])/2 - color[2]
    print(f"{name:40s} RGB{color} dist={dist:.1f} warmth={warmth:.1f}")
