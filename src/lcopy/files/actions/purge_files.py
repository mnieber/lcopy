import os
import logging
import typing as T
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def purge_files(
    destination: str, files_to_keep: T.List[str], dry_run: bool = False
) -> None:
    if not destination:
        logger.error("No destination directory provided")
        return

    # Normalize destination path
    destination = normalize_path(destination)

    if not os.path.isdir(destination):
        logger.error(f"Destination is not a directory: {destination}")
        return

    logger.info(f"Purging files from {destination}")

    # Create a set of normalized paths to keep for faster lookups
    files_to_keep_set = set(normalize_path(path) for path in files_to_keep)

    # Walk the destination directory in bottom-up order (to handle directories properly)
    for root, dirs, files in os.walk(destination, topdown=False):
        # Process files
        for file in files:
            file_path = os.path.join(root, file)
            normalized_path = normalize_path(file_path)

            if normalized_path not in files_to_keep_set:
                if not dry_run:
                    try:
                        logger.info(f"Removing file: {file_path}")
                        os.remove(file_path)
                    except OSError as e:
                        logger.error(f"Error removing file {file_path}: {e}")
                else:
                    logger.info(f"Would remove file: {file_path}")

        # Process directories (only empty ones)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)

            # Check if directory is empty
            if not os.listdir(dir_path):
                if not dry_run:
                    try:
                        logger.info(f"Removing empty directory: {dir_path}")
                        os.rmdir(dir_path)
                    except OSError as e:
                        logger.error(f"Error removing directory {dir_path}: {e}")
                else:
                    logger.info(f"Would remove empty directory: {dir_path}")
