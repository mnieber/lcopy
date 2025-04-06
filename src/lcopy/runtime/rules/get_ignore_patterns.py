import logging
import typing as T

logger = logging.getLogger(__name__)


def get_ignore_patterns(default_ignore: bool, extra_ignore: T.List[str]) -> T.List[str]:
    ignore_patterns = list(extra_ignore) if extra_ignore else []

    # Add default ignore patterns if enabled
    if default_ignore:
        default_patterns = [
            "*.pyc",
            "__pycache__",
            ".DS_Store",
            ".git",
            ".gitignore",
            ".svn",
            ".hg",
            ".idea",
            "*.swp",
            "*.bak",
            "*.tmp",
            "*.log",
        ]
        ignore_patterns.extend(default_patterns)

    logger.info(f"Using {len(ignore_patterns)} ignore patterns")
    if logger.isEnabledFor(logging.DEBUG):
        for pattern in ignore_patterns:
            logger.debug(f"Ignore pattern: {pattern}")

    return ignore_patterns
