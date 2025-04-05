from dataclassy import dataclass
import typing as T


@dataclass
class Options:
    # List of config file paths
    configs: T.List[str]
    # Destination directory for copied files
    destination: str
    # Labels to include (filtering which sections of config to use)
    labels: T.List[str]
    # Conflict resolution strategy (overwrite, skip, prompt)
    conflict: str
    # Enable verbose output
    verbose: bool
    # Purge files in destination that weren't copied
    purge: bool
    # Enable dry run mode (no actual copying)
    dry_run: bool
