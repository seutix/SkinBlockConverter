"""
Custom exceptions for the Minecraft Skin Pixelart converter.
"""


class MinecraftSkinPixelartError(Exception):
    """Base exception for all minecraft skin pixelart errors."""
    pass


class InvalidDimensionsError(MinecraftSkinPixelartError):
    """Raised when input image has invalid dimensions."""
    pass


class InvalidImageError(MinecraftSkinPixelartError):
    """Raised when file cannot be read as an image."""
    pass


class BlockPaletteEmptyError(MinecraftSkinPixelartError):
    """Raised when no valid block textures are found."""
    pass


class BlockDirectoryNotFoundError(MinecraftSkinPixelartError):
    """Raised when blocks directory doesn't exist."""
    pass


class ProcessingError(MinecraftSkinPixelartError):
    """Raised when unexpected error occurs during processing."""
    pass


class OutputSaveError(MinecraftSkinPixelartError):
    """Raised when output cannot be saved."""
    pass
