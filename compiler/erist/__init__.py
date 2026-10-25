"""Bootstrap implementation of the Eristavi toolchain."""

from .collection_support import install_collection_support
from .collection_validation import install_collection_validation

install_collection_support()
install_collection_validation()

from .cli import main

__all__ = ["main"]
