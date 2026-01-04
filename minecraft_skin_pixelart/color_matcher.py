"""
ColorMatcher module for finding the closest block color to a given pixel.
"""

import math
from typing import Tuple, Optional


class ColorMatcher:
    """Finds the closest matching block for a given pixel color."""
    
    def __init__(self, block_palette):
        """
        Initialize the color matcher with a block palette.
        
        Args:
            block_palette: BlockPalette instance containing block textures
        """
        self.block_palette = block_palette
    
    def find_closest_block(self, pixel_color: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Find the block with the closest average color to the given pixel.
        Uses perceptual color distance for better matching.
        
        Args:
            pixel_color: RGBA tuple of the pixel color
            
        Returns:
            Name of the closest matching block, or None for transparent pixels
        """
        # Handle transparent pixels (alpha < 128)
        if len(pixel_color) >= 4 and pixel_color[3] < 128:
            return None
        
        # Extract RGB components (ignore alpha)
        pixel_rgb = pixel_color[:3]
        
        # Get all blocks with their average colors
        all_blocks = self.block_palette.get_all_blocks()
        
        # Find the block with minimum distance
        min_distance = float('inf')
        closest_block = None
        
        for block_name, block_color in all_blocks:
            distance = self.color_distance_ciede2000(pixel_rgb, block_color)
            if distance < min_distance:
                min_distance = distance
                closest_block = block_name
                
                # Early exit if we found a perfect match
                if distance == 0:
                    return closest_block
        
        return closest_block
    
    def _calculate_block_distance(self, target_color: Tuple[int, int, int], 
                                   texture: 'Image.Image') -> float:
        """
        Calculate the perceptual distance between target color 
        and the average color of the block texture.
        
        Args:
            target_color: RGB tuple of the target color
            texture: PIL Image of the block texture
            
        Returns:
            Distance to the block's average color
        """
        # Calculate weighted average color
        pixels = list(texture.getdata())
        r_sum = 0
        g_sum = 0
        b_sum = 0
        weight_sum = 0
        
        for pixel in pixels:
            r, g, b, a = pixel
            weight = a / 255.0
            r_sum += r * weight
            g_sum += g * weight
            b_sum += b * weight
            weight_sum += weight
        
        if weight_sum == 0:
            return float('inf')
        
        avg_color = (
            round(r_sum / weight_sum),
            round(g_sum / weight_sum),
            round(b_sum / weight_sum)
        )
        
        return self.color_distance_ciede2000(target_color, avg_color)
    
    @staticmethod
    def color_distance_ciede2000(color1: Tuple[int, int, int], 
                                  color2: Tuple[int, int, int]) -> float:
        """
        Calculate perceptual color distance using improved weighted Euclidean formula.
        This approximates CIEDE2000 and accounts for human color perception.
        Enhanced to better distinguish warm (beige/tan) from cool (gray) colors.
        
        Args:
            color1: First RGB color tuple
            color2: Second RGB color tuple
            
        Returns:
            Perceptual distance between the colors
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        # Calculate average red
        r_mean = (r1 + r2) / 2
        
        # Calculate differences
        delta_r = r1 - r2
        delta_g = g1 - g2
        delta_b = b1 - b2
        
        # Weighted Euclidean distance that accounts for human perception
        # Red perception varies based on average red value
        weight_r = 2 + r_mean / 256
        weight_g = 4.0
        weight_b = 2 + (255 - r_mean) / 256
        
        distance = math.sqrt(
            weight_r * delta_r * delta_r +
            weight_g * delta_g * delta_g +
            weight_b * delta_b * delta_b
        )
        
        # Add penalty for warm vs cool color mismatch
        # This helps distinguish beige/tan colors from gray colors
        warmth1 = (r1 + g1) / 2 - b1  # Positive for warm colors
        warmth2 = (r2 + g2) / 2 - b2
        
        # Calculate saturation (how colorful vs gray)
        sat1 = max(r1, g1, b1) - min(r1, g1, b1)
        sat2 = max(r2, g2, b2) - min(r2, g2, b2)
        
        # Penalty for warmth mismatch - but only if signs differ (warm vs cool)
        # Don't penalize if both are warm or both are cool, just different amounts
        if (warmth1 > 5 and warmth2 < -5) or (warmth1 < -5 and warmth2 > 5):
            # Strong penalty for warm-to-cool or cool-to-warm mismatch
            warmth_penalty = abs(warmth1 - warmth2) * 0.8
        else:
            # Light penalty for same-category warmth differences
            warmth_penalty = abs(warmth1 - warmth2) * 0.2
        
        # Penalty for saturation mismatch (colorful vs gray)
        # Increased to better distinguish saturated skin tones from gray blocks
        saturation_penalty = abs(sat1 - sat2) * 0.5
        
        # For medium-brightness colors (likely skin tones), strongly prefer warmer blocks
        # over gray blocks even if they're slightly further in pure RGB distance
        brightness1 = (r1 + g1 + b1) / 3
        brightness2 = (r2 + g2 + b2) / 3
        
        # If source is medium brightness (50-200) with some saturation, penalize gray/cool blocks
        if 50 < brightness1 < 200 and sat1 > 15:
            # If target block is gray (low saturation) and cool (low warmth)
            if sat2 < 15 and warmth2 < 10:
                # Add significant penalty for matching skin tones to gray blocks
                gray_penalty = 70.0
            else:
                gray_penalty = 0.0
        else:
            gray_penalty = 0.0
        
        return distance + warmth_penalty + saturation_penalty + gray_penalty
    
    @staticmethod
    def color_distance(color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int]) -> float:
        """
        Calculate Euclidean distance between two RGB colors.
        
        Args:
            color1: First RGB color tuple
            color2: Second RGB color tuple
            
        Returns:
            Euclidean distance between the colors
        """
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        
        # Euclidean distance: sqrt((r1-r2)² + (g1-g2)² + (b1-b2)²)
        return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
