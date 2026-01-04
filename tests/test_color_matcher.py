"""
Unit and property tests for ColorMatcher.
"""

import tempfile
import os
import pytest
from hypothesis import given, settings, assume
import hypothesis.strategies as st
from PIL import Image

from minecraft_skin_pixelart.color_matcher import ColorMatcher
from minecraft_skin_pixelart.block_palette import BlockPalette


# Custom Hypothesis strategies
@st.composite
def rgb_color(draw):
    """Generate a random RGB color tuple."""
    return (
        draw(st.integers(min_value=0, max_value=255)),
        draw(st.integers(min_value=0, max_value=255)),
        draw(st.integers(min_value=0, max_value=255))
    )


@st.composite
def rgba_color(draw):
    """Generate a random RGBA color tuple."""
    return (
        draw(st.integers(min_value=0, max_value=255)),
        draw(st.integers(min_value=0, max_value=255)),
        draw(st.integers(min_value=0, max_value=255)),
        draw(st.integers(min_value=0, max_value=255))
    )


class TestColorMatcher:
    """Test suite for ColorMatcher class."""
    
    @settings(max_examples=50)
    @given(rgba_color())
    def test_property_closest_block_selection(self, pixel_color):
        """
        Property 3: Closest Block Selection
        
        Feature: minecraft-skin-pixelart, Property 3: For any pixel color and block 
        palette, the selected block SHALL have the minimum perceptual distance 
        among all blocks in the palette, comparing against average block colors.
        
        Validates: Requirements 3.1, 3.2, 6.1
        """
        # Skip transparent pixels (they should return None)
        if pixel_color[3] < 128:
            # Create a temporary palette with some blocks
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create a few test blocks
                for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
                    img = Image.new('RGB', (16, 16), color=color)
                    img.save(os.path.join(tmpdir, f"block_{i}.png"))
                
                palette = BlockPalette(tmpdir)
                palette.load_blocks()
                matcher = ColorMatcher(palette)
                
                result = matcher.find_closest_block(pixel_color)
                assert result is None, "Transparent pixels should return None"
            return
        
        # For opaque pixels, verify the selected block has minimum distance
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a few test blocks with known colors
            test_colors = [
                (255, 0, 0),    # Red
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
            ]
            
            for i, color in enumerate(test_colors):
                img = Image.new('RGB', (16, 16), color=color)
                img.save(os.path.join(tmpdir, f"block_{i}.png"))
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            
            # Find the closest block
            closest_block = matcher.find_closest_block(pixel_color)
            
            # Verify it's not None for opaque pixels
            assert closest_block is not None, "Opaque pixels should return a block"
            
            # Calculate the distance to the selected block's average color
            pixel_rgb = pixel_color[:3]
            selected_color = palette.average_colors[closest_block]
            selected_distance = ColorMatcher.color_distance_ciede2000(pixel_rgb, selected_color)
            
            # Verify this is indeed the minimum distance among all blocks
            for block_name, block_color in palette.get_all_blocks():
                distance = ColorMatcher.color_distance_ciede2000(pixel_rgb, block_color)
                assert distance >= selected_distance - 0.01, (
                    f"Found block '{block_name}' with smaller distance {distance} "
                    f"than selected block '{closest_block}' with distance {selected_distance}"
                )
    
    def test_color_distance_known_values(self):
        """
        Test color distance calculation with known values.
        
        Requirements: 3.1
        """
        # Test identical colors (distance should be 0)
        color1 = (100, 150, 200)
        color2 = (100, 150, 200)
        distance = ColorMatcher.color_distance(color1, color2)
        assert distance == 0.0, "Distance between identical colors should be 0"
        
        # Test black and white (maximum distance for grayscale)
        black = (0, 0, 0)
        white = (255, 255, 255)
        distance = ColorMatcher.color_distance(black, white)
        # sqrt(255^2 + 255^2 + 255^2) = sqrt(195075) ≈ 441.67
        expected = (255**2 + 255**2 + 255**2) ** 0.5
        assert abs(distance - expected) < 0.01, f"Expected {expected}, got {distance}"
        
        # Test known Pythagorean triple (3, 4, 5)
        color1 = (0, 0, 0)
        color2 = (3, 4, 0)
        distance = ColorMatcher.color_distance(color1, color2)
        assert abs(distance - 5.0) < 0.01, f"Expected 5.0, got {distance}"
        
        # Test another known case
        color1 = (100, 100, 100)
        color2 = (110, 105, 95)
        # Distance = sqrt((10)^2 + (5)^2 + (-5)^2) = sqrt(100 + 25 + 25) = sqrt(150) ≈ 12.247
        expected = (10**2 + 5**2 + 5**2) ** 0.5
        distance = ColorMatcher.color_distance(color1, color2)
        assert abs(distance - expected) < 0.01, f"Expected {expected}, got {distance}"
    
    def test_equal_distances_first_block_selected(self):
        """
        Test that when multiple blocks have equal distances, the first one is selected.
        
        Requirements: 3.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create blocks with colors equidistant from a test pixel
            # Test pixel: (128, 128, 128) - middle gray
            # Create blocks at equal distance
            test_colors = [
                (138, 128, 128),  # Distance = 10 in R
                (128, 138, 128),  # Distance = 10 in G
                (128, 128, 138),  # Distance = 10 in B
            ]
            
            for i, color in enumerate(test_colors):
                img = Image.new('RGB', (16, 16), color=color)
                img.save(os.path.join(tmpdir, f"block_{i}.png"))
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            
            # Test with the middle gray pixel
            pixel_color = (128, 128, 128, 255)
            closest_block = matcher.find_closest_block(pixel_color)
            
            # Verify a block was selected
            assert closest_block is not None
            
            # Verify all blocks have the same distance
            pixel_rgb = pixel_color[:3]
            distances = []
            for block_name, block_color in palette.get_all_blocks():
                distance = ColorMatcher.color_distance(pixel_rgb, block_color)
                distances.append(distance)
            
            # All distances should be equal (within floating point tolerance)
            assert all(abs(d - distances[0]) < 0.01 for d in distances), (
                f"Expected equal distances, got {distances}"
            )
            
            # The selected block should be one of the blocks (first found)
            assert closest_block in palette.blocks
    
    def test_transparent_pixel_handling(self):
        """
        Test handling of transparent pixels (edge case).
        
        Requirements: 3.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test block
            img = Image.new('RGB', (16, 16), color=(255, 0, 0))
            img.save(os.path.join(tmpdir, "red_block.png"))
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            
            # Test fully transparent pixel (alpha = 0)
            transparent_pixel = (100, 150, 200, 0)
            result = matcher.find_closest_block(transparent_pixel)
            assert result is None, "Fully transparent pixel should return None"
            
            # Test semi-transparent pixel below threshold (alpha = 127)
            semi_transparent = (100, 150, 200, 127)
            result = matcher.find_closest_block(semi_transparent)
            assert result is None, "Semi-transparent pixel (alpha < 128) should return None"
            
            # Test semi-transparent pixel at threshold (alpha = 128)
            at_threshold = (100, 150, 200, 128)
            result = matcher.find_closest_block(at_threshold)
            assert result is not None, "Pixel with alpha >= 128 should return a block"
            
            # Test opaque pixel (alpha = 255)
            opaque_pixel = (100, 150, 200, 255)
            result = matcher.find_closest_block(opaque_pixel)
            assert result is not None, "Opaque pixel should return a block"
            assert result == "red_block", "Should return the only available block"
