"""
CLI interface for Minecraft Skin Pixelart converter.
"""

import argparse
import sys
import os

# Set UTF-8 encoding for stdout/stderr on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from .block_palette import BlockPalette
from .color_matcher import ColorMatcher
from .skin_processor import SkinProcessor
from .cape_processor import CapeProcessor
from .exceptions import (
    MinecraftSkinPixelartError,
    InvalidImageError,
    InvalidDimensionsError,
    BlockDirectoryNotFoundError,
    BlockPaletteEmptyError,
    ProcessingError,
    OutputSaveError
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Minecraft skins and capes to pixelart using block textures.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert skin (64x64)
  %(prog)s --input my_skin.png --output result.png
  %(prog)s -i skin.png -o output.png
  
  # Convert cape (64x32)
  %(prog)s --input my_cape.png --output result.png --cape
  %(prog)s -i cape.png -o output.png -c
  
  # Use default output name
  %(prog)s --input skin.png
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input file (skin: 64x64 pixels, cape: 64x32 pixels)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Path to output file (default: minecraft_skin_output.png or minecraft_cape_output.png)'
    )
    
    parser.add_argument(
        '--blocks-dir', '-b',
        default='block',
        help='Path to directory containing block textures (default: block)'
    )
    
    parser.add_argument(
        '--cape', '-c',
        action='store_true',
        help='Process as cape (64x32) instead of skin (64x64)'
    )
    
    args = parser.parse_args()
    
    try:
        # Print startup message
        print("Minecraft Skin/Cape Pixelart Converter")
        print("=" * 40)
        
        # Step 1: Load block palette
        print(f"\n[1/4] Loading block textures from '{args.blocks_dir}'...")
        
        if not os.path.exists(args.blocks_dir):
            print(f"Error: Blocks directory not found: {args.blocks_dir}")
            sys.exit(1)
        
        palette = BlockPalette(args.blocks_dir)
        palette.load_blocks()
        
        block_count = len(palette.blocks)
        print(f"      ✓ Loaded {block_count} block textures")
        
        # Step 2: Initialize color matcher
        print("\n[2/4] Initializing color matcher...")
        matcher = ColorMatcher(palette)
        print("      ✓ Color matcher ready")
        
        # Step 3: Initialize processor
        if args.cape:
            print("\n[3/4] Processing cape...")
            processor = CapeProcessor(palette, matcher)
            item_type = "cape"
            default_output = "minecraft_cape_output.png"
        else:
            print("\n[3/4] Processing skin...")
            processor = SkinProcessor(palette, matcher)
            item_type = "skin"
            default_output = "minecraft_skin_output.png"
        
        # Verify input file exists
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        
        print(f"      • Loading {item_type} from '{args.input}'...")
        
        # Step 4: Convert the skin/cape
        output_path = args.output if args.output else default_output
        if args.cape:
            processor.convert_cape(args.input, args.output)
        else:
            processor.convert_skin(args.input, args.output)
        
        # Determine actual output path (might have suffix if file existed)
        if args.output is None:
            # Check if default name was used or modified
            if os.path.exists(default_output):
                actual_output = default_output
            else:
                # Find the file with suffix
                counter = 1
                base, ext = os.path.splitext(default_output)
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                actual_output = f"{base}_{counter - 1}{ext}"
        else:
            # Check if specified path was used or modified
            if os.path.exists(args.output):
                actual_output = args.output
            else:
                # Find the file with suffix
                base, ext = os.path.splitext(args.output)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                actual_output = f"{base}_{counter - 1}{ext}"
        
        print(f"      ✓ {item_type.capitalize()} processed successfully")
        
        # Step 5: Success message
        print(f"\n[4/4] Saving output...")
        print(f"      ✓ Output saved to '{actual_output}'")
        
        print("\n" + "=" * 40)
        print("✓ Conversion completed successfully!")
        
        return 0
        
    except InvalidDimensionsError as e:
        print(f"\n✗ Error: {e}")
        if args.cape:
            print("  The input cape must be exactly 64x32 pixels.")
        else:
            print("  The input skin must be exactly 64x64 pixels.")
        return 1
        
    except InvalidImageError as e:
        print(f"\n✗ Error: {e}")
        print("  Please provide a valid image file.")
        return 1
        
    except BlockDirectoryNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Please ensure the blocks directory exists and contains block textures.")
        return 1
        
    except BlockPaletteEmptyError as e:
        print(f"\n✗ Error: {e}")
        print("  The blocks directory must contain at least one valid PNG texture.")
        return 1
        
    except OutputSaveError as e:
        print(f"\n✗ Error: {e}")
        print("  Please check file permissions and disk space.")
        return 1
        
    except ProcessingError as e:
        print(f"\n✗ Error: {e}")
        return 1
        
    except MinecraftSkinPixelartError as e:
        print(f"\n✗ Error: {e}")
        return 1
        
    except KeyboardInterrupt:
        print("\n\n✗ Conversion cancelled by user.")
        return 130
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
