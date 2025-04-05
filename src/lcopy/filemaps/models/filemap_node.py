from dataclassy import dataclass
import typing as T


@dataclass
class FilemapNode:
    target_path: str
    # Source files are read from this path
    source_path: str
    # List of filenames relative to the source_path
    filenames: T.List[str] = []
    child_nodes: T.List["FilemapNode"] = []
