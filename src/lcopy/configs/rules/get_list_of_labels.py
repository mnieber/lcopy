import logging
import os
import typing as T

import yaml
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def get_list_of_labels(config_file: str) -> T.List[str]:
    """
    Extract all labels from the targets section of a config file and
    all included source configs.
    """
    labels = set()
    processed_files = set()

    # Process the config file and collect all labels
    _collect_labels_from_file(config_file, labels, processed_files)

    logger.info(f"Found {len(labels)} unique labels across all config files")
    return sorted(list(labels))


def _collect_labels_from_file(
    config_file: str, labels: set, processed_files: set
) -> None:
    """
    Recursively collect labels from a config file and its sources.
    """
    # Normalize path
    normalized_config_file = normalize_path(config_file)

    # Skip if already processed
    if normalized_config_file in processed_files:
        return

    # Mark as processed
    processed_files.add(normalized_config_file)

    logger.info(f"Extracting labels from config file: {normalized_config_file}")

    # Check if file exists
    if not os.path.isfile(normalized_config_file):
        logger.error(f"Config file not found: {normalized_config_file}")
        return

    # Read and parse the config file
    try:
        with open(normalized_config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return

    # Extract labels from targets section
    targets_data = config_data.get("targets", {})
    for label in targets_data.keys():
        labels.add(label)

    # Process sources section to find more labels
    sources_data = config_data.get("sources", {})
    if sources_data:
        source_dirname = os.path.dirname(normalized_config_file)
        for source_path, _ in sources_data.items():
            # Get absolute path to source
            source_abs_path = normalize_path(source_path, base_path=source_dirname)

            # Check for config file in the source directory
            source_config_file = os.path.join(source_abs_path, ".lcopy.yaml")

            if os.path.isfile(source_config_file):
                # Recursively collect labels from the source config file
                _collect_labels_from_file(source_config_file, labels, processed_files)
