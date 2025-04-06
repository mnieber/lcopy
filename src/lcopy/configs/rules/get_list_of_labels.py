import logging
import os
import yaml
import typing as T
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def get_list_of_labels(config_file: str) -> T.List[str]:
    labels = set()

    # Normalize path
    normalized_config_file = normalize_path(config_file)

    logger.info(f"Extracting labels from config file: {normalized_config_file}")

    # Check if file exists
    if not os.path.isfile(normalized_config_file):
        logger.error(f"Config file not found: {normalized_config_file}")
        return list(labels)

    # Read and parse the config file
    try:
        with open(normalized_config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return list(labels)

    # Extract labels from targets
    targets_data = config_data.get("targets", {})
    _extract_labels_from_targets(targets_data, labels)

    # Process include_fns if present
    include_fns = config_data.get("include_fns", [])
    if include_fns:
        source_dirname = os.path.dirname(normalized_config_file)
        for include_fn in include_fns:
            include_path = normalize_path(include_fn, base_path=source_dirname)
            included_labels = get_list_of_labels(include_path)
            labels.update(included_labels)

    logger.info(f"Found {len(labels)} unique labels in {normalized_config_file}")
    return sorted(list(labels))


def _extract_labels_from_targets(targets_data: dict, labels: set) -> None:
    for label, target_node in targets_data.items():
        labels.add(label)
