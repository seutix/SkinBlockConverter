"""
Integration tests for the complete Minecraft Skin Pixelart pipeline.
"""

import os
import sys
import tempfile
import subprocess
import pytest
from PIL import Image

from minecraft_skin_pixelart.skin_processor import SkinProcessor
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher


class TestFullPipeline:
    """Test the complete conversion pipeline from input to output."""
    
    def test_convert_skin_full_pipeline(self):
        """
        Test the complete pipeline from input file to output file.
        
        Requirements: All
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            test_blocks = [
                ('red', (255, 0, 0)),
                ('green', (0, 255, 0)),
                ('blue', (0, 0, 255)),
                ('white', (255, 255, 255)),
                ('black', (0, 0, 0)),
            ]
            
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            for block_name, color in test_blocks:
                block_img = Image.new('RGB', (16, 16), color=color)
                block_path = os.path.join(blocks_dir, f"{block_name}.png")
                block_img.save(block_path)
            
            # Create a test 64x64 skin with different colored quadrants
            skin = Image.new('RGBA', (64, 64))
            pixels = []
            for y in range(64):
                for x in range(64):
                    if x < 32 and y < 32:
                        # Top-left: red
                        pixels.append((255, 0, 0, 255))
                    elif x >= 32 and y < 32:
                        # Top-right: green
                        pixels.append((0, 255, 0, 255))
                    elif x < 32 and y >= 32:
                        # Bottom-left: blue
                        pixels.append((0, 0, 255, 255))
                    else:
                        # Bottom-right: white
                        pixels.append((255, 255, 255, 255))
            
            skin.putdata(pixels)
            skin_path = os.path.join(tmpdir, 'test_skin.png')
            skin.save(skin_path)
            
            # Initialize components
            palette = BlockPalette(blocks_dir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Run the full conversion
            output_path = os.path.join(tmpdir, 'output.png')
            processor.convert_skin(skin_path, output_path)
            
            # Verify output file was created
            assert os.path.exists(output_path), "Output file should be created"
            
            # Verify output is valid and has correct dimensions
            with Image.open(output_path) as output:
                assert output.size == (1024, 1024), "Output should be 1024x1024"
                assert output.format == 'PNG', "Output should be PNG format"
                
                # Verify the output contains block textures
                # Check a sample pixel from each quadrant
                
                # Top-left should be red block (at position 8*16, 8*16)
                sample_pixel = output.getpixel((8 * 16, 8 * 16))
                assert sample_pixel[:3] == (255, 0, 0), "Top-left should be red"
                
                # Top-right should be green block (at position 40*16, 8*16)
                sample_pixel = output.getpixel((40 * 16, 8 * 16))
                assert sample_pixel[:3] == (0, 255, 0), "Top-right should be green"
                
                # Bottom-left should be blue block (at position 8*16, 40*16)
                sample_pixel = output.getpixel((8 * 16, 40 * 16))
                assert sample_pixel[:3] == (0, 0, 255), "Bottom-left should be blue"
                
                # Bottom-right should be white block (at position 40*16, 40*16)
                sample_pixel = output.getpixel((40 * 16, 40 * 16))
                assert sample_pixel[:3] == (255, 255, 255), "Bottom-right should be white"
    
    def test_convert_skin_with_default_output(self):
        """
        Test conversion using default output path.
        
        Requirements: 5.3
        """
        # Save current directory
        original_dir = os.getcwd()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Change to temp directory
                os.chdir(tmpdir)
                
                # Create a simple block palette
                blocks_dir = os.path.join(tmpdir, 'blocks')
                os.makedirs(blocks_dir)
                
                block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
                block_path = os.path.join(blocks_dir, "gray.png")
                block_img.save(block_path)
                
                # Create a test skin
                skin = Image.new('RGBA', (64, 64), color=(100, 100, 100, 255))
                skin_path = os.path.join(tmpdir, 'test_skin.png')
                skin.save(skin_path)
                
                # Initialize components
                palette = BlockPalette(blocks_dir)
                palette.load_blocks()
                matcher = ColorMatcher(palette)
                processor = SkinProcessor(palette, matcher)
                
                # Run conversion with default output (None)
                processor.convert_skin(skin_path, None)
                
                # Verify default output file was created
                default_output = "minecraft_skin_output.png"
                assert os.path.exists(default_output), "Default output file should be created"
                
                # Verify it's valid
                with Image.open(default_output) as output:
                    assert output.size == (1024, 1024)
                    assert output.format == 'PNG'
                
                # Clean up
                os.unlink(default_output)
                
            finally:
                # Restore original directory
                os.chdir(original_dir)
    
    def test_convert_skin_with_transparent_pixels(self):
        """
        Test conversion with transparent pixels in the skin.
        
        Requirements: 3.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(255, 0, 0))
            block_path = os.path.join(blocks_dir, "red.png")
            block_img.save(block_path)
            
            # Create a skin with some transparent pixels
            skin = Image.new('RGBA', (64, 64))
            pixels = []
            for y in range(64):
                for x in range(64):
                    if x < 32:
                        # Left half: opaque red
                        pixels.append((255, 0, 0, 255))
                    else:
                        # Right half: transparent
                        pixels.append((0, 0, 0, 0))
            
            skin.putdata(pixels)
            skin_path = os.path.join(tmpdir, 'test_skin.png')
            skin.save(skin_path)
            
            # Initialize components
            palette = BlockPalette(blocks_dir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = SkinProcessor(palette, matcher)
            
            # Run conversion
            output_path = os.path.join(tmpdir, 'output.png')
            processor.convert_skin(skin_path, output_path)
            
            # Verify output was created
            assert os.path.exists(output_path)
            
            # Verify transparent pixels were handled (not replaced with blocks)
            with Image.open(output_path) as output:
                assert output.size == (1024, 1024)
                
                # Check that left side has red blocks
                sample_pixel = output.getpixel((8 * 16, 8 * 16))
                assert sample_pixel[:3] == (255, 0, 0), "Left side should have red blocks"
                
                # Check that right side is transparent (alpha = 0)
                sample_pixel = output.getpixel((40 * 16, 8 * 16))
                assert sample_pixel[3] == 0, "Right side should be transparent"


class TestCLI:
    """Test the CLI interface."""
    
    def test_cli_with_input_and_output(self):
        """
        Test CLI with --input and --output parameters.
        
        Requirements: All
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
            block_path = os.path.join(blocks_dir, "gray.png")
            block_img.save(block_path)
            
            # Create a test skin
            skin = Image.new('RGBA', (64, 64), color=(100, 100, 100, 255))
            skin_path = os.path.join(tmpdir, 'test_skin.png')
            skin.save(skin_path)
            
            # Run CLI
            output_path = os.path.join(tmpdir, 'cli_output.png')
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', skin_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI succeeded
            assert result.returncode == 0, f"CLI should succeed. stderr: {result.stderr}"
            
            # Verify output file was created
            assert os.path.exists(output_path), "CLI should create output file"
            
            # Verify output is valid
            with Image.open(output_path) as output:
                assert output.size == (1024, 1024)
                assert output.format == 'PNG'
            
            # Verify success message in output
            assert "Conversion completed successfully" in result.stdout
    
    def test_cli_with_invalid_dimensions(self):
        """
        Test CLI with invalid skin dimensions.
        
        Requirements: 1.2
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
            block_path = os.path.join(blocks_dir, "gray.png")
            block_img.save(block_path)
            
            # Create an invalid skin (wrong dimensions)
            skin = Image.new('RGBA', (32, 32), color=(100, 100, 100, 255))
            skin_path = os.path.join(tmpdir, 'invalid_skin.png')
            skin.save(skin_path)
            
            # Run CLI
            output_path = os.path.join(tmpdir, 'output.png')
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', skin_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI failed with appropriate error
            assert result.returncode == 1, "CLI should fail with invalid dimensions"
            assert "Invalid skin dimensions" in result.stdout or "32x32" in result.stdout
            assert "64x64" in result.stdout
    
    def test_cli_with_missing_input(self):
        """
        Test CLI with missing input file.
        
        Requirements: 1.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
            block_path = os.path.join(blocks_dir, "gray.png")
            block_img.save(block_path)
            
            # Use a nonexistent input file
            skin_path = os.path.join(tmpdir, 'nonexistent.png')
            output_path = os.path.join(tmpdir, 'output.png')
            
            # Run CLI
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', skin_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI failed
            assert result.returncode == 1, "CLI should fail with missing input"
            assert "not found" in result.stdout.lower()
    
    def test_cli_with_missing_blocks_directory(self):
        """
        Test CLI with missing blocks directory.
        
        Requirements: 2.3
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test skin
            skin = Image.new('RGBA', (64, 64), color=(100, 100, 100, 255))
            skin_path = os.path.join(tmpdir, 'test_skin.png')
            skin.save(skin_path)
            
            # Use a nonexistent blocks directory
            blocks_dir = os.path.join(tmpdir, 'nonexistent_blocks')
            output_path = os.path.join(tmpdir, 'output.png')
            
            # Run CLI
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', skin_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI failed
            assert result.returncode == 1, "CLI should fail with missing blocks directory"
            assert "not found" in result.stdout.lower()
    
    def test_cli_help_message(self):
        """
        Test CLI help message.
        """
        result = subprocess.run(
            [sys.executable, '-m', 'minecraft_skin_pixelart', '--help'],
            capture_output=True,
            text=True
        )
        
        # Verify help is displayed
        assert result.returncode == 0, "Help should succeed"
        assert "--input" in result.stdout
        assert "--output" in result.stdout
        assert "--blocks-dir" in result.stdout
        assert "Convert Minecraft skins" in result.stdout


class TestCapePipeline:
    """Test the complete conversion pipeline for capes."""
    
    def test_convert_cape_full_pipeline(self):
        """
        Test the complete pipeline from input cape file to output file.
        """
        from minecraft_skin_pixelart.cape_processor import CapeProcessor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            test_blocks = [
                ('red', (255, 0, 0)),
                ('green', (0, 255, 0)),
                ('blue', (0, 0, 255)),
                ('white', (255, 255, 255)),
            ]
            
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            for block_name, color in test_blocks:
                block_img = Image.new('RGB', (16, 16), color=color)
                block_path = os.path.join(blocks_dir, f"{block_name}.png")
                block_img.save(block_path)
            
            # Create a test 64x32 cape with different colored quadrants
            cape = Image.new('RGBA', (64, 32))
            pixels = []
            for y in range(32):
                for x in range(64):
                    if x < 32 and y < 16:
                        # Top-left: red
                        pixels.append((255, 0, 0, 255))
                    elif x >= 32 and y < 16:
                        # Top-right: green
                        pixels.append((0, 255, 0, 255))
                    elif x < 32 and y >= 16:
                        # Bottom-left: blue
                        pixels.append((0, 0, 255, 255))
                    else:
                        # Bottom-right: white
                        pixels.append((255, 255, 255, 255))
            
            cape.putdata(pixels)
            cape_path = os.path.join(tmpdir, 'test_cape.png')
            cape.save(cape_path)
            
            # Initialize components
            palette = BlockPalette(blocks_dir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = CapeProcessor(palette, matcher)
            
            # Run the full conversion
            output_path = os.path.join(tmpdir, 'output.png')
            processor.convert_cape(cape_path, output_path)
            
            # Verify output file was created
            assert os.path.exists(output_path), "Output file should be created"
            
            # Verify output is valid and has correct dimensions
            with Image.open(output_path) as output:
                assert output.size == (1024, 512), "Output should be 1024x512"
                assert output.format == 'PNG', "Output should be PNG format"
                
                # Verify the output contains block textures
                # Check a sample pixel from each quadrant
                
                # Top-left should be red block (at position 8*16, 4*16)
                sample_pixel = output.getpixel((8 * 16, 4 * 16))
                assert sample_pixel[:3] == (255, 0, 0), "Top-left should be red"
                
                # Top-right should be green block (at position 40*16, 4*16)
                sample_pixel = output.getpixel((40 * 16, 4 * 16))
                assert sample_pixel[:3] == (0, 255, 0), "Top-right should be green"
                
                # Bottom-left should be blue block (at position 8*16, 20*16)
                sample_pixel = output.getpixel((8 * 16, 20 * 16))
                assert sample_pixel[:3] == (0, 0, 255), "Bottom-left should be blue"
                
                # Bottom-right should be white block (at position 40*16, 20*16)
                sample_pixel = output.getpixel((40 * 16, 20 * 16))
                assert sample_pixel[:3] == (255, 255, 255), "Bottom-right should be white"
    
    def test_convert_cape_with_transparency(self):
        """
        Test conversion with transparent pixels in the cape.
        """
        from minecraft_skin_pixelart.cape_processor import CapeProcessor
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(255, 0, 0))
            block_path = os.path.join(blocks_dir, "red.png")
            block_img.save(block_path)
            
            # Create a cape with some transparent pixels
            cape = Image.new('RGBA', (64, 32))
            pixels = []
            for y in range(32):
                for x in range(64):
                    if x < 32:
                        # Left half: opaque red
                        pixels.append((255, 0, 0, 255))
                    else:
                        # Right half: transparent
                        pixels.append((0, 0, 0, 0))
            
            cape.putdata(pixels)
            cape_path = os.path.join(tmpdir, 'test_cape.png')
            cape.save(cape_path)
            
            # Initialize components
            palette = BlockPalette(blocks_dir)
            palette.load_blocks()
            matcher = ColorMatcher(palette)
            processor = CapeProcessor(palette, matcher)
            
            # Run conversion
            output_path = os.path.join(tmpdir, 'output.png')
            processor.convert_cape(cape_path, output_path)
            
            # Verify output was created
            assert os.path.exists(output_path)
            
            # Verify transparent pixels were handled
            with Image.open(output_path) as output:
                assert output.size == (1024, 512)
                
                # Check that left side has red blocks
                sample_pixel = output.getpixel((8 * 16, 8 * 16))
                assert sample_pixel[:3] == (255, 0, 0), "Left side should have red blocks"
                
                # Check that right side is transparent (alpha = 0)
                sample_pixel = output.getpixel((40 * 16, 8 * 16))
                assert sample_pixel[3] == 0, "Right side should be transparent"


class TestCapeCLI:
    """Test the CLI interface for capes."""
    
    def test_cli_cape_with_input_and_output(self):
        """
        Test CLI with --cape flag.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
            block_path = os.path.join(blocks_dir, "gray.png")
            block_img.save(block_path)
            
            # Create a test cape
            cape = Image.new('RGBA', (64, 32), color=(100, 100, 100, 255))
            cape_path = os.path.join(tmpdir, 'test_cape.png')
            cape.save(cape_path)
            
            # Run CLI with --cape flag
            output_path = os.path.join(tmpdir, 'cli_output.png')
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', cape_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir,
                    '--cape'
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI succeeded
            assert result.returncode == 0, f"CLI should succeed. stderr: {result.stderr}"
            
            # Verify output file was created
            assert os.path.exists(output_path), "CLI should create output file"
            
            # Verify output is valid
            with Image.open(output_path) as output:
                assert output.size == (1024, 512), "Cape output should be 1024x512"
                assert output.format == 'PNG'
            
            # Verify success message in output
            assert "Conversion completed successfully" in result.stdout
    
    def test_cli_cape_with_invalid_dimensions(self):
        """
        Test CLI with invalid cape dimensions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple block palette
            blocks_dir = os.path.join(tmpdir, 'blocks')
            os.makedirs(blocks_dir)
            
            block_img = Image.new('RGB', (16, 16), color=(128, 128, 128))
            block_path = os.path.join(blocks_dir, "gray.png")
            block_img.save(block_path)
            
            # Create an invalid cape (wrong dimensions)
            cape = Image.new('RGBA', (32, 32), color=(100, 100, 100, 255))
            cape_path = os.path.join(tmpdir, 'invalid_cape.png')
            cape.save(cape_path)
            
            # Run CLI with --cape flag
            output_path = os.path.join(tmpdir, 'output.png')
            result = subprocess.run(
                [
                    sys.executable, '-m', 'minecraft_skin_pixelart',
                    '--input', cape_path,
                    '--output', output_path,
                    '--blocks-dir', blocks_dir,
                    '--cape'
                ],
                capture_output=True,
                text=True
            )
            
            # Verify CLI failed with appropriate error
            assert result.returncode == 1, "CLI should fail with invalid dimensions"
            assert "Invalid cape dimensions" in result.stdout or "32x32" in result.stdout
            assert "64x32" in result.stdout
    
    def test_cli_help_includes_cape_option(self):
        """
        Test that CLI help message includes cape option.
        """
        result = subprocess.run(
            [sys.executable, '-m', 'minecraft_skin_pixelart', '--help'],
            capture_output=True,
            text=True
        )
        
        # Verify help includes cape option
        assert result.returncode == 0, "Help should succeed"
        assert "--cape" in result.stdout or "-c" in result.stdout
        assert "64x32" in result.stdout
