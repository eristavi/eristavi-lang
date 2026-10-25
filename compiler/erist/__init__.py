"""Bootstrap implementation of the Eristavi toolchain."""

from .collection_support import install_collection_support

install_collection_support()

from .cli import main

__all__ = ["main"]
