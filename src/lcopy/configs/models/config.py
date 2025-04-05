from dataclassy import dataclass
import typing as T

# Forward references for type hints
if T.TYPE_CHECKING:
    from lcopy.configs.models.root_config_node import RootConfigNode


@dataclass
class Config:
    # List of other lcopy configs to include
    source_path: str
    include: T.List[str] = []
    root_config_nodes: T.List["RootConfigNode"] = []
