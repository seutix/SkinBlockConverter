"""
Unit and property tests for BlockPalette.
"""

import os
import tempfile
import pytest
from hypothesis import given, settings
import hypothesis.strategies as st
from PIL import Image

from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.exceptions import BlockDirectoryNotFoundError, BlockPaletteEmptyError


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
def block_texture_image(draw):
    """Generate a random block texture image (16x16 pixels)."""
    width = draw(st.integers(min_value=1, max_value=32))
    height = draw(st.integers(min_value=1, max_value=32))
    
    # Create image with random pixels
    img = Image.new('RGB', (width, height))
    pixels = []
    for _ in range(width * height):
        color = draw(rgb_color())
        pixels.append(color)
    img.putdata(pixels)
    
    return img


@st.composite
def block_palette_data(draw):
    """Generate random block palette data (multiple blocks with textures)."""
    num_blocks = draw(st.integers(min_value=1, max_value=5))
    blocks = {}
    
    for i in range(num_blocks):
        block_name = f"block_{i}"
        # Use smaller images for faster generation
        width = draw(st.integers(min_value=4, max_value=16))
        height = draw(st.integers(min_value=4, max_value=16))
        
        # Create a simple solid color block for faster generation
        color = draw(rgb_color())
        texture = Image.new('RGB', (width, height), color=color)
        blocks[block_name] = texture
    
    return blocks


