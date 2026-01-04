"""
Unit and property tests for SkinProcessor.
"""

import os
import tempfile
import pytest
from hypothesis import given, settings, assume, HealthCheck
import hypothesis.strategies as st
from PIL import Image

from minecraft_skin_pixelart.skin_processor import SkinProcessor
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher
from minecraft_skin_pixelart.exceptions import InvalidDimensionsError, InvalidImageError


# Custom Hypothesis strategies
@st.composite
def image_dimensions(draw):
    """Generate random image dimensions."""
    width = draw(st.integers(min_value=1, max_value=128))
    height = draw(st.integers(min_value=1, max_value=128))
    return (width, height)


@st.composite
def skin_image_with_dimensions(draw):
    """Generate a random image with specified dimensions."""
    width, height = draw(image_dimensions())
    
    # Create image - use simpler color generation for speed
    img = Image.new('RGBA', (width, height))
    
    # Generate a single random color and fill the image (much faster)
    r = draw(st.integers(min_value=0, max_value=255))
    g = draw(st.integers(min_value=0, max_value=255))
    b = draw(st.integers(min_value=0, max_value=255))
    a = draw(st.integers(min_value=0, max_value=255))
    
    # Fill with solid color for speed
    pixels = [(r, g, b, a)] * (width * height)
    img.putdata(pixels)
    
    return img


class TestSkinProcessor:
    """Test suite for SkinProcessor class."""
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @given(skin_image_with_dimensions())
    def test_property_input_validation_consistency(self, test_image):
        """
        Property 1: Input Validation Consistency
        
        Feature: minecraft-skin-pixelart, Property 1: For any image file provided 
        as input, if the image dimensions are exactly 64x64 pixels, then the system 
        SHALL successfully load it; otherwise, the system SHALL reject it with an 
        appropriate error message.
        
        Validates: Requirements 1.1, 1.2, 1.3
        """
        # Create a minimal BlockPalette and ColorMatcher for testing
        # We don't need actual blocks for this test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Save test image to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                test_image.save(tmp_path, 'PNG')
                width, height = test_image.size
                
                if width == 64 and height == 64:
                    # Should successfully load
                    loaded_skin = processor.load_skin(tmp_path)
                    assert loaded_skin is not None
                    assert loaded_skin.size == (64, 64)
                    # Close the loaded image to release file handle
                    loaded_skin.close()
                else:
                    # Should raise InvalidDimensionsError
                    with pytest.raises(InvalidDimensionsError) as exc_info:
                        processor.load_skin(tmp_path)
                    
                    # Verify error message contains dimension information
                    error_msg = str(exc_info.value)
                    assert "Invalid skin dimensions" in error_msg
                    assert f"{width}x{height}" in error_msg
                    assert "64x64" in error_msg
            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except PermissionError:
                    # On Windows, file might still be locked
                    pass
    
    def test_load_valid_64x64_skin(self):
        """
        Test loading a valid 64x64 skin.
        
        Requirements: 1.1, 1.2, 1.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Create a valid 64x64 skin
            skin = Image.new('RGBA', (64, 64), color=(255, 0, 0, 255))
            skin_path = os.path.join(tmpdir, "test_skin.png")
            skin.save(skin_path)
            
            # Load the skin
            loaded_skin = processor.load_skin(skin_path)
            
            # Verify it was loaded correctly
            assert loaded_skin is not None
            assert loaded_skin.size == (64, 64)
            assert loaded_skin.mode == 'RGBA'
    
    def test_reject_wrong_dimensions(self):
        """
        Test rejection of skins with wrong dimensions (63x63, 65x65, 128x128).
        
        Requirements: 1.1, 1.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Test various wrong dimensions
            wrong_dimensions = [(63, 63), (65, 65), (128, 128), (64, 32), (32, 64)]
            
            for width, height in wrong_dimensions:
                # Create a skin with wrong dimensions
                skin = Image.new('RGBA', (width, height), color=(0, 255, 0, 255))
                skin_path = os.path.join(tmpdir, f"skin_{width}x{height}.png")
                skin.save(skin_path)
                skin.close()  # Close to release file handle
                
                # Should raise InvalidDimensionsError
                try:
                    with pytest.raises(InvalidDimensionsError) as exc_info:
                        processor.load_skin(skin_path)
                    
                    # Verify error message
                    error_msg = str(exc_info.value)
                    assert "Invalid skin dimensions" in error_msg
                    assert f"{width}x{height}" in error_msg
                    assert "64x64" in error_msg
                finally:
                    # Clean up the file immediately
                    try:
                        os.unlink(skin_path)
                    except (PermissionError, FileNotFoundError):
                        pass
    
    def test_handle_corrupted_files(self):
        """
        Test handling of corrupted/invalid image files (edge case).
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Create a corrupted file (not an image)
            corrupted_path = os.path.join(tmpdir, "corrupted.png")
            with open(corrupted_path, 'w') as f:
                f.write("This is not an image file")
            
            # Should raise InvalidImageError
            with pytest.raises(InvalidImageError) as exc_info:
                processor.load_skin(corrupted_path)
            
            # Verify error message
            error_msg = str(exc_info.value)
            assert "Cannot read image file" in error_msg
            assert corrupted_path in error_msg
            assert "corrupted or not an image" in error_msg
    
    def test_handle_nonexistent_file(self):
        """
        Test handling of nonexistent file (edge case).
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Try to load a nonexistent file
            nonexistent_path = os.path.join(tmpdir, "nonexistent.png")
            
            # Should raise InvalidImageError
            with pytest.raises(InvalidImageError) as exc_info:
                processor.load_skin(nonexistent_path)
            
            # Verify error message
            error_msg = str(exc_info.value)
            assert "Cannot read image file" in error_msg



