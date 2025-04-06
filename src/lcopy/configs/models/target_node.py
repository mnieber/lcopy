from dataclassy import dataclass
import typing as T


@dataclass
class TargetNode:
    source_dirname: str
    target_basename: str
    filename_patterns: T.List[str]
    child_nodes: T.List["TargetNode"] = []
    labels: T.List[str] = []
