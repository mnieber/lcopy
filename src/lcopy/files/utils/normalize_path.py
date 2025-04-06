import os
import pathlib


def normalize_path(rel_path: str, base_path: str = "") -> str:
    # Expand environment variables and user home directory
    expanded_base = os.path.expandvars(os.path.expanduser(base_path))
    expanded_rel = os.path.expandvars(os.path.expanduser(rel_path))

    # Join with relative path if provided
    if rel_path:
        path = os.path.join(expanded_base, expanded_rel)
    else:
        path = expanded_base

    # Convert to absolute path and normalize
    return str(pathlib.Path(path).absolute().resolve())
