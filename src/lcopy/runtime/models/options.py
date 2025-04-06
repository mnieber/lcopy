from dataclassy import dataclass
import typing as T


@dataclass
class Options:
    config_fns: T.List[str]
    destination: str
    labels: T.List[str]
    conflict: str
    verbose: bool
    purge: bool
    dry_run: bool
    default_ignore: bool
    extra_ignore: T.List[str]