# Custom Hypothesis strategies for process_skin tests
@st.composite
def valid_skin_image(draw):
    """Generate a random valid 64x64 skin image."""
    img = Image.new('RGBA', (64, 64))
    
    # Generate random pixels
    pixels = []
    for _ in range(64 * 64):
        r = draw(st.integers(min_value=0, max_value=255))
        g = draw(st.integers(min_value=0, max_value=255))
        b = draw(st.integers(min_value=0, max_value=255))
        a = draw(st.integers(min_value=0, max_value=255))
        pixels.append((r, g, b, a))
    
    img.putdata(pixels)
    return img


class TestSkinProcessing:
    """Test suite for skin processing functionality."""
    
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example, HealthCheck.data_too_large])
    @given(valid_skin_image())
    def test_property_output_image_structure(self, skin):
        """
        Property 4: Output Image Structure
        
        Feature: minecraft-skin-pixelart, Property 4: For any valid 64x64 input skin,
        the output image SHALL be exactly 1024x1024 pixels, and each 16x16 block region
        at position (x*16, y*16) SHALL contain the texture of the block matched to the
        pixel at position (x, y) in the input.
        
        Validates: Requirements 4.1, 4.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette with a few test blocks
            test_blocks = [
                ('red', (255, 0, 0)),
                ('green', (0, 255, 0)),
                ('blue', (0, 0, 255)),
                ('white', (255, 255, 255)),
                ('black', (0, 0, 0)),
            ]
            
            for block_name, color in test_blocks:
                block_img = Image.new('RGB', (16, 16), color=color)
                block_path = os.path.join(tmpdir, f"{block_name}.png")
                block_img.save(block_path)
            
            # Initialize components
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Process the skin
            output = processor.process_skin(skin)
            
            # Property 1: Output must be exactly 1024x1024
            assert output.size == (1024, 1024), \
                f"Output size should be 1024x1024, got {output.size}"
            
            # Property 2: Each 16x16 region should contain the matched block texture
            # We'll verify this by checking a sample of positions
            for y in range(0, 64, 8):  # Sample every 8th pixel for performance
                for x in range(0, 64, 8):
                    # Get the pixel color from input
                    pixel_color = skin.getpixel((x, y))
                    
                    # Find what block should be matched
                    expected_block = matcher.find_closest_block(pixel_color)
                    
                    # If transparent, skip
                    if expected_block is None:
                        continue
                    
                    # Get the expected block texture
                    expected_texture = palette.get_block_texture(expected_block)
                    
                    # Get the 16x16 region from output at position (x*16, y*16)
                    output_x = x * 16
                    output_y = y * 16
                    output_region = output.crop((
                        output_x, 
                        output_y, 
                        output_x + 16, 
                        output_y + 16
                    ))
                    
                    # Convert both to RGB for comparison (ignore alpha differences)
                    expected_rgb = expected_texture.convert('RGB')
                    output_rgb = output_region.convert('RGB')
                    
                    # Compare the textures
                    assert output_rgb.size == (16, 16), \
                        f"Output region should be 16x16, got {output_rgb.size}"
                    
                    # Verify the texture matches by comparing pixel data
                    expected_pixels = list(expected_rgb.getdata())
                    output_pixels = list(output_rgb.getdata())
                    
                    assert expected_pixels == output_pixels, \
                        f"Block texture at ({x}, {y}) doesn't match expected block {expected_block}"


class TestSaveOutput:
    """Test suite for save_output functionality."""
    
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=1, max_value=2048), st.integers(min_value=1, max_value=2048))
    def test_property_output_format_preservation(self, width, height):
        """
        Property 5: Output Format Preservation
        
        Feature: minecraft-skin-pixelart, Property 5: For any successfully processed skin,
        the saved output file SHALL be in PNG format and SHALL be readable as a valid
        image with dimensions 1024x1024.
        
        Validates: Requirements 5.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Create a test image with random dimensions
            test_image = Image.new('RGBA', (width, height), color=(255, 0, 0, 255))
            
            # Save the image
            output_path = os.path.join(tmpdir, "test_output.png")
            
            try:
                processor.save_output(test_image, output_path)
                
                # Verify the file was created
                assert os.path.exists(output_path), "Output file should be created"
                
                # Verify it can be read as a valid image
                with Image.open(output_path) as saved_image:
                    # Verify it's in PNG format (check format attribute)
                    assert saved_image.format == 'PNG', \
                        f"Output should be PNG format, got {saved_image.format}"
                    
                    # Verify dimensions are preserved
                    assert saved_image.size == (width, height), \
                        f"Output dimensions should be {width}x{height}, got {saved_image.size}"
                    
                    # Verify the image is readable and valid
                    saved_image.load()  # This will raise an exception if image is corrupted
                    
            finally:
                # Clean up
                if os.path.exists(output_path):
                    try:
                        os.unlink(output_path)
                    except (PermissionError, FileNotFoundError):
                        pass

    
    def test_save_to_specified_path(self):
        """
        Test saving output to a specified path (example).
        
        Requirements: 5.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Create a test image
            test_image = Image.new('RGBA', (1024, 1024), color=(0, 255, 0, 255))
            
            # Specify output path
            output_path = os.path.join(tmpdir, "my_custom_output.png")
            
            # Save the image
            processor.save_output(test_image, output_path)
            
            # Verify the file was created at the specified path
            assert os.path.exists(output_path), "Output file should be created at specified path"
            
            # Verify it's a valid PNG
            with Image.open(output_path) as saved_image:
                assert saved_image.format == 'PNG'
                assert saved_image.size == (1024, 1024)
    
    def test_use_default_name(self):
        """
        Test using default name when path not specified (example).
        
        Requirements: 5.3
        """
        # Save current directory
        original_dir = os.getcwd()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Change to temp directory
                os.chdir(tmpdir)
                
                # Create a dummy block for the palette
                dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
                dummy_path = os.path.join(tmpdir, "dummy.png")
                dummy_block.save(dummy_path)
                
                palette = BlockPalette(tmpdir)
                palette.load_blocks()
                matcher = ColorMatcher(palette)
                processor = SkinProcessor(palette, matcher)
                
                # Create a test image
                test_image = Image.new('RGBA', (1024, 1024), color=(0, 0, 255, 255))
                
                # Save without specifying path (should use default)
                processor.save_output(test_image, None)
                
                # Verify default file was created
                default_path = "minecraft_skin_output.png"
                assert os.path.exists(default_path), "Default output file should be created"
                
                # Verify it's a valid PNG
                with Image.open(default_path) as saved_image:
                    assert saved_image.format == 'PNG'
                    assert saved_image.size == (1024, 1024)
                
                # Clean up
                os.unlink(default_path)
            finally:
                # Restore original directory
                os.chdir(original_dir)
    
    def test_handle_existing_files(self):
        """
        Test handling of existing files by adding suffix (example).
        
        Requirements: 5.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy block for the palette
            dummy_block = Image.new('RGB', (16, 16), color=(128, 128, 128))
            dummy_path = os.path.join(tmpdir, "dummy.png")
            dummy_block.save(dummy_path)
            
            palette = BlockPalette(tmpdir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Create test images
            test_image1 = Image.new('RGBA', (1024, 1024), color=(255, 0, 0, 255))
            test_image2 = Image.new('RGBA', (1024, 1024), color=(0, 255, 0, 255))
            test_image3 = Image.new('RGBA', (1024, 1024), color=(0, 0, 255, 255))
            
            # Specify the same output path
            output_path = os.path.join(tmpdir, "output.png")
            
            # Save first image
            processor.save_output(test_image1, output_path)
            assert os.path.exists(output_path), "First file should be created"
            
            # Save second image with same path - should create output_1.png
            processor.save_output(test_image2, output_path)
            output_path_1 = os.path.join(tmpdir, "output_1.png")
            assert os.path.exists(output_path_1), "Second file should be created with _1 suffix"
            
            # Save third image with same path - should create output_2.png
            processor.save_output(test_image3, output_path)
            output_path_2 = os.path.join(tmpdir, "output_2.png")
            assert os.path.exists(output_path_2), "Third file should be created with _2 suffix"
            
            # Verify all three files exist and are different
            assert os.path.exists(output_path)
            assert os.path.exists(output_path_1)
            assert os.path.exists(output_path_2)
            
            # Verify they're all valid PNGs
            for path in [output_path, output_path_1, output_path_2]:
                with Image.open(path) as img:
                    assert img.format == 'PNG'
                    assert img.size == (1024, 1024)
