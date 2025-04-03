import os
import yaml
from typing import List, Dict, Any

from configs.models.root_config_node import RootConfigNode
from configs.models.config_node import ConfigNode
from options.models.options import Options


def parse_config_file(config_file: str, options: Options) -> List[RootConfigNode]:
    """
    Parse a config file and build a tree structure of config nodes.

    This function reads the YAML config file and creates RootConfigNode objects
    for each section that matches a label specified in the options.

    Args:
        config_file: Path to the config YAML file
        options: Options object containing labels to filter config sections

    Returns:
        List[RootConfigNode]: List of root config nodes from the parsed config file

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the config file contains invalid YAML
    """
    # Ensure the config file exists
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")

    # Read and parse the config file
    with open(config_file, "r") as file:
        config_data = yaml.safe_load(file)

    # Filter config sections based on labels in options
    root_config_nodes = []
    for label in options.labels:
        if label in config_data:
            root_node = _create_root_config_node(label, config_data[label])
            root_config_nodes.append(root_node)

    return root_config_nodes


def _create_root_config_node(
    label: str, config_section: Dict[str, Any]
) -> RootConfigNode:
    """
    Create a RootConfigNode for a given label and config section.

    Args:
        label: Label for the root config node
        config_section: Dictionary containing the config section data

    Returns:
        RootConfigNode: Root config node with child nodes
    """
    root_node = RootConfigNode(label=label)

    # Process each subdirectory in the config section
    for dirname, patterns in config_section.items():
        # Process child nodes recursively
        config_node = _process_config_section(dirname, patterns)
        if config_node:
            root_node.child_nodes.append(config_node)

    return root_node


def _process_config_section(dirname: str, patterns: Dict[str, Any]) -> ConfigNode:
    """
    Process a config section and create a ConfigNode.

    Args:
        dirname: Directory name or pattern
        patterns: Dictionary of filename patterns or nested subdirectories

    Returns:
        ConfigNode: Config node with filename patterns and child nodes
    """
    # Handle special case for the current directory (.)
    if "." in patterns:
        filename_patterns = patterns["."]
        # Remove the "." entry to process remaining entries as child nodes
        patterns_copy = patterns.copy()
        del patterns_copy["."]
        # If there are no more entries, set patterns to empty dict
        if patterns_copy:
            patterns = patterns_copy
        else:
            patterns = {}
    else:
        filename_patterns = []

    # Create the config node
    config_node = ConfigNode(
        dirname_pattern=dirname, filename_patterns=filename_patterns
    )

    # Process child nodes recursively
    for child_dirname, child_patterns in patterns.items():
        # Skip the already processed "." entry
        if child_dirname == ".":
            continue

        child_config_node = _process_config_section(child_dirname, child_patterns)
        if child_config_node:
            config_node.child_nodes.append(child_config_node)

    return config_node
