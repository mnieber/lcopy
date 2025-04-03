from dataclassy import dataclass
import typing as T


@dataclass
class FilemapNode:
    """
    Node in the file mapping tree representing files to be copied.

    Each FilemapNode specifies a source path, target path, and a list of filenames
    to be copied from the source to the target.
    """

    target_path: str  # Destination path where files will be copied to
    source_path: str  # Source path where files will be copied from
    filenames: T.List[str]  # List of filenames relative to the source_path to be copied
    child_nodes: T.List["FilemapNode"] = []
