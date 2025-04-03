import os
from typing import List

from lcopy.filemaps.models.filemap_node import FilemapNode


def create_filemap_node(
    source_path: str, target_path: str, filenames: List[str]
) -> FilemapNode:
    # Normalize paths to ensure consistent format
    source_path = os.path.normpath(source_path)
    target_path = os.path.normpath(target_path)

    # Filter out any invalid filenames (empty strings, etc.)
    valid_filenames = [f for f in filenames if f and isinstance(f, str)]

    # Create and return the FilemapNode
    return FilemapNode(
        source_path=source_path, target_path=target_path, filenames=valid_filenames
    )
