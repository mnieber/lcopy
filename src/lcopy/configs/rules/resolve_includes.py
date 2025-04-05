import os
import logging
import yaml
import typing as T

from lcopy.configs.utils.normalize_path import normalize_path
from lcopy.runtime.models.options import Options

logger = logging.getLogger(__name__)


def resolve_includes(
    config_file: str, options: Options, processed_files: T.List[str]
) -> T.List[str]:
    if processed_files is None:
        processed_files = []

    # Normalize the config file path
    config_file = normalize_path(config_file, None)

    # If this file has already been processed, return empty list to avoid duplicates
    if config_file in processed_files:
        logger.debug(f"Config file {config_file} already processed, skipping")
        return []

    # Mark this file as processed
    processed_files.append(config_file)

    # Start with the current config file
    result = [config_file]

    try:
        # Read the config file
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        # If the file doesn't contain an 'include' key or it's empty, return just this file
        if (
            not config_data
            or "include" not in config_data
            or not config_data["include"]
        ):
            return result

        # Get the directory of the current config file to resolve relative paths
        config_dir = os.path.dirname(config_file)

        # Process each included config file
        for include_path in config_data["include"]:
            # Normalize the include path relative to the config directory
            include_path = normalize_path(include_path, config_dir)

            logger.debug(f"Resolving include: {include_path}")

            # Recursively resolve includes in the included file
            included_files = resolve_includes(include_path, options, processed_files)
            result.extend(included_files)

    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_file}")
    except yaml.YAMLError as e:
        logger.warning(f"Error parsing YAML in {config_file}: {e}")
    except Exception as e:
        logger.error(f"Error processing includes in {config_file}: {e}")

    return result
