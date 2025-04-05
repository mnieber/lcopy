from dataclassy import dataclass
import typing as T


@dataclass
class ConfigNode:
    dirname_pattern: str
    filename_patterns: T.List[str]
    child_nodes: T.List["ConfigNode"] = []
