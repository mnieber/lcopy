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
    # Extract variable name from pattern (remove parentheses)
    variable_name = target_basename[1:-1]

    # The pattern is now directly in the variable name
    # For example: scenarios/<scenario_name>
    glob_pattern = variable_name.replace(f"<{variable_name.split('/')[-1][1:-1]}>", "*")

    # Create full glob pattern
    full_glob_pattern = normalize_path(glob_pattern, base_path=source_dirname)

    # Find matching paths
    matching_paths = glob.glob(full_glob_pattern)

    if not matching_paths:
        logger.debug(f"No matches found for glob pattern: {full_glob_pattern}")
        return []

    # Create regex pattern to extract variable value
    # Convert the glob pattern to a regex pattern by escaping special chars and replacing * with capture group
    regex_pattern = re.escape(variable_name).replace("\\*", ".*")
    # Replace the variable placeholder with a named capture group
    var_placeholder = re.escape(f"<{variable_name.split('/')[-1][1:-1]}>")
    regex_pattern = regex_pattern.replace(
        var_placeholder, f"(?P<{variable_name.split('/')[-1][1:-1]}>.*)"
    )
    regex = re.compile(regex_pattern)

    # Process each matching path
    child_nodes = []
    for path in matching_paths:
        # Extract relative path from source_dirname
        rel_path = os.path.relpath(path, source_dirname)

        # Extract variable value using regex
        match = regex.match(rel_path)
        if not match:
            continue

        # Get the variable value - use the last component of the path if regex fails
        if variable_name.split("/")[-1][1:-1] in match.groupdict():
            target_basename = match.group(variable_name.split("/")[-1][1:-1])
        else:
            target_basename = os.path.basename(path)

        # Process the child node JSON structure
        include_patterns = []
        exclude_patterns = []

        for key, value in target_node_json.items():
            if isinstance(value, bool):
                if value:
                    include_patterns.append(key)
                else:
                    exclude_patterns.append(f"!{key}")

        # Create a new target node for this match
        child_node = TargetNode(
            source_dirname=path,
            target_basename=target_basename,
            filename_patterns=include_patterns + exclude_patterns,
            child_nodes=[],
            labels=labels or [],
        )

        # Add this node to our result list
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
