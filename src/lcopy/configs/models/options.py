import typing as T

from dataclassy import dataclass


@dataclass
class Options:
    destination: str = ""
    conflict: str = "skip"
    verbose: bool = False
    purge: bool = False
    dry_run: bool = False
    default_ignore: bool = True
    extra_ignore: T.List[str] = []
    concatenated_output_filename: T.Optional[str] = None
