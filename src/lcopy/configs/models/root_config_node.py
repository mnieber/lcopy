from dataclassy import dataclass
import typing as T

# Forward references for type hints
if T.TYPE_CHECKING:
    from lcopy.configs.models.config_node import ConfigNode


@dataclass
class RootConfigNode:
    source_path: str
    label: str
    child_nodes: T.List["ConfigNode"] = []
