import glob
import logging
import os
import re
import typing as T

from lcopy.configs.models.target_node import TargetNode
from lcopy.files.rules.get_filtered_files import get_filtered_files
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_target_node(
    target_basename,
    source_dirname: str,
    target_node_json: dict,
    labels: T.List[str] = None,
    ignore_patterns: T.List[str] = None,
) -> T.List[TargetNode]:
    # Check if target_basename is a regex pattern (enclosed in parentheses)
    if target_basename.startswith("(") and target_basename.endswith(")"):
        return _handle_regex_pattern(
            source_dirname, target_basename, target_node_json, labels, ignore_patterns
        )

    # Create target node instance
    target_node = TargetNode(
        source_dirname=source_dirname,
        target_basename=target_basename,
        filename_patterns=[],  # We'll populate this with concrete files
        child_nodes=[],
        labels=labels or [],
    )

    # Collect include and exclude patterns
    include_patterns = []
    exclude_patterns = []

    # Process each entry in the target_node_json
    for key, value in target_node_json.items():
        # Skip processing child nodes that don't have boolean values
        if isinstance(value, bool):
            # If value is True, add to include patterns, else add to exclude patterns
            if value:
                include_patterns.append(key)
            else:
                exclude_patterns.append(key)
        elif isinstance(value, dict):
            # This is a child node
            child_nodes = parse_target_node(
                target_basename=key,
                source_dirname=source_dirname,
                target_node_json=value,
                labels=labels,
                ignore_patterns=ignore_patterns,
            )

            # Add to parent node if not None
            if child_nodes:
                target_node.child_nodes.extend(child_nodes)

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
        target_node.filename_patterns = files

        # Handle directories by creating additional nodes to process
        if directories:
            child_nodes = _handle_directories(
                directories, source_dirname, labels, ignore_patterns
            )
            if child_nodes:
                target_node.child_nodes.extend(child_nodes)

    logger.debug(
        f"Created target node: {target_basename} with {len(target_node.filename_patterns)} files"
    )
    return [target_node]


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
    parent_source_dirname: str,
    labels: T.List[str] = None,
    ignore_patterns: T.List[str] = None,
) -> T.List[TargetNode]:
    """
    Process directories by creating appropriate JSON structures
    and parsing them recursively through the main parse_target_node function.
    """
    child_nodes = []

    for directory in directories:
        dir_basename = os.path.basename(directory)

        # Create a simple JSON structure with "*" pattern to include all files
        target_node_json = {"*": True}

        # Process this directory through parse_target_node
        directory_nodes = parse_target_node(
            target_basename=dir_basename,
            source_dirname=directory,
            target_node_json=target_node_json,
            labels=labels,
            ignore_patterns=ignore_patterns,
        )

        if directory_nodes:
            child_nodes.extend(directory_nodes)
            logger.debug(
                f"Created directory child node: {dir_basename} through recursive processing"
            )

    return child_nodes


def _handle_regex_pattern(
    source_dirname: str,
    target_basename: str,
    target_node_json: dict,
    labels: T.List[str] = None,
    ignore_patterns: T.List[str] = None,
) -> T.List[TargetNode]:
    # Extract regex pattern from target_basename (remove parentheses)
    regex_pattern = target_basename[1:-1]

    # Find the variable part
    variable_name = _extract_variable_from_regex(regex_pattern)
    if not variable_name:
        raise NoVariableInRegexPattern()

    # Create glob pattern and find matching paths
    full_glob_pattern = _create_glob_pattern(
        regex_pattern, variable_name, source_dirname
    )
    matching_paths = glob.glob(full_glob_pattern)

    if not matching_paths:
        logger.debug(f"No matches found for glob pattern: {full_glob_pattern}")
        return []

    # Create regex for extracting variable values
    regex = _create_regex_matcher(regex_pattern, variable_name)

    # Process each matching path
    child_nodes = []
    for path in matching_paths:
        # Extract relative path and variable value
        rel_path = os.path.relpath(path, source_dirname)
        match = regex.match(rel_path)
        if not match:
            continue

        # Get target basename
        target_basename = (
            match.group(variable_name)
            if variable_name in match.groupdict()
            else os.path.basename(path)
        )

        # Process this path recursively through parse_target_node
        # The target_node_json will be processed the same as any other node
        more_child_nodes = parse_target_node(
            target_basename=target_basename,
            source_dirname=path,
            target_node_json=target_node_json,
            labels=labels,
            ignore_patterns=ignore_patterns,
        )

        if more_child_nodes:
            child_nodes.extend(more_child_nodes)

    return child_nodes


def _extract_variable_from_regex(regex_pattern: str) -> T.Optional[str]:
    """Extract the variable part from a regex pattern."""
    variable_match = re.search(r"<([^>]+)>", regex_pattern)
    return variable_match.group(1) if variable_match else None


def _create_glob_pattern(
    regex_pattern: str, variable_name: str, source_dirname: str
) -> str:
    """Create a glob pattern from a regex pattern by replacing variable with wildcard."""
    glob_pattern = regex_pattern.replace(f"<{variable_name}>", "*")
    return normalize_path(glob_pattern, base_path=source_dirname)


def _create_regex_matcher(regex_pattern: str, variable_name: str) -> re.Pattern:
    """Create a regex pattern to extract variable values."""
    regex_expr = re.escape(regex_pattern).replace("\\*", ".*")
    var_placeholder = re.escape(f"<{variable_name}>")
    regex_expr = regex_expr.replace(var_placeholder, f"(?P<{variable_name}>.*)")
    return re.compile(regex_expr)


class NoVariableInRegexPattern(Exception):
    pass
