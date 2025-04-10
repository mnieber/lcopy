import logging
import typing as T
from pathlib import Path

import yaml
from lcopy.configs.actions.parse_target_node import parse_target_node
from lcopy.configs.models.config import Config
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_config_file(
    config_file: str,
    config_file_skip_list: T.List[str] = None,
    recursive: bool = True,
    labels: T.List[str] = None,
    ignore_patterns: T.List[str] = None,
) -> T.List[Config]:
    # Initialize skip list if not provided
    if config_file_skip_list is None:
        config_file_skip_list = []

    # Normalize path
    normalized_config_file = normalize_path(config_file)

    # Skip if already processed
    if normalized_config_file in config_file_skip_list:
        logger.info(f"Skipping already processed config file: {normalized_config_file}")
        return []

    # Add to skip list
    config_file_skip_list.append(normalized_config_file)

    logger.info(f"Parsing config file: {normalized_config_file}")

    # Read the config file
    try:
        with open(normalized_config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error(f"Config file not found: {normalized_config_file}")
        return []
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return []

    # Get source directory from config file path
    source_dirname = str(Path(normalized_config_file).parent)
    logger.info(f"Source directory: {source_dirname}")

    # Create Config instance
    config = Config(
        source_dirname=source_dirname,
        include_fns=config_data.get("include_fns", []),
        target_nodes=[],
    )

    # Parse target nodes
    targets_data = config_data.get("targets", {})
    for label, targets_json in targets_data.items():
        if label not in labels:
            continue

        for target_basename, target_node_json in targets_json.items():
            # Parse target node
            target_nodes = parse_target_node(
                target_basename=target_basename,
                source_dirname=source_dirname,
                target_node_json=target_node_json,
                ignore_patterns=ignore_patterns,
            )

            # Add to config if not None
            if target_nodes:
                config.target_nodes.extend(target_nodes)

    configs = [config]

    # Process included config files if recursive is enabled
    if recursive and config.include_fns:
        for include_fn in config.include_fns:
            # Resolve path relative to source directory
            include_path = normalize_path(include_fn, base_path=source_dirname)
            included_configs = parse_config_file(
                config_file=include_path,
                config_file_skip_list=config_file_skip_list,
                recursive=recursive,
                labels=labels,
            )
            configs.extend(included_configs)

    return configs
