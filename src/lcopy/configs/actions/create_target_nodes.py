import logging
import typing as T

from lcopy.configs.actions.create_target_node import create_target_node
from lcopy.configs.models.target_node import TargetNode

logger = logging.getLogger(__name__)


def create_target_nodes(
    targets_json: dict,
    ignore_patterns: T.List[str],
) -> T.List[TargetNode]:
    target_nodes = []

    if not targets_json:
        logger.debug("No files data found in config")
        return target_nodes

    for target_basename, target_node_json in targets_json.items():
        if target_basename.startswith("__"):
            continue

        target_nodes.append(
            create_target_node(
                relative_target_dir=target_basename,
                target_node_json=target_node_json,
                ignore_patterns=ignore_patterns,
            )
        )

    return target_nodes
