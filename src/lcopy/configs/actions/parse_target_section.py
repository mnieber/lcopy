import logging
import typing as T

from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.configs.actions.parse_target_node import parse_target_node
from lcopy.configs.models.config import Config
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def parse_target_section(
    config: Config,
    skip_list: T.List[T.Tuple[str, str]],
    ignore_patterns: T.List[str],
    labels: T.List[str],
) -> None:
    """
    Parse the targets section of a config file and add the resulting target nodes
    to the config.target_nodes list.
    """
    # Load the config file again to get the targets data
    try:
        import yaml

        with open(
            normalize_path(config.source_dirname + "/" + config.source_basename), "r"
        ) as f:
            config_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error(f"Config file not found in {config.source_dirname}")
        return
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        return

    # Process each target label
    targets_data = config_data.get("targets", {})
    for label, target_data in targets_data.items():
        # Skip if not in requested labels
        if (label not in labels) or ((config.source_filename, label) in skip_list):
            logger.debug(
                f"Skipping target with label '{label}' - not in requested labels"
            )
            continue

        # Add to skip list
        skip_list.append((config.source_filename, label))

        # Process includes
        includes = target_data.get("include", [])
        if includes:
            process_includes(config, includes, skip_list, ignore_patterns)

        # Process files section
        files_data = target_data.get("files", {})
        for target_basename, target_node_json in files_data.items():
            # Parse target node
            target_nodes = parse_target_node(
                target_basename=target_basename,
                source_dirname=config.source_dirname,
                target_node_json=target_node_json,
                labels=[label],
                ignore_patterns=ignore_patterns,
            )

            # Add to config if not None
            if target_nodes:
                config.target_nodes.extend(target_nodes)


def process_includes(
    config: Config,
    includes: T.List[str],
    skip_list: T.List[T.Tuple[str, str]],
    ignore_patterns: T.List[str],
) -> None:
    """
    Process include references like "source_alias.label" by loading the
    appropriate source configs and extracting the target nodes.
    """
    for include_ref in includes:
        try:
            # Parse the include reference (format: "source_alias.label")
            source_alias, include_label = include_ref.split(".", 1)

            # Check if the source alias exists in the config
            if source_alias not in config.sources:
                logger.warning(
                    f"Source alias '{source_alias}' not found in config sources"
                )
                continue

            # Get the source config
            source_config = config.sources[source_alias]
            source_path = source_config.path

            # Load the source's config file
            source_config_file = f"{source_path}/.lcopy.yaml"
            source_config_obj = parse_config_file(config_file=source_config_file)

            if not source_config_obj:
                logger.warning(
                    f"Failed to load config file for source '{source_alias}'"
                )
                continue

            # Parse the target section of the source config
            parse_target_section(
                config=source_config_obj,
                skip_list=skip_list,
                ignore_patterns=ignore_patterns,
                labels=[include_label],  # Only process the included label
            )

            # Add the target nodes from the source config to the current config
            config.target_nodes.extend(source_config_obj.target_nodes)

            logger.debug(
                f"Included {len(source_config_obj.target_nodes)} target nodes from '{include_ref}'"
            )
        except ValueError:
            logger.warning(
                f"Invalid include reference format: '{include_ref}' (should be 'source_alias.label')"
            )
        except Exception as e:
            logger.error(f"Error processing include '{include_ref}': {e}")