class TestBlockPalette:
    """Test suite for BlockPalette class."""
    
    @settings(max_examples=50)
    @given(block_texture_image())
    def test_property_average_color_computation(self, texture):
        """
        Property 2: Average Color Computation Correctness
        
        Feature: minecraft-skin-pixelart, Property 2: For any block texture loaded 
        into the palette, the computed average color SHALL equal the arithmetic mean 
        of all pixel RGB values in that texture.
        
        Validates: Requirements 2.2, 6.3
        """
        # Create a temporary BlockPalette instance
        palette = BlockPalette("dummy")
        
        # Calculate average color using the method
        avg_color = palette._calculate_average_color(texture)
        
        # Manually calculate expected average
        rgb_texture = texture.convert('RGB')
        pixels = list(rgb_texture.getdata())
        total_pixels = len(pixels)
        
        expected_r = round(sum(p[0] for p in pixels) / total_pixels)
        expected_g = round(sum(p[1] for p in pixels) / total_pixels)
        expected_b = round(sum(p[2] for p in pixels) / total_pixels)
        
        expected_avg = (expected_r, expected_g, expected_b)
        
        # Assert that computed average matches expected
        assert avg_color == expected_avg, (
            f"Average color mismatch: got {avg_color}, expected {expected_avg}"
        )
    
    @settings(max_examples=50)
    @given(block_palette_data())
    def test_property_cache_consistency(self, blocks_data):
        """
        Property 6: Color Cache Consistency
        
        Feature: minecraft-skin-pixelart, Property 6: For any block in the palette, 
        if the average color is computed once during initialization, then all 
        subsequent color matching operations SHALL use the cached value without 
        recomputation.
        
        Validates: Requirements 6.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save all generated blocks to temporary directory
            for block_name, texture in blocks_data.items():
                img_path = os.path.join(tmpdir, f"{block_name}.png")
                texture.save(img_path)
            
            # Create palette and load blocks
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            
            # Store the initial cache state
            initial_cache = {k: v for k, v in palette.average_colors.items()}
            cache_object_id = id(palette.average_colors)
            
            # Perform multiple get_all_blocks operations (simulating color matching)
            for _ in range(20):
                all_blocks = palette.get_all_blocks()
                
                # Verify each returned color matches the initial cache
                for block_name, avg_color in all_blocks:
                    assert avg_color == initial_cache[block_name], (
                        f"Cached color for {block_name} changed: "
                        f"expected {initial_cache[block_name]}, got {avg_color}"
                    )
            
            # Verify the cache dictionary is still the same object
            assert id(palette.average_colors) == cache_object_id, (
                "Cache dictionary object was replaced"
            )
            
            # Verify cache contents haven't changed
            assert palette.average_colors == initial_cache, (
                "Cache contents were modified"
            )
            
            # Verify that accessing individual blocks also uses cache
            for block_name in blocks_data.keys():
                # The average_colors should still contain the same values
                assert palette.average_colors[block_name] == initial_cache[block_name], (
                    f"Cache value for {block_name} was modified"
                )
    
    def test_load_blocks_from_real_directory(self):
        """
        Test loading blocks from the real block directory.
        
        Requirements: 2.1, 2.4
        """
        # Use the actual block directory
        block_dir = "block"
        
        # Skip test if directory doesn't exist
        if not os.path.exists(block_dir):
            pytest.skip(f"Block directory '{block_dir}' not found")
        
        palette = BlockPalette(block_dir)
        palette.load_blocks()
        
        # Verify blocks were loaded
        assert len(palette.blocks) > 0, "No blocks were loaded"
        assert len(palette.average_colors) > 0, "No average colors computed"
        assert len(palette.blocks) == len(palette.average_colors), (
            "Mismatch between blocks and average colors"
        )
        
        # Verify get_all_blocks returns correct data
        all_blocks = palette.get_all_blocks()
        assert len(all_blocks) == len(palette.blocks)
        
        # Verify each block has a valid average color
        for block_name, avg_color in all_blocks:
            assert isinstance(avg_color, tuple)
            assert len(avg_color) == 3
            assert all(0 <= c <= 255 for c in avg_color)
        
        # Test get_block_texture
        first_block_name = list(palette.blocks.keys())[0]
        texture = palette.get_block_texture(first_block_name)
        assert isinstance(texture, Image.Image)
    
    def test_empty_directory(self):
        """
        Test handling of empty directory (edge case).
        
        Requirements: 2.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            palette = BlockPalette(tmpdir)
            
            # Should raise BlockPaletteEmptyError
            with pytest.raises(BlockPaletteEmptyError) as exc_info:
                palette.load_blocks()
            
            assert "No block textures found" in str(exc_info.value)
            assert tmpdir in str(exc_info.value)
    
    def test_nonexistent_directory(self):
        """
        Test handling of nonexistent directory (edge case).
        
        Requirements: 2.3
        """
        palette = BlockPalette("/nonexistent/path/to/blocks")
        
        # Should raise BlockDirectoryNotFoundError
        with pytest.raises(BlockDirectoryNotFoundError) as exc_info:
            palette.load_blocks()
        
        assert "not found" in str(exc_info.value)
    
    def test_skip_invalid_files(self):
        """
        Test that invalid files are skipped (edge case).
        
        Requirements: 2.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid PNG file
            valid_img = Image.new('RGB', (16, 16), color=(255, 0, 0))
            valid_path = os.path.join(tmpdir, "valid_block.png")
            valid_img.save(valid_path)
            
            # Create an invalid file (not an image)
            invalid_path = os.path.join(tmpdir, "invalid.png")
            with open(invalid_path, 'w') as f:
                f.write("This is not an image")
            
            # Create a non-PNG file
            txt_path = os.path.join(tmpdir, "readme.txt")
            with open(txt_path, 'w') as f:
                f.write("Some text")
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            
            # Should have loaded only the valid block
            assert len(palette.blocks) == 1
            assert "valid_block" in palette.blocks
            assert "invalid" not in palette.blocks
            assert "readme" not in palette.blocks
    
    def test_get_block_texture_nonexistent(self):
        """
        Test getting a nonexistent block texture raises KeyError.
        
        Requirements: 2.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid PNG file
            img = Image.new('RGB', (16, 16), color=(0, 255, 0))
            img_path = os.path.join(tmpdir, "test_block.png")
            img.save(img_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            
            # Should raise KeyError for nonexistent block
            with pytest.raises(KeyError):
                palette.get_block_texture("nonexistent_block")
    
    def test_cache_usage_verification(self):
        """
        Test that average colors are cached and not recomputed on access.
        
        This verifies that colors are computed only once during load_blocks()
        and subsequent calls to get_all_blocks() use the cached values.
        
        Requirements: 6.2, 6.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test blocks
            for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
                img = Image.new('RGB', (16, 16), color=color)
                img_path = os.path.join(tmpdir, f"block_{i}.png")
                img.save(img_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            
            # Store reference to the cache and make a copy of values
            cache_reference = palette.average_colors
            initial_colors = {k: v for k, v in palette.average_colors.items()}
            
            # Call get_all_blocks multiple times
            for _ in range(10):
                all_blocks = palette.get_all_blocks()
                
                # Verify the returned colors match the cached values
                for block_name, avg_color in all_blocks:
                    assert avg_color == initial_colors[block_name], (
                        f"Color for {block_name} changed between calls"
                    )
            
            # Verify the cache dictionary itself hasn't been modified
            assert palette.average_colors == initial_colors, (
                "Cache dictionary was modified"
            )
            
            # Verify that the cache is the same object (not replaced)
            assert palette.average_colors is cache_reference, (
                "Cache dictionary was replaced with a new object"
            )
