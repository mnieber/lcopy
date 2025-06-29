import os
import pathlib


def normalize_path(rel_path: str, base_path: str = "") -> str:
    # Expand environment variables and user home directory
    expanded_rel = os.path.expandvars(os.path.expanduser(rel_path))

    # Join with relative path if provided
    if base_path and not os.path.isabs(expanded_rel):
        expanded_base = os.path.expandvars(os.path.expanduser(base_path))
        path = os.path.join(expanded_base, expanded_rel)
    else:
        path = expanded_rel

    # Convert to absolute path and normalize
    return str(pathlib.Path(path).absolute().resolve())
