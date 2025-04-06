import logging
import os
import yaml
from lcopy.runtime.models.options import Options
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_options_file(options_file: str) -> Options:
    logger.info(f"Parsing options file: {options_file}")

    # Normalize the path to the options file
    normalized_options_file = normalize_path(options_file)
    options_dirname = os.path.dirname(normalized_options_file)

    # Read the options file
    try:
        with open(normalized_options_file, "r") as f:
            options_data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Options file not found: {normalized_options_file}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing options file: {e}")
        raise

    # Extract options with defaults
    config_fns = options_data.get("config_fns", [])
    destination = options_data.get("destination", "")
    labels = options_data.get("labels", [])
    conflict = options_data.get("conflict", "skip")
    verbose = options_data.get("verbose", False)
    purge = options_data.get("purge", False)
    dry_run = options_data.get("dry_run", False)
    default_ignore = options_data.get("default_ignore", True)
    extra_ignore = options_data.get("extra_ignore", [])

    # Normalize the destination path (expanding ~ and env vars)
    if destination:
        destination = normalize_path(destination, base_path=options_dirname)

    # Normalize config file paths
    normalized_config_fns = []
    for config_fn in config_fns:
        normalized_config_fns.append(
            normalize_path(config_fn, base_path=options_dirname)
        )

    logger.info(f"Found {len(normalized_config_fns)} config files")

    # Create and return Options instance
    return Options(
        config_fns=normalized_config_fns,
        destination=destination,
        labels=labels,
        conflict=conflict,
        verbose=verbose,
        purge=purge,
        dry_run=dry_run,
        default_ignore=default_ignore,
        extra_ignore=extra_ignore,
    )
