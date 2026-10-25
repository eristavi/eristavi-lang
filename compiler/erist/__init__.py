"""Bootstrap implementation of the Eristavi toolchain."""

from .collection_support import install_collection_support
from .collection_validation import install_collection_validation

install_collection_support()
install_collection_validation()

from .cli import main
from .ir_collections import Lowerer as _CollectionLowerer
from . import cli as _cli
from . import direct_project as _direct_project

# The CLI/direct-project modules are imported before this compatibility hook so
# their ordinary bootstrap dependency graph stays unchanged. Their functions
# resolve these module globals at execution time, letting the collection-aware
# typed-IR layer extend both paths without duplicating the CLI implementation.
_cli.Lowerer = _CollectionLowerer
_direct_project.Lowerer = _CollectionLowerer

__all__ = ["main"]
