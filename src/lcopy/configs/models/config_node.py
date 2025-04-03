from dataclassy import dataclass
import typing as T


@dataclass
class ConfigNode:
    """
    Node in the configuration tree representing a mapping directive.

    Each ConfigNode specifies a pattern for matching directories and files
    within those directories, along with potential nested configuration nodes.
    """

    dirname_pattern: str
    filename_patterns: T.List[str]
    child_nodes: T.List["ConfigNode"] = []
