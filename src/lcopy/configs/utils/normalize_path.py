import os
import logging

logger = logging.getLogger(__name__)


def normalize_path(path: str, base_path: str = None) -> str:
    # Expand environment variables and ~ for home directory
    path = os.path.expanduser(os.path.expandvars(path))

    # If the path is not absolute and a base path is provided, join with base path
    if base_path is not None and not os.path.isabs(path):
        path = os.path.join(base_path, path)

    # Normalize the path (resolves '..' and '.' components)
    path = os.path.normpath(path)

    logger.debug(f"Normalized path: {path}")
    return path
