from dataclassy import dataclass
import typing as T

if T.TYPE_CHECKING:
    from .config_node import ConfigNode


@dataclass
class RootConfigNode:
    """
    Root node of the configuration tree.

    Each root node represents a labeled section in the configuration file.
    """

    source_path: str
    label: str  # Label identifying this configuration section (e.g., "use-scenarios")
    child_nodes: T.List["ConfigNode"] = []  # Child configuration nodes
