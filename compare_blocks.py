from PIL import Image, ImageDraw, ImageFont
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher

# Your main skin color
skin_color = (183, 160, 149)

# Load palette
palette = BlockPalette('block')
palette.load_blocks()

# Get top candidates
candidates = [
    'white_terracotta',
    'test_block_start', 
    'stripped_cherry_log',
    'cherry_planks',
    'raw_iron_block',
    'birch_planks',
    'light_gray_concrete',
]

# Create comparison image
block_size = 64
img_width = block_size * len(candidates)
img_height = block_size * 2

img = Image.new('RGB', (img_width, img_height), color='white')

# Draw skin color on top row
for i in range(len(candidates)):
    for x in range(block_size):
        for y in range(block_size):
            img.putpixel((i * block_size + x, y), skin_color)

# Draw block textures on bottom row
for i, block_name in enumerate(candidates):
    texture = palette.get_block_texture(block_name).resize((block_size, block_size))
    img.paste(texture, (i * block_size, block_size))

img.save('comparison.png')
print(f"Saved comparison.png")
print(f"\nSkin color: RGB{skin_color}")
print(f"\nBlocks (left to right):")
for i, block_name in enumerate(candidates, 1):
    block_color = palette.average_colors[block_name]
    dist = ColorMatcher.color_distance_ciede2000(skin_color, block_color)
    # Simple distance without penalties
    simple_dist = ColorMatcher.color_distance(skin_color, block_color)
    print(f"{i}. {block_name:30s} RGB{block_color} ciede={dist:5.1f} simple={simple_dist:5.1f}")
