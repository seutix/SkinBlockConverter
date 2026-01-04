"""
Tests for CapeProcessor class.
"""

import pytest
from PIL import Image
from minecraft_skin_pixelart.cape_processor import CapeProcessor
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher
from minecraft_skin_pixelart.exceptions import (
    InvalidDimensionsError,
    InvalidImageError,
    OutputSaveError
)


@pytest.fixture
def block_palette():
    """Create a BlockPalette with test blocks."""
    palette = BlockPalette("block")
    palette.load_blocks()
    return palette


@pytest.fixture
def color_matcher(block_palette):
    """Create a ColorMatcher with test palette."""
    return ColorMatcher(block_palette)


@pytest.fixture
def cape_processor(block_palette, color_matcher):
    """Create a CapeProcessor instance."""
    return CapeProcessor(block_palette, color_matcher)


@pytest.fixture
def valid_cape():
    """Create a valid 64x32 cape image."""
    cape = Image.new('RGBA', (64, 32), (255, 0, 0, 255))
    return cape


@pytest.fixture
def invalid_cape():
    """Create an invalid 32x32 cape image."""
    cape = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
    return cape


class TestCapeProcessorInit:
    """Tests for CapeProcessor initialization."""
    
    def test_init_with_valid_components(self, block_palette, color_matcher):
        """Test initialization with valid components."""
        processor = CapeProcessor(block_palette, color_matcher)
        assert processor.block_palette == block_palette
        assert processor.color_matcher == color_matcher


class TestLoadCape:
    """Tests for load_cape method."""
    
    def test_load_valid_cape(self, cape_processor, tmp_path):
        """Test loading a valid 64x32 cape."""
        cape_path = tmp_path / "test_cape.png"
        cape = Image.new('RGBA', (64, 32), (255, 0, 0, 255))
        cape.save(cape_path)
        
        loaded_cape = cape_processor.load_cape(str(cape_path))
        assert loaded_cape.size == (64, 32)
        assert loaded_cape.mode == 'RGBA'
    
    def test_load_invalid_dimensions(self, cape_processor, tmp_path):
        """Test loading cape with invalid dimensions."""
        cape_path = tmp_path / "invalid_cape.png"
        cape = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
        cape.save(cape_path)
        
        with pytest.raises(InvalidDimensionsError) as exc_info:
            cape_processor.load_cape(str(cape_path))
        assert "32x32" in str(exc_info.value)
        assert "64x32" in str(exc_info.value)
    
    def test_load_nonexistent_file(self, cape_processor):
        """Test loading a nonexistent file."""
        with pytest.raises(InvalidImageError):
            cape_processor.load_cape("nonexistent.png")


class TestProcessCape:
    """Tests for process_cape method."""
    
    def test_process_valid_cape(self, cape_processor, valid_cape):
        """Test processing a valid cape."""
        output = cape_processor.process_cape(valid_cape)
        assert output.size == (1024, 512)
        assert output.mode == 'RGBA'
    
    def test_process_cape_with_transparency(self, cape_processor):
        """Test processing cape with transparent pixels."""
        cape = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
        # Add some opaque pixels
        for x in range(10):
            for y in range(10):
                cape.putpixel((x, y), (255, 0, 0, 255))
        
        output = cape_processor.process_cape(cape)
        assert output.size == (1024, 512)
    
    def test_process_cape_multiple_colors(self, cape_processor):
        """Test processing cape with multiple colors."""
        cape = Image.new('RGBA', (64, 32), (255, 0, 0, 255))
        # Add different colored regions
        for x in range(20, 40):
            for y in range(10, 20):
                cape.putpixel((x, y), (0, 255, 0, 255))
        
        output = cape_processor.process_cape(cape)
        assert output.size == (1024, 512)


class TestSaveOutput:
    """Tests for save_output method."""
    
    def test_save_output_default_name(self, cape_processor, tmp_path, monkeypatch):
        """Test saving output with default name."""
        monkeypatch.chdir(tmp_path)
        
        output = Image.new('RGBA', (1024, 512), (255, 0, 0, 255))
        cape_processor.save_output(output)
        
        assert (tmp_path / "minecraft_cape_output.png").exists()
    
    def test_save_output_custom_name(self, cape_processor, tmp_path):
        """Test saving output with custom name."""
        output_path = tmp_path / "custom_cape.png"
        output = Image.new('RGBA', (1024, 512), (255, 0, 0, 255))
        
        cape_processor.save_output(output, str(output_path))
        assert output_path.exists()
    
    def test_save_output_file_exists(self, cape_processor, tmp_path):
        """Test saving output when file already exists."""
        output_path = tmp_path / "existing_cape.png"
        output = Image.new('RGBA', (1024, 512), (255, 0, 0, 255))
        
        # Create existing file
        output.save(output_path)
        
        # Save again - should create _1 suffix
        cape_processor.save_output(output, str(output_path))
        assert (tmp_path / "existing_cape_1.png").exists()


class TestConvertCape:
    """Tests for convert_cape method."""
    
    def test_convert_cape_success(self, cape_processor, tmp_path):
        """Test complete cape conversion."""
        input_path = tmp_path / "input_cape.png"
        output_path = tmp_path / "output_cape.png"
        
        # Create input cape
        cape = Image.new('RGBA', (64, 32), (255, 0, 0, 255))
        cape.save(input_path)
        
        # Convert
        cape_processor.convert_cape(str(input_path), str(output_path))
        
        # Verify output
        assert output_path.exists()
        output = Image.open(output_path)
        assert output.size == (1024, 512)
    
    def test_convert_cape_invalid_dimensions(self, cape_processor, tmp_path):
        """Test conversion with invalid dimensions."""
        input_path = tmp_path / "invalid_cape.png"
        
        # Create invalid cape
        cape = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
        cape.save(input_path)
        
        with pytest.raises(InvalidDimensionsError):
            cape_processor.convert_cape(str(input_path))
