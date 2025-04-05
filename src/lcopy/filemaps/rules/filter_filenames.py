import os
import re
import glob
import logging
import typing as T

from lcopy.configs.utils.normalize_path import normalize_path


logger = logging.getLogger(__name__)


def filter_filenames(
    filename_patterns,
    source_path,
    exclude_patterns: T.List[str],
    ignore_patterns: T.List[str],
) -> T.List[str]:
    filenames = []

    # Make sure the source path exists
    if not os.path.exists(source_path):
        logger.warning(f"Source path does not exist: {source_path}")
        return filenames

    # Process each filename pattern
    for pattern in filename_patterns:
        # Skip exclude patterns (those starting with !)
        if pattern.startswith("!"):
            continue

        # Create a full pattern by joining the source path and the filename pattern
        full_pattern = os.path.join(source_path, pattern)

        # Find all files matching the pattern
        for filepath in glob.glob(full_pattern):
            # Get the filename relative to the source path
            filename = os.path.relpath(filepath, source_path)
            # Normalize the filename for comparison
            norm_filename = normalize_path(filename, None)

            # Check if the file matches any exclude patterns (relative to source path)
            # HACK !!!
            if False:
                should_exclude = False
                for exclude in exclude_patterns:
                    # Normalize the exclude pattern for comparison
                    norm_exclude = normalize_path(exclude, None)
                    if re.match(norm_exclude, norm_filename):
                        logger.debug(
                            f"Excluding file due to exclude pattern: {filename}"
                        )
                        should_exclude = True
                        break

                # Check if the file matches any ignore patterns
                for ignore in ignore_patterns:
                    # Normalize the ignore pattern for comparison
                    norm_ignore = normalize_path(ignore, None)
                    if re.match(norm_ignore, norm_filename):
                        logger.debug(f"Ignoring file due to ignore pattern: {filename}")
                        should_exclude = True
                        break

                if should_exclude:
                    continue

            # Add the filename to the list if not already present
            if filename not in filenames:
                filenames.append(filename)

    return filenames
