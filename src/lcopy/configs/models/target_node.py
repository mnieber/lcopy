import typing as T

from dataclassy import dataclass


@dataclass
class TargetNode:
    source_dirname: str
    target_basename: str
    filename_patterns: T.List[str]
    child_nodes: T.List["TargetNode"] = []
    labels: T.List[str] = []
    includes: T.List[str] = []  # List of references like "source_alias.label"
