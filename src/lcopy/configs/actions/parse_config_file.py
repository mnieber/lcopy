import os
import logging
import yaml
import typing as T

from lcopy.configs.models import Config, RootConfigNode, ConfigNode

logger = logging.getLogger(__name__)


def parse_config_file(config_file: str) -> Config:
    """
    Parses a config file and returns a Config object with the parsed configuration.

    Args:
        config_file: Path to the config file

    Returns:
        Config object with the parsed configuration
    """
    logger.debug(f"Parsing config file: {config_file}")

    # Create a new Config object with the source path set to the config file
    config = Config(source_path=config_file)

    try:
        # Read and parse the YAML file
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        # If the file is empty or not a valid YAML file, return the empty config
        if not config_data:
            logger.warning(
                f"Config file is empty or not a valid YAML file: {config_file}"
            )
            return config

        # Parse include directives
        if "include" in config_data and isinstance(config_data["include"], list):
            config.include = config_data["include"]

        # Get the directory of the config file to resolve relative paths
        config_dir = os.path.dirname(config_file)

        # Parse target directives
        if "target" in config_data and isinstance(config_data["target"], dict):
            # Process each label defined in the target section
            for label, target_data in config_data["target"].items():
                # Create a root config node for each label
                root_node = RootConfigNode(source_path=config_dir, label=label)

                # Process the target data for this label
                if target_data and isinstance(target_data, dict):
                    # Each key in the target data is a target directory
                    for target_dir, dir_data in target_data.items():
                        # Process this target directory and its children
                        child_nodes = _parse_target_directory(
                            target_dir, dir_data, config_dir
                        )
                        root_node.child_nodes.extend(child_nodes)

                # Add the root node to the config
                config.root_config_nodes.append(root_node)

    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML in {config_file}: {e}")
    except Exception as e:
        logger.error(f"Error parsing config file {config_file}: {e}")

    return config


def _parse_target_directory(
    target_dir: str, dir_data: dict, base_path: str
) -> T.List[ConfigNode]:
    """
    Parse a target directory configuration and its children.

    Args:
        target_dir: The target directory name or pattern
        dir_data: The configuration data for this directory
        base_path: The base path for resolving relative paths

    Returns:
        List of ConfigNode objects representing this directory and its children
    """
    result = []

    # Process directory data
    if isinstance(dir_data, dict):
        # Create a config node for this directory
        node = ConfigNode(
            source_path=base_path,
            dirname_pattern=target_dir,
            filename_patterns=_extract_file_patterns(dir_data),
        )

        # Process child directories recursively
        for child_dir, child_data in dir_data.items():
            # Skip entries that are not dictionaries (like file patterns)
            if not isinstance(child_data, dict):
                continue

            # For each child directory, process it recursively
            child_nodes = _parse_target_directory(child_dir, child_data, base_path)
            node.child_nodes.extend(child_nodes)

        result.append(node)

    return result


def _extract_file_patterns(dir_data: dict) -> T.List[str]:
    """
    Extract file patterns from directory data.

    Args:
        dir_data: The directory data to extract patterns from

    Returns:
        List of file patterns
    """
    patterns = []

    # Look for a list of file patterns at the "." key
    if "." in dir_data and isinstance(dir_data["."], list):
        patterns.extend(dir_data["."])

    return patterns
