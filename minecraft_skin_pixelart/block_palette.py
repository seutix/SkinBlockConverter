"""
BlockPalette module for loading and managing Minecraft block textures.
"""

import os
from typing import Dict, List, Tuple
from PIL import Image
import logging

from .exceptions import BlockDirectoryNotFoundError, BlockPaletteEmptyError

logger = logging.getLogger(__name__)


class BlockPalette:
    """Manages loading and indexing of Minecraft block textures."""
    
    def __init__(self, blocks_directory: str):
        """
        Initialize the block palette from the specified directory.
        
        Args:
            blocks_directory: Path to the directory containing block textures
        """
        self.blocks_directory = blocks_directory
        self.blocks: Dict[str, Image.Image] = {}
        self.average_colors: Dict[str, Tuple[int, int, int]] = {}
    
    def load_blocks(self) -> None:
        """Load all block textures and compute their average colors."""
        # Check if directory exists
        if not os.path.exists(self.blocks_directory):
            raise BlockDirectoryNotFoundError(
                f"Blocks directory not found: {self.blocks_directory}"
            )
        
        if not os.path.isdir(self.blocks_directory):
            raise BlockDirectoryNotFoundError(
                f"Path is not a directory: {self.blocks_directory}"
            )
        
        # Load all PNG files from the directory
        loaded_count = 0
        for filename in os.listdir(self.blocks_directory):
            if not filename.lower().endswith('.png'):
                continue
            
            filepath = os.path.join(self.blocks_directory, filename)
            block_name = os.path.splitext(filename)[0]
            
            try:
                # Load the image
                texture = Image.open(filepath)
                # Convert to RGBA to ensure consistent format
                texture = texture.convert('RGBA')
                
                # Store the texture
                self.blocks[block_name] = texture
                
                # Calculate and store average color
                avg_color = self._calculate_average_color(texture)
                self.average_colors[block_name] = avg_color
                
                loaded_count += 1
            except Exception as e:
                # Skip invalid files and log warning
                logger.warning(f"Skipping invalid block texture {filename}: {e}")
                continue
        
        # Check if any blocks were loaded
        if loaded_count == 0:
            raise BlockPaletteEmptyError(
                f"No block textures found in directory: {self.blocks_directory}"
            )
    
    def _calculate_average_color(self, texture: Image.Image) -> Tuple[int, int, int]:
        """
        Calculate the weighted average RGB color of a texture.
        Uses alpha channel as weight for more accurate color representation.
        
        Args:
            texture: PIL Image object
            
        Returns:
            Tuple of (r, g, b) representing the average color
        """
        # Get all pixel data with alpha
        pixels = list(texture.getdata())
        
        # Calculate weighted average for each channel
        r_sum = 0
        g_sum = 0
        b_sum = 0
        weight_sum = 0
        
        for pixel in pixels:
            r, g, b, a = pixel
            
            # Use alpha as weight (fully transparent pixels contribute nothing)
            weight = a / 255.0
            
            r_sum += r * weight
            g_sum += g * weight
            b_sum += b * weight
            weight_sum += weight
        
        # Avoid division by zero for fully transparent textures
        if weight_sum == 0:
            return (0, 0, 0)
        
        avg_r = round(r_sum / weight_sum)
        avg_g = round(g_sum / weight_sum)
        avg_b = round(b_sum / weight_sum)
        
        return (avg_r, avg_g, avg_b)
    
    def get_block_texture(self, block_name: str) -> Image.Image:
        """
        Get the texture for a specific block.
        
        Args:
            block_name: Name of the block
            
        Returns:
            PIL Image object of the block texture
            
        Raises:
            KeyError: If block_name is not found in the palette
        """
        return self.blocks[block_name]
    
    def get_all_blocks(self) -> List[Tuple[str, Tuple[int, int, int]]]:
        """
        Get all blocks with their average colors.
        
        Returns:
            List of tuples (block_name, average_color)
        """
        return [(name, self.average_colors[name]) for name in self.blocks.keys()]
