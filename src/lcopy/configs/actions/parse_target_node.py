import logging
import os
import glob
import re
import typing as T
from lcopy.configs.models.target_node import TargetNode
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_target_node(
    target_basename, source_dirname: str, target_node_json: dict
) -> T.List[TargetNode]:
    # Extract target node information
    filename_patterns = target_node_json.get(".", [])
    if isinstance(filename_patterns, str):
        filename_patterns = [filename_patterns]

    # Check if target_basename is a regex pattern (enclosed in parentheses)
    if target_basename.startswith("(") and target_basename.endswith(")"):
        return _handle_regex_pattern(source_dirname, target_basename, target_node_json)

    # Create target node instance
    target_node = TargetNode(
        source_dirname=source_dirname,
        target_basename=target_basename,
        filename_patterns=filename_patterns,
        child_nodes=[],
    )

    # Process child nodes
    for target_basename, child_data in target_node_json.items():
        # Skip special keys
        if target_basename in [".", "__source__"]:
            continue

        # Skip if child_data is not a dictionary (could be a list or scalar)
        if not isinstance(child_data, dict):
            continue

        # Parse child node
        child_nodes = parse_target_node(
            target_basename=target_basename,
            source_dirname=source_dirname,
            target_node_json=child_data,
        )

        # Add to parent node if not None
        if child_nodes:
            target_node.child_nodes.extend(child_nodes)

    return [target_node]


def _handle_regex_pattern(
    source_dirname: str,
    target_basename: str,
    target_node_json: dict,
) -> T.List[TargetNode]:
    # Extract variable name from pattern (remove parentheses)
    variable_name = target_basename[1:-1]

    # Get source path pattern from __source__ field
    source_pattern = target_node_json.get("__source__", "")
    if not source_pattern:
        logger.warning(
            f"Missing __source__ field for regex pattern '{target_basename}'"
        )
        return []

    # Replace <variable-name> with * in source pattern for globbing
    glob_pattern = source_pattern.replace(f"<{variable_name}>", "*")

    # Create full glob pattern
    full_glob_pattern = normalize_path(glob_pattern, base_path=source_dirname)

    # Find matching paths
    matching_paths = glob.glob(full_glob_pattern)

    if not matching_paths:
        logger.debug(f"No matches found for glob pattern: {full_glob_pattern}")
        return []

    # Create regex pattern to extract variable value
    regex_pattern = source_pattern.replace(
        f"<{variable_name}>", f"(?P<{variable_name}>.*)"
    )
    regex = re.compile(regex_pattern)

    # Process each matching path
    child_target_node_json = target_node_json.copy()
    del child_target_node_json["__source__"]
    child_nodes = []
    for path in matching_paths:
        # Extract relative path from source_dirname
        rel_path = os.path.relpath(path, source_dirname)

        # Extract variable value using regex
        match = regex.match(rel_path)
        if not match:
            continue

        # Get the variable value
        target_basename = match.group(variable_name)

        # Parse the child node for this instance
        more_child_nodes = parse_target_node(
            target_basename=target_basename,
            source_dirname=path,
            target_node_json=child_target_node_json,
        )

        if more_child_nodes:
            child_nodes.extend(more_child_nodes)

    return child_nodes
