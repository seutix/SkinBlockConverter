"""
SkinProcessor module for coordinating the skin conversion process.
"""

from PIL import Image
from .exceptions import (
    InvalidDimensionsError,
    InvalidImageError,
    OutputSaveError,
    ProcessingError
)


class SkinProcessor:
    """Coordinates the process of converting Minecraft skins to pixelart."""
    
    def __init__(self, block_palette, color_matcher):
        """
        Initialize the skin processor.
        
        Args:
            block_palette: BlockPalette instance
            color_matcher: ColorMatcher instance
        """
        self.block_palette = block_palette
        self.color_matcher = color_matcher
    
    def load_skin(self, skin_path: str) -> Image.Image:
        """
        Load and validate a 64x64 skin image.
        
        Args:
            skin_path: Path to the skin image file
            
        Returns:
            PIL Image object of the skin
            
        Raises:
            InvalidImageError: If file cannot be read as an image
            InvalidDimensionsError: If image is not 64x64 pixels
        """
        try:
            # Try to open the image
            with Image.open(skin_path) as skin:
                # Validate dimensions
                width, height = skin.size
                if width != 64 or height != 64:
                    raise InvalidDimensionsError(
                        f"Invalid skin dimensions: {width}x{height}. Expected 64x64."
                    )
                
                # Convert to RGBA for consistent processing and load into memory
                # This creates a copy that's independent of the file
                skin = skin.convert('RGBA')
                # Force load into memory to close the file
                skin.load()
                
                return skin
        except InvalidDimensionsError:
            # Re-raise our custom exception
            raise
        except Exception as e:
            raise InvalidImageError(
                f"Cannot read image file: {skin_path}. File may be corrupted or not an image."
            ) from e
    
    def process_skin(self, skin: Image.Image) -> Image.Image:
        """
        Process the skin and create a 1024x1024 output image.
        Each pixel gets the best matching block based on color similarity.
        
        Args:
            skin: Input skin image (64x64)
            
        Returns:
            Output image (1024x1024) with block textures
        """
        print("      • Analyzing skin colors...", flush=True)
        
        # Build a cache for color-to-block mapping to avoid redundant calculations
        color_to_block_cache = {}
        
        # Render the output image
        print("      • Rendering output image...", flush=True)
        output = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
        
        total_pixels = 64 * 64
        processed = 0
        
        # Iterate over each pixel in the 64x64 skin
        for y in range(64):
            for x in range(64):
                # Get the pixel color at position (x, y)
                pixel_color = skin.getpixel((x, y))
                
                # Skip transparent pixels
                if len(pixel_color) >= 4 and pixel_color[3] < 128:
                    processed += 1
                    continue
                
                # Get RGB color
                rgb = pixel_color[:3]
                
                # Check cache first
                if rgb not in color_to_block_cache:
                    # Find the best matching block for this color
                    block_name = self.color_matcher.find_closest_block(pixel_color)
                    color_to_block_cache[rgb] = block_name
                else:
                    block_name = color_to_block_cache[rgb]
                
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
                
                # Print progress every 512 pixels
                if processed % 512 == 0:
                    progress = (processed / total_pixels) * 100
                    print(f"      • Progress: {progress:.1f}% ({processed}/{total_pixels} pixels)", flush=True)
        
        print(f"      • Used {len(color_to_block_cache)} unique colors", flush=True)
        
        return output

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
            output_path = "minecraft_skin_output.png"
        
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
    
    def convert_skin(self, input_path: str, output_path: str = None) -> None:
        """
        Complete conversion process from input file to output file.
        
        Args:
            input_path: Path to input skin file
            output_path: Path to save output file (optional, uses default if None)
            
        Raises:
            InvalidImageError: If input file cannot be read
            InvalidDimensionsError: If input is not 64x64
            ProcessingError: If processing fails
            OutputSaveError: If output cannot be saved
        """
        try:
            # Step 1: Load and validate the skin
            skin = self.load_skin(input_path)
            
            # Step 2: Process the skin to create output image
            output_image = self.process_skin(skin)
            
            # Step 3: Save the output
            self.save_output(output_image, output_path)
            
        except (InvalidImageError, InvalidDimensionsError, OutputSaveError):
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            # Wrap any unexpected errors in ProcessingError
            raise ProcessingError(
                f"Error processing skin: {str(e)}"
            ) from e
