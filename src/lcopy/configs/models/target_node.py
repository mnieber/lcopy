import typing as T

from dataclassy import dataclass


@dataclass
class TargetNode:
    source_dirname: str
    relative_target_dir: str
    filenames: T.List[str]
    child_nodes: T.List["TargetNode"] = []
