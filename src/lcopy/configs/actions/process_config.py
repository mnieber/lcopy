import os
import re
import glob
import logging
import typing as T

from lcopy.configs.models import Config, RootConfigNode, ConfigNode
from lcopy.filemaps.models import FilemapNode
from lcopy.filemaps.rules.filter_filenames import filter_filenames
from lcopy.configs.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def process_config(
    destination,
    config: Config,
    filemap_nodes: list,
    ignore_patterns: T.List[str] = None,
) -> None:
    logger.debug(f"Processing config: {config.source_path}")

    if ignore_patterns is None:
        ignore_patterns = []

    # Process each root config node
    for root_node in config.root_config_nodes:
        _process_root_config_node(
            destination, root_node, filemap_nodes, ignore_patterns
        )


def _process_root_config_node(
    destination,
    root_node: RootConfigNode,
    filemap_nodes: list,
    ignore_patterns: T.List[str],
) -> None:
    logger.debug(f"Processing root config node with label: {root_node.label}")

    # Process each child node
    for child_node in root_node.child_nodes:
        _process_config_node(destination, child_node, filemap_nodes, ignore_patterns)


def _process_config_node(
    destination,
    config_node: ConfigNode,
    filemap_nodes: list,
    ignore_patterns: T.List[str],
) -> None:
    # Check if this is a regex pattern
    if _is_regex_pattern(config_node.dirname_pattern):
        _process_regex_pattern(destination, config_node, filemap_nodes, ignore_patterns)
    else:
        _process_simple_target_directory(
            destination, config_node, filemap_nodes, ignore_patterns
        )


def _is_regex_pattern(dirname: str) -> bool:
    # A regex pattern starts with '(' and ends with ')' and contains a variable part in '[]'
    return (
        dirname.startswith("(")
        and dirname.endswith(")")
        and "[" in dirname
        and "]" in dirname
    )


def _process_regex_pattern(
    destination,
    config_node: ConfigNode,
    filemap_nodes: list,
    ignore_patterns: T.List[str],
) -> None:
    # Extract the variable part from the regex pattern (between square brackets)
    match = re.search(r"\[(.*?)\]", config_node.dirname_pattern)
    if not match:
        logger.warning(f"Invalid regex pattern: {config_node.dirname_pattern}")
        return

    # Convert the regex pattern to a glob pattern
    # Replace the variable part with a wildcard
    pattern_without_parens = config_node.dirname_pattern[1:-1]  # Remove ( and )
    glob_pattern = re.sub(r"\[.*?\]", "*", pattern_without_parens)

    # Join with the source path to create a full glob pattern
    full_glob_pattern = os.path.join(config_node.source_path, glob_pattern)

    # Find all matches of the glob pattern
    matches = glob.glob(full_glob_pattern)

    for match_path in matches:
        # Create a new config node for this match
        new_config_node = ConfigNode(
            source_path=match_path,
            dirname_pattern=os.path.basename(match_path),  # HACK!!!
            filename_patterns=config_node.filename_patterns,
            child_nodes=config_node.child_nodes,
        )

        # Process this new config node as a simple target directory
        _process_simple_target_directory(
            destination, new_config_node, filemap_nodes, ignore_patterns
        )


def _process_simple_target_directory(
    destination: str,
    config_node: ConfigNode,
    filemap_nodes: list,
    ignore_patterns: T.List[str],
) -> None:
    # Determine the list of exclude patterns for this target directory
    exclude_patterns = _determine_exclude_patterns(config_node)

    # Determine the list of filenames in this target directory
    filenames = filter_filenames(
        config_node.filename_patterns,
        config_node.source_path,
        exclude_patterns,
        ignore_patterns,
    )

    # Create a filemap node for this target directory
    target_path = normalize_path(config_node.dirname_pattern, destination)

    # Create a new filemap node
    if filenames:
        filemap_node = FilemapNode(
            target_path=target_path,
            source_path=config_node.source_path,
            filenames=filenames,
        )
        filemap_nodes.append(filemap_node)

    # Process child nodes recursively
    for child_node in config_node.child_nodes:
        _process_config_node(target_path, child_node, filemap_nodes, ignore_patterns)


def _determine_exclude_patterns(config_node: ConfigNode) -> T.List[str]:
    exclude_patterns = []

    for pattern in config_node.filename_patterns:
        if pattern.startswith("!"):
            # Remove the exclamation mark and add to exclude patterns
            exclude_patterns.append(pattern[1:])

    return exclude_patterns
