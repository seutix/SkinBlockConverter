from PIL import Image
import os

# Test skin color
skin = Image.open('your_skin.png').convert('RGBA')
pixels = [p for p in skin.getdata() if len(p) >= 4 and p[3] > 128]
test_color = (199, 184, 174)  # Typical beige skin color

print(f"Test skin color: RGB{test_color}")
print(f"Warmth: {(test_color[0] + test_color[1]) / 2 - test_color[2]}")
print(f"Saturation: {max(test_color) - min(test_color)}")
print()

# Check gray blocks
gray_blocks = ['gray_concrete.png', 'light_gray_concrete.png', 'polished_granite.png', 'terracotta.png']
print("Gray/neutral blocks:")
for block in gray_blocks:
    path = os.path.join('block', block)
    if os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        # Calculate average color
        pixels = list(img.getdata())
        r_sum = g_sum = b_sum = weight_sum = 0
        for r, g, b, a in pixels:
            weight = a / 255.0
            r_sum += r * weight
            g_sum += g * weight
            b_sum += b * weight
            weight_sum += weight
        if weight_sum > 0:
            avg = (round(r_sum/weight_sum), round(g_sum/weight_sum), round(b_sum/weight_sum))
            warmth = (avg[0] + avg[1]) / 2 - avg[2]
            sat = max(avg) - min(avg)
            print(f"  {block}: RGB{avg}, warmth={warmth:.1f}, sat={sat}")

print()

# Check beige blocks
beige_blocks = ['sandstone.png', 'birch_planks.png', 'oak_planks.png', 'smooth_sandstone.png']
print("Beige/warm blocks:")
for block in beige_blocks:
    path = os.path.join('block', block)
    if os.path.exists(path):
        img = Image.open(path).convert('RGBA')
        pixels = list(img.getdata())
        r_sum = g_sum = b_sum = weight_sum = 0
        for r, g, b, a in pixels:
            weight = a / 255.0
            r_sum += r * weight
            g_sum += g * weight
            b_sum += b * weight
            weight_sum += weight
        if weight_sum > 0:
            avg = (round(r_sum/weight_sum), round(g_sum/weight_sum), round(b_sum/weight_sum))
            warmth = (avg[0] + avg[1]) / 2 - avg[2]
            sat = max(avg) - min(avg)
            print(f"  {block}: RGB{avg}, warmth={warmth:.1f}, sat={sat}")
