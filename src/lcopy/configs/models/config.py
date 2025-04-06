from dataclassy import dataclass
import typing as T

if T.TYPE_CHECKING:
    from lcopy.configs.models.target_node import TargetNode


@dataclass
class Config:
    source_dirname: str
    target_nodes: T.List["TargetNode"] = []
    include_fns: T.List[str] = []
