import os
import yaml
from typing import List, Dict, Any

from lcopy.configs.models.root_config_node import RootConfigNode
from lcopy.configs.models.config_node import ConfigNode
from lcopy.runtime.models.options import Options


def parse_config_file(config_file: str, options: Options) -> List[RootConfigNode]:
    # Ensure the config file exists
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")

    source_path = os.path.dirname(os.path.abspath(config_file))

    # Read and parse the config file
    with open(config_file, "r") as file:
        config_data = yaml.safe_load(file)

    # Filter config sections based on labels in options
    root_config_nodes = []
    for label in options.labels:
        if label in config_data:
            root_node = _create_root_config_node(label, source_path, config_data[label])
            root_config_nodes.append(root_node)

    return root_config_nodes


def _create_root_config_node(
    label: str, source_path: str, config_section: Dict[str, Any]
) -> RootConfigNode:
    root_node = RootConfigNode(label=label, source_path=source_path)

    # Process each subdirectory in the config section
    for dirname, patterns in config_section.items():
        # Process child nodes recursively
        config_node = _process_config_section(dirname, patterns)
        if config_node:
            root_node.child_nodes.append(config_node)

    return root_node


def _process_config_section(dirname: str, patterns: Dict[str, Any]) -> ConfigNode:
    # Handle special case for the current directory (.)
    if "." in patterns:
        filename_patterns = patterns["."]
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
