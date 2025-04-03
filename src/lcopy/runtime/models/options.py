from dataclassy import dataclass
import typing as T
from typing import List


@dataclass
class Options:
    """
    Options for the lcopy tool.

    This model represents the parsed options from the options.yaml file.
    """

    configs: List[str]  # List of config file paths
    destination: str  # Destination directory for copied files
    labels: List[str]  # Labels to include (filtering which sections of config to use)
    conflict: str  # Conflict resolution strategy (overwrite, skip, prompt)
    verbose: bool  # Enable verbose output
    purge: bool  # Purge files in destination that weren't copied
    dry_run: bool  # Enable dry run mode (no actual copying)
