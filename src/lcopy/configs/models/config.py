import typing as T

from dataclassy import dataclass

if T.TYPE_CHECKING:
    from lcopy.configs.models.options import Options
    from lcopy.configs.models.source_config import SourceConfig
    from lcopy.configs.models.target_node import TargetNode


@dataclass
class Config:
    source_dirname: str
    source_basename: str
    target_nodes: T.List["TargetNode"] = []
    sources: T.Dict[str, "SourceConfig"] = {}
    options: T.Optional["Options"] = None

    @property
    def source_filename(self) -> str:
        return f"{self.source_dirname}/{self.source_basename}"
