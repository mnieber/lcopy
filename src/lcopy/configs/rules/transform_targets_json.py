import logging
import typing as T
from collections import defaultdict
from pathlib import Path

from lcopy.configs.actions.parse_config_file import parse_config_file

logger = logging.getLogger(__name__)


def transform_targets_json(
    targets_json: dict,
    source_dirname: str,
    sources: T.Dict[str, str],
    labels: T.List[str],
    skip_list: T.List[str] | None = None,
) -> dict:
    if skip_list is None:
        skip_list = []

    transformed: T.Dict = {"__source_dir__": source_dirname, **targets_json}

    _process_child_nodes(
        source_dirname=source_dirname,
        sources=sources,
        labels=labels,
        skip_list=skip_list,
        transformed=transformed,
    )

    return transformed


def _transform_target_node_json(
    cd: str | None,
    target_node_json: dict,
    source_dirname: str,
    sources: T.Dict[str, str],
    labels: T.List[str],
    skip_list: T.List[str],
) -> dict:
    # Create a copy to avoid modifying the original
    transformed = dict(target_node_json)
    transformed["__source_dir__"] = source_dirname
    if cd:
        transformed["__cd__"] = cd

    # Process includes
    _process_includes(sources, skip_list, transformed)

    # Recursively transform child nodes
    _process_child_nodes(
        source_dirname,
        sources,
        labels,
        skip_list,
        transformed,
    )

    return transformed


def _process_includes(sources, skip_list, transformed):
    includes = transformed.get("__include__", [])
    if includes:
        if isinstance(includes, str):
            includes = [includes]

        # Process each include
        labels_by_source_alias = _get_labels_by_source_alias(
            includes, skip_list, sources
        )
        transformed["__include__"] = []
        for source_alias, include_labels in labels_by_source_alias.items():
            assert source_alias in sources
            source_path = sources[source_alias]
            source_config_file = f"{source_path}/.lcopy.yaml"
            source_config_obj = parse_config_file(config_file=source_config_file)

            if not source_config_obj:
                logger.warning(
                    f"Failed to load config file for source '{source_alias}'"
                )
                continue

            # Transform the source config's targets recursively
            source_transformed = transform_targets_json(
                targets_json=source_config_obj.targets_json,
                sources=source_config_obj.sources,
                source_dirname=source_path,
                labels=include_labels,
                skip_list=[
                    *skip_list,
                    *[f"{source_alias}.{label}" for label in include_labels],
                ],
            )
            transformed["__include__"].append(source_transformed)


def _process_child_nodes(
    source_dirname,
    sources,
    labels,
    skip_list,
    transformed,
):
    for key, value in list(transformed.items()):
        if isinstance(value, dict) and not key.startswith("__"):
            # Skip if labels don't match
            node_labels = value.get("__labels__", [])
            if node_labels and not any(label in labels for label in node_labels):
                logger.debug(
                    f"Skipping target '{key}' - labels {node_labels} not in requested labels {labels}"
                )
                del transformed[key]
                continue

            # Handle parentheses pattern - transform (foo) to foo with __cd__ directive
            target_basenames = []
            if key.startswith("(") and key.endswith(")"):
                target_basename = key[1:-1]  # Remove parentheses

                if target_basename.startswith("<") and target_basename.endswith(">"):
                    # If it starts with < and ends with >, then find all directories in source_dirname
                    # and add them to the target_basenames
                    for path in Path(source_dirname).iterdir():
                        if path.is_dir():
                            target_basenames.append((path.name, path.name))
                else:
                    target_basenames.append((target_basename, target_basename))
            else:
                target_basenames.append((key, None))

            for target_basename, cd in target_basenames:
                target_node_json = value.copy()
                transformed[target_basename] = _transform_target_node_json(
                    cd=cd,
                    target_node_json=target_node_json,
                    source_dirname=source_dirname,
                    sources=sources,
                    labels=labels,
                    skip_list=skip_list,
                )


def _get_labels_by_source_alias(
    includes: T.List[str], skip_list: T.List[str], sources: T.Dict[str, str]
):
    """
    Get labels by source alias from the includes list.
    """
    labels_by_source_alias = defaultdict(list)

    for include in includes:
        parts = include.split(".")

        source_alias = parts[0]
        if source_alias not in sources:
            logger.warning(f"Source alias '{source_alias}' not found in sources")
            continue

        if len(parts) == 1:
            if source_alias in skip_list:
                logger.debug(f"Skipping source alias '{source_alias}' as per skip list")
                continue

        labels = labels_by_source_alias[source_alias]
        for label in parts[1:]:
            if f"{source_alias}.{label}" in skip_list:
                logger.debug(f"Skipping source alias '{source_alias}' as per skip list")
                continue
            if label not in labels:
                labels.append(label)

    return labels_by_source_alias
