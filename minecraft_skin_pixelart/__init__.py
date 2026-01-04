"""
Minecraft Skin Pixelart Converter

A tool to convert Minecraft skins (64x64) into pixelart using block textures (1024x1024).
Also supports Minecraft capes (64x32) conversion to pixelart (1024x512).
"""

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

__version__ = "0.1.0"

__all__ = [
    'BlockPalette',
    'ColorMatcher',
    'SkinProcessor',
    'CapeProcessor',
    'MinecraftSkinPixelartError',
    'InvalidImageError',
    'InvalidDimensionsError',
    'BlockDirectoryNotFoundError',
    'BlockPaletteEmptyError',
    'ProcessingError',
    'OutputSaveError',
]
