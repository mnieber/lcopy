from dataclassy import dataclass


@dataclass
class SourceConfig:
    path: str  # Absolute path to the source directory
    alias: str  # Name used to reference this source directory
