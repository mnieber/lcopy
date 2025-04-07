import logging
import os
import glob
import re
import typing as T
from lcopy.configs.models.target_node import TargetNode
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_target_node(
    target_basename,
    source_dirname: str,
    target_node_json: dict,
    labels: T.List[str] = None,
) -> T.List[TargetNode]:
    # Initialize include and exclude patterns
    include_patterns = []
    exclude_patterns = []

    # Check if target_basename is a regex pattern (enclosed in parentheses)
    if target_basename.startswith("(") and target_basename.endswith(")"):
        return _handle_regex_pattern(
            source_dirname, target_basename, target_node_json, labels
        )

    # Create target node instance
    target_node = TargetNode(
        source_dirname=source_dirname,
        target_basename=target_basename,
        filename_patterns=[],  # We'll populate this later
        child_nodes=[],
        labels=labels or [],
    )

    # Process each entry in the target_node_json
    for key, value in target_node_json.items():
        # Skip processing child nodes that don't have boolean values
        if isinstance(value, bool):
            # If value is True, add to include patterns, else add to exclude patterns
            if value:
                include_patterns.append(key)
            else:
                # Add to exclude patterns with ! prefix
                exclude_patterns.append(f"!{key}")
        elif isinstance(value, dict):
            # This is a child node
            child_nodes = parse_target_node(
                target_basename=key,
                source_dirname=source_dirname,
                target_node_json=value,
                labels=labels,
            )

            # Add to parent node if not None
            if child_nodes:
                target_node.child_nodes.extend(child_nodes)

    # Combine include and exclude patterns
    target_node.filename_patterns = include_patterns + exclude_patterns

    logger.debug(
        f"Created target node: {target_basename} with {len(target_node.filename_patterns)} patterns"
    )
    return [target_node]


def _handle_regex_pattern(
    source_dirname: str,
    target_basename: str,
    target_node_json: dict,
    labels: T.List[str] = None,
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

        # Get patterns from JSON
        include_patterns, exclude_patterns = _get_patterns_from_json(target_node_json)

        # Create the target node
        child_node = TargetNode(
            source_dirname=path,
            target_basename=target_basename,
            filename_patterns=include_patterns + exclude_patterns,
            child_nodes=[],
            labels=labels or [],
        )

        child_nodes.append(child_node)

        # Process nested levels recursively
        for key, value in target_node_json.items():
            if isinstance(value, dict):
                more_child_nodes = parse_target_node(
                    target_basename=key,
                    source_dirname=path,
                    target_node_json=value,
                    labels=labels,
                )

                if more_child_nodes:
                    child_node.child_nodes.extend(more_child_nodes)

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


def _get_patterns_from_json(
    target_node_json: dict,
) -> T.Tuple[T.List[str], T.List[str]]:
    """Extract include and exclude patterns from target node JSON."""
    include_patterns = []
    exclude_patterns = []

    for key, value in target_node_json.items():
        if isinstance(value, bool):
            if value:
                include_patterns.append(key)
            else:
                exclude_patterns.append(f"!{key}")

    return include_patterns, exclude_patterns


class NoVariableInRegexPattern(Exception):
    pass
