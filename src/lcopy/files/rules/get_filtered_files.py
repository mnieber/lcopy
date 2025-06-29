import fnmatch
import logging
import os
import typing as T

from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def get_filtered_files(
    files: T.List[str],
    source_dirname: str,
    ignore_patterns: T.List[str],
    exclude_patterns: T.List[str],
) -> T.List[str]:
    if not files:
        return []

    filtered_files = list(files)

    # Filter out excluded files
    if exclude_patterns:
        filtered_files = _filter_by_exclude_patterns(
            filtered_files, source_dirname, exclude_patterns
        )

    # Filter out ignored files
    if ignore_patterns:
        filtered_files = _filter_by_ignore_patterns(filtered_files, ignore_patterns)

    logger.debug(f"Filtered {len(files)} files to {len(filtered_files)} files")
    return [normalize_path(f) for f in filtered_files]


def _filter_by_exclude_patterns(
    files: T.List[str], source_dirname: str, exclude_patterns: T.List[str]
) -> T.List[str]:
    result = []

    for file_path in files:
        # Get the path relative to source_dirname
        rel_path = os.path.relpath(file_path, source_dirname)

        # Check if the file matches any exclude pattern
        exclude = False
        for pattern in exclude_patterns:
            # Make pattern relative to source_dirname
            if fnmatch.fnmatch(rel_path, pattern):
                logger.debug(f"Excluding {file_path} (matches pattern '{pattern}')")
                exclude = True
                break

        if not exclude:
            result.append(file_path)

    return result


def _filter_by_ignore_patterns(
    files: T.List[str], ignore_patterns: T.List[str]
) -> T.List[str]:
    result = []

    for file_path in files:
        # Check if the file matches any ignore pattern
        ignore = False
        for pattern in ignore_patterns:
            if _matches_ignore_pattern(file_path, pattern):
                logger.debug(f"Ignoring {file_path} (matches pattern '{pattern}')")
                ignore = True
                break

        if not ignore:
            result.append(file_path)

    return result


def _matches_ignore_pattern(file_path: str, pattern: str) -> bool:
    # Convert pattern to absolute path if it starts with /
    if pattern.startswith("/"):
        pattern = pattern[1:]
        # Match from the beginning of the path
        return fnmatch.fnmatch(os.path.basename(file_path), pattern)

    # Handle directory-specific patterns (ending with /)
    if pattern.endswith("/"):
        pattern = pattern[:-1]
        return os.path.isdir(file_path) and fnmatch.fnmatch(
            os.path.basename(file_path), pattern
        )

    # Handle patterns with wildcards
    if "*" in pattern or "?" in pattern or "[" in pattern:
        return fnmatch.fnmatch(os.path.basename(file_path), pattern)

    # Handle exact matches
    return os.path.basename(file_path) == pattern
