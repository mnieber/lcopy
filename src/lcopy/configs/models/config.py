import typing as T

from dataclassy import dataclass

if T.TYPE_CHECKING:
    from lcopy.configs.models.options import Options


@dataclass
class Config:
    source_dirname: str
    targets_json: dict
    sources: T.Dict[str, str] = {}
    options: T.Optional["Options"] = None
