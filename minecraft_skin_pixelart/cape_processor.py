"""
CapeProcessor module for coordinating the cape conversion process.
"""

from PIL import Image
from .exceptions import (
    InvalidDimensionsError,
    InvalidImageError,
    OutputSaveError,
    ProcessingError
)


class CapeProcessor:
    """Coordinates the process of converting Minecraft capes to pixelart."""
    
    def __init__(self, block_palette, color_matcher):
        """
        Initialize the cape processor.
        
        Args:
            block_palette: BlockPalette instance
            color_matcher: ColorMatcher instance
        """
        self.block_palette = block_palette
        self.color_matcher = color_matcher
    
    def load_cape(self, cape_path: str) -> Image.Image:
        """
        Load and validate a 64x32 cape image.
        
        Args:
            cape_path: Path to the cape image file
            
        Returns:
            PIL Image object of the cape
            
        Raises:
            InvalidImageError: If file cannot be read as an image
            InvalidDimensionsError: If image is not 64x32 pixels
        """
        try:
            # Try to open the image
            with Image.open(cape_path) as cape:
                # Validate dimensions
                width, height = cape.size
                if width != 64 or height != 32:
                    raise InvalidDimensionsError(
                        f"Invalid cape dimensions: {width}x{height}. Expected 64x32."
                    )
                
                # Convert to RGBA for consistent processing and load into memory
                cape = cape.convert('RGBA')
                cape.load()
                
                return cape
        except InvalidDimensionsError:
            raise
        except Exception as e:
            raise InvalidImageError(
                f"Cannot read image file: {cape_path}. File may be corrupted or not an image."
            ) from e
    
    def process_cape(self, cape: Image.Image) -> Image.Image:
        """
        Process the cape and create a 1024x512 output image.
        Uses a two-pass approach:
        1. First pass: collect all unique colors in the cape
        2. Second pass: assign unique blocks to each color and render
        
        Args:
            cape: Input cape image (64x32)
            
        Returns:
            Output image (1024x512) with block textures
        """
        print("      • Analyzing unique colors in cape...", flush=True)
        
        # PASS 1: Collect all unique colors
        unique_colors = set()
        for y in range(32):
            for x in range(64):
                pixel_color = cape.getpixel((x, y))
                # Only include opaque pixels
                if len(pixel_color) >= 4 and pixel_color[3] >= 128:
                    unique_colors.add(pixel_color[:3])  # Store RGB only
        
        print(f"      • Found {len(unique_colors)} unique colors", flush=True)
        print("      • Assigning unique blocks to each color...", flush=True)
        
        # PASS 2: Assign a unique block to each unique color
        color_to_block = {}
        used_blocks = set()
        
        # Sort colors by frequency (most common first) for better block assignment
        color_frequency = {}
        for y in range(32):
            for x in range(64):
                pixel_color = cape.getpixel((x, y))
                if len(pixel_color) >= 4 and pixel_color[3] >= 128:
                    rgb = pixel_color[:3]
                    color_frequency[rgb] = color_frequency.get(rgb, 0) + 1
        
        # Sort by frequency (descending)
        sorted_colors = sorted(unique_colors, key=lambda c: color_frequency[c], reverse=True)
        
        # Get all available blocks sorted by their suitability for each color
        for color in sorted_colors:
            # Find the best unused block for this color
            best_block = self._find_best_unused_block(color, used_blocks)
            if best_block:
                color_to_block[color] = best_block
                used_blocks.add(best_block)
        
        print(f"      • Assigned {len(color_to_block)} blocks", flush=True)
        
        # PASS 3: Render the output image
        print("      • Rendering output image...", flush=True)
        output = Image.new('RGBA', (1024, 512), (0, 0, 0, 0))
        
        total_pixels = 64 * 32
        processed = 0
        
        # Iterate over each pixel in the 64x32 cape
        for y in range(32):
            for x in range(64):
                # Get the pixel color at position (x, y)
                pixel_color = cape.getpixel((x, y))
                
                # Skip transparent pixels
                if len(pixel_color) >= 4 and pixel_color[3] < 128:
                    processed += 1
                    continue
                
                # Get RGB color
                rgb = pixel_color[:3]
                
                # Get the assigned block for this color
                block_name = color_to_block.get(rgb)
                
                if block_name is None:
                    processed += 1
                    continue
                
                # Get the block texture
                block_texture = self.block_palette.get_block_texture(block_name)
                
                # Calculate position in output image (x*16, y*16)
                output_x = x * 16
                output_y = y * 16
                
                # Paste the block texture at the calculated position
                output.paste(block_texture, (output_x, output_y))
                
                processed += 1
                
                # Print progress every 256 pixels
                if processed % 256 == 0:
                    progress = (processed / total_pixels) * 100
                    print(f"      • Progress: {progress:.1f}% ({processed}/{total_pixels} pixels)", flush=True)
        
        return output
    
    def _find_best_unused_block(self, color, used_blocks):
        """
        Find the best matching block for a color that hasn't been used yet.
        
        Args:
            color: RGB tuple
            used_blocks: Set of already used block names
            
        Returns:
            Best matching unused block name, or None if all blocks are used
        """
        # Get all blocks with their distances
        all_blocks = self.block_palette.get_all_blocks()
        
        # Calculate distances and filter out used blocks
        candidates = []
        for block_name, block_color in all_blocks:
            if block_name not in used_blocks:
                distance = self.color_matcher.color_distance_ciede2000(color, block_color)
                candidates.append((distance, block_name))
        
        # If no unused blocks available, return None
        if not candidates:
            return None
        
        # Sort by distance and return the closest
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    def save_output(self, output_image: Image.Image, output_path: str = None) -> None:
        """
        Save the output image to a file.
        
        Args:
            output_image: The processed image to save
            output_path: Path where to save the output. If None, uses default name.
            
        Raises:
            OutputSaveError: If the file cannot be saved
        """
        import os
        
        # Use default name if path not specified
        if output_path is None:
            output_path = "minecraft_cape_output.png"
        
        # Handle file name conflicts by adding suffix
        if os.path.exists(output_path):
            base, ext = os.path.splitext(output_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            output_path = f"{base}_{counter}{ext}"
        
        try:
            # Save as PNG format
            output_image.save(output_path, 'PNG')
        except Exception as e:
            raise OutputSaveError(
                f"Cannot save output to: {output_path}. {str(e)}"
            ) from e
    
    def convert_cape(self, input_path: str, output_path: str = None) -> None:
        """
        Complete conversion process from input file to output file.
        
        Args:
            input_path: Path to input cape file
            output_path: Path to save output file (optional, uses default if None)
            
        Raises:
            InvalidImageError: If input file cannot be read
            InvalidDimensionsError: If input is not 64x32
            ProcessingError: If processing fails
            OutputSaveError: If output cannot be saved
        """
        try:
            # Step 1: Load and validate the cape
            cape = self.load_cape(input_path)
            
            # Step 2: Process the cape to create output image
            output_image = self.process_cape(cape)
            
            # Step 3: Save the output
            self.save_output(output_image, output_path)
            
        except (InvalidImageError, InvalidDimensionsError, OutputSaveError):
            raise
        except Exception as e:
            raise ProcessingError(
                f"Error processing cape: {str(e)}"
            ) from e
