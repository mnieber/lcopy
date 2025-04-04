import os
import re
import glob
from typing import List, Optional

from lcopy.configs.models.config_node import ConfigNode
from lcopy.filemaps.models.filemap_node import FilemapNode
from lcopy.filemaps.actions.create_filemap_node import create_filemap_node
from lcopy.runtime.models.options import Options


def process_config(
    config: ConfigNode,
    file_map_tree: List[FilemapNode],
    current_dir: str,
    base_target_dir: str,
    options: Optional[Options] = None,
) -> None:
    # Check if dirname pattern is a regex pattern (enclosed in parentheses)
    is_regex = config.dirname_pattern.startswith(
        "("
    ) and config.dirname_pattern.endswith(")")

    if is_regex:
        # Extract the pattern without parentheses
        pattern_str = config.dirname_pattern[1:-1]

        # Find the variable part in the pattern (enclosed in square brackets)
        # Only one variable part is allowed per pattern
        var_parts = re.findall(r"\[(.*?)\]", pattern_str)
        var_part = var_parts[0] if var_parts else None

        # Replace variable part with wildcard for glob matching
        glob_pattern = re.sub(r"\[(.*?)\]", "*", pattern_str)

        # Find all matching directories
        matching_dirs = glob.glob(os.path.join(current_dir, glob_pattern))

        for source_dir in matching_dirs:
            # Extract the variable part value from the matched directory
            rel_path = os.path.relpath(source_dir, current_dir)

            # Create a regex pattern to extract variable value
            target_subdir = ""
            if var_part:
                extract_pattern = pattern_str.replace(
                    f"[{var_part}]", f"(?P<{var_part}>.*?)$"
                )
                match = re.match(extract_pattern, rel_path)
                if match and var_part in match.groupdict():
                    # Use the variable value as the target subdirectory
                    target_subdir = match.group(var_part)
                else:
                    continue  # Skip if we can't extract the variable
            else:
                # If no variable part, use the relative path
                target_subdir = rel_path

            target_dir = os.path.join(base_target_dir, target_subdir)

            # Create a simple non-regex config node for this match
            simple_config = ConfigNode(
                dirname_pattern=".",  # Use current directory
                filename_patterns=config.filename_patterns,
                child_nodes=config.child_nodes,
            )

            # Process the simple config with the matched directory as the current directory
            process_config(
                simple_config, file_map_tree, source_dir, target_dir, options
            )
    else:
        # Process this directory with the config's filename patterns
        target_dir = os.path.join(base_target_dir, config.dirname_pattern)
        _process_directory(current_dir, target_dir, config, file_map_tree)

        # Process child config nodes
        for child_config in config.child_nodes:
            process_config(
                child_config, file_map_tree, current_dir, target_dir, options
            )


def _process_directory(
    source_dir: str,
    target_dir: str,
    config: ConfigNode,
    file_map_tree: List[FilemapNode],
) -> None:
    # Skip if source directory doesn't exist
    if not os.path.exists(source_dir):
        return

    # Collect all matching files from the filename patterns
    matching_files = []
    for pattern in config.filename_patterns:
        # Handle glob patterns in filenames
        pattern_path = os.path.join(source_dir, pattern)
        for file_path in glob.glob(pattern_path):
            if os.path.isfile(file_path):
                # Store relative path to source directory
                rel_path = os.path.relpath(file_path, source_dir)
                matching_files.append(rel_path)

    # Create a filemap node if there are matching files
    if matching_files:
        filemap_node = create_filemap_node(
            source_path=source_dir, target_path=target_dir, filenames=matching_files
        )
        file_map_tree.append(filemap_node)
