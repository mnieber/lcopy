from dataclassy import dataclass
import typing as T


@dataclass
class Options:
    configs: T.List[str]
    destination: str
    labels: T.List[str]
    conflict: str
    verbose: bool
    purge: bool
    dry_run: bool
    default_ignore: bool
    extra_ignore: T.List[str]

    def get_ignore_patterns(self) -> T.List[str]:
        """
        Get the list of ignore patterns to apply when copying files.
        Combines default ignore patterns with any extra ignore patterns.
        """
        ignore_patterns = []

        # Add default ignore patterns if enabled
        if self.default_ignore:
            ignore_patterns.extend(
                [
                    "*.pyc",
                    "__pycache__",
                    ".git",
                    ".gitignore",
                    ".DS_Store",
                    "*.swp",
                    "*.swo",
                    "*.bak",
                    "*.tmp",
                ]
            )

        # Add any extra ignore patterns
        if self.extra_ignore:
            ignore_patterns.extend(self.extra_ignore)

        return ignore_patterns
