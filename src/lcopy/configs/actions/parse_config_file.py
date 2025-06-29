import logging
import typing as T
from pathlib import Path

import yaml
from lcopy.configs.models.config import Config
from lcopy.configs.models.options import Options
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_config_file(
    config_file: str,
) -> T.Optional[Config]:
    # Normalize path
    normalized_config_file = normalize_path(config_file)
    logger.info(f"Parsing config file: {normalized_config_file}")

    # Read the config file
    try:
        with open(normalized_config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error(f"Config file not found: {normalized_config_file}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return None

    # Get source directory from config file path
    source_dirname = str(Path(normalized_config_file).parent)
    logger.info(f"Source directory: {source_dirname}")

    # Create Config instance
    config = Config(
        source_dirname=source_dirname,
        targets_json=config_data.get("files", {}),
    )

    # Parse sources section
    if "sources" in config_data:
        _parse_sources(config_data.get("sources", {}), config, source_dirname)

    # Parse options section
    if "options" in config_data:
        _parse_options(config_data.get("options", {}), config)

    return config


def _parse_sources(sources_data: dict, config: Config, base_dirname: str) -> None:
    """Parse the sources section and populate the config.sources dict."""
    for source_path, source_alias in sources_data.items():
        # Normalize the source path relative to the config file location
        absolute_path = normalize_path(source_path, base_path=base_dirname)
        config.sources[source_alias] = absolute_path
        logger.debug(f"Added source alias '{source_alias}' -> {absolute_path}")


def _parse_options(options_data: dict, config: Config) -> None:
    """Parse the options section and set the config.options field."""
    concatenated_output_filename = options_data.get("concatenated_output_filename", "")
    options = Options(
        destination=normalize_path(
            options_data.get("destination", config.source_dirname)
        ),
        concatenated_output_filename=(
            normalize_path(
                concatenated_output_filename,
                base_path=config.source_dirname,
            )
            if concatenated_output_filename
            else ""
        ),
        conflict=options_data.get("conflict", "skip"),
        verbose=options_data.get("verbose", False),
        purge=options_data.get("purge", False),
        dry_run=options_data.get("dry_run", False),
        default_ignore=options_data.get("default_ignore", True),
        extra_ignore=options_data.get("extra_ignore", []),
    )
    config.options = options

    logger.debug(f"Added options to config: destination={options.destination}")
