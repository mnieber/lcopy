import glob
import logging
import os
import typing as T

from lcopy.configs.models.target_node import TargetNode
from lcopy.files.rules.get_filtered_files import get_filtered_files
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def create_target_node(
    relative_target_dir: str,
    target_node_json: dict,
    ignore_patterns: T.List[str],
) -> TargetNode:
    # Get source directory from __source_dir__ directive
    source_dirname = target_node_json.get("__source_dir__", "")
    assert source_dirname

    # Handle __cd__ directive if present
    if "__cd__" in target_node_json:
        cd_path = target_node_json["__cd__"]
        source_dirname = normalize_path(cd_path, base_path=source_dirname)

    # Create target node instance
    target_node = TargetNode(
        source_dirname=source_dirname,
        relative_target_dir=relative_target_dir,
        filenames=[],
        child_nodes=[],
        includes=[],
    )

    # Collect include and exclude patterns
    include_patterns = []
    exclude_patterns = []

    # Process each entry in the target_node_json
    for key, value in target_node_json.items():
        # Skip special directives
        if key.startswith("__"):
            continue

        # If value is True, add to include patterns, else add to exclude patterns
        if isinstance(value, bool):
            if value:
                include_patterns.append(key)
            else:
                exclude_patterns.append(key)
        elif isinstance(value, dict):
            # This is a child node - create it with the key as relative_target_dir
            child_node_json = dict(value)
            target_node.child_nodes.append(
                create_target_node(
                    relative_target_dir=key,
                    target_node_json=child_node_json,
                    ignore_patterns=ignore_patterns,
                )
            )

    # Process each include
    for included_target_node_json in target_node_json.get("__include__", []):
        target_node.child_nodes.append(
            create_target_node(
                relative_target_dir=".",
                target_node_json=included_target_node_json,
                ignore_patterns=ignore_patterns,
            )
        )

    # Resolve patterns to concrete file paths
    all_files = _expand_patterns(include_patterns, source_dirname)

    # Apply exclude patterns and ignore patterns
    if all_files:
        filtered_files = get_filtered_files(
            files=all_files,
            source_dirname=source_dirname,
            ignore_patterns=ignore_patterns or [],
            exclude_patterns=exclude_patterns,
        )

        # Extract directories to be processed separately
        directories = [f for f in filtered_files if os.path.isdir(f)]
        files = [f for f in filtered_files if not os.path.isdir(f)]

        # Store concrete file paths in the target node
        target_node.filenames = files

        # Handle directories by creating additional nodes to process
        if directories:
            child_nodes = _handle_directories(directories, ignore_patterns)
            target_node.child_nodes.extend(child_nodes)

    logger.debug(
        f"Created target node with {len(target_node.filenames)} files and {len(target_node.child_nodes)} child nodes"
    )
    return target_node


def _expand_patterns(patterns: T.List[str], source_dirname: str) -> T.List[str]:
    """Expand all patterns to concrete file paths."""
    all_files = []
    for pattern in patterns:
        # Join source directory with pattern
        full_pattern = normalize_path(pattern, base_path=source_dirname)
        # Expand glob pattern
        matching_files = [f for f in glob.glob(full_pattern, recursive=True)]
        all_files.extend(matching_files)
    return all_files


def _handle_directories(
    directories: T.List[str],
    ignore_patterns: T.List[str],
) -> T.List[TargetNode]:
    """
    Process directories by creating appropriate JSON structures
    and parsing them recursively through the main create_target_node function.
    """
    child_nodes = []

    for directory in directories:
        dir_basename = os.path.basename(directory)

        # Create a simple JSON structure with "*" pattern to include all files
        target_node_json = {"__source_dir__": directory, "*": True}

        # Process this directory through create_target_node
        child_nodes.append(
            create_target_node(
                relative_target_dir=dir_basename,
                target_node_json=target_node_json,
                ignore_patterns=ignore_patterns,
            )
        )

        logger.debug(f"Created directory child node: {dir_basename}")

    return child_nodes
