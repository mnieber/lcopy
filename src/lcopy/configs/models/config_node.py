from dataclassy import dataclass
import typing as T


@dataclass
class ConfigNode:
    # The dirname_pattern indicates a subdirectory of the destination directory.
    #
    # However, there is a special case where the dirname is a regex pattern that
    # is enclosed in brackets and which contains a variable part that is in square
    # brackets such as /some/path/[var]/subdir. In that case, the dirname is
    # interpreted as a relative path to the source directory and the variable part is
    # replaced with a wildcard for glob matching. The match for the wildcard is then
    # used to create the target subdirectory in the destination directory, whereas
    # the full matching path is used as the new source directory for any child nodes.
    source_path: str
    dirname_pattern: str
    filename_patterns: T.List[str]
    child_nodes: T.List["ConfigNode"] = []
