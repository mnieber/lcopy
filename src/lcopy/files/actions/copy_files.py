import logging
import os
import shutil
import typing as T

from lcopy.configs.models.target_node import TargetNode
from lcopy.files.rules.get_filtered_files import get_filtered_files
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def copy_files(
    destination: str,
    target_nodes: T.List[TargetNode],
    overwrite: str = "skip",
    ignore_patterns: T.List[str] = None,
    dry_run: bool = False,
) -> T.List[str]:
    # Initialize the list of copied files
    copied_files = []

    if not target_nodes:
        logger.warning("No target nodes provided")
        return copied_files

    if not destination:
        logger.error("No destination directory provided")
        return copied_files

    # Normalize destination path
    destination = normalize_path(destination)

    # Create destination directory if it doesn't exist
    if not dry_run and not os.path.exists(destination):
        logger.info(f"Creating destination directory: {destination}")
        os.makedirs(destination, exist_ok=True)

    # Process each target node
    for target_node in target_nodes:
        _process_target_node(
            target_node=target_node,
            destination=destination,
            base_destination=destination,
            copied_files=copied_files,
            overwrite=overwrite,
            ignore_patterns=ignore_patterns,
            dry_run=dry_run,
        )

    logger.info(f"Copied {len(copied_files)} files to {destination}")
    return copied_files


def _process_target_node(
    target_node: TargetNode,
    destination: str,
    base_destination: str,
    copied_files: T.List[str],
    overwrite: str,
    ignore_patterns: T.List[str],
    dry_run: bool,
) -> None:
    # Create target directory path
    target_dir = os.path.join(destination, target_node.target_basename)

    # Ensure target directory exists
    if not dry_run and not os.path.exists(target_dir):
        logger.info(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)

    # Extract exclude patterns (patterns starting with !)
    exclude_patterns = []
    include_patterns = []
    for pattern in target_node.filename_patterns:
        if pattern.startswith("!"):
            exclude_patterns.append(pattern[1:])  # Remove the ! prefix
        else:
            include_patterns.append(pattern)

    # Get files to copy (filtered by patterns)
    if include_patterns:
        # Get all files that match the include patterns
        all_files = []
        for pattern in include_patterns:
            # Join source directory with pattern
            full_pattern = normalize_path(pattern, base_path=target_node.source_dirname)
            # Expand glob pattern
            matching_files = [f for f in _expand_glob_pattern(full_pattern)]
            all_files.extend(matching_files)

        # Filter files
        filtered_files = get_filtered_files(
            files=all_files,
            source_dirname=target_node.source_dirname,
            ignore_patterns=ignore_patterns or [],
            exclude_patterns=exclude_patterns,
        )

        # Copy each file
        for src_file in filtered_files:
            # Determine destination filename
            rel_path = os.path.relpath(src_file, target_node.source_dirname)
            dest_file = normalize_path(os.path.basename(rel_path), base_path=target_dir)

            # Copy the file
            if _copy_file(src_file, dest_file, overwrite, dry_run):
                if os.path.isdir(dest_file):
                    # If it's a directory, add the entire directory to copied_files
                    for root, _, files in os.walk(dest_file):
                        for file in files:
                            copied_files.append(os.path.join(root, file))
                else:
                    # If it's a file, add the file to copied_files
                    copied_files.append(dest_file)

    # Process child nodes
    for child_node in target_node.child_nodes:
        _process_target_node(
            target_node=child_node,
            destination=target_dir,
            base_destination=base_destination,
            copied_files=copied_files,
            overwrite=overwrite,
            ignore_patterns=ignore_patterns,
            dry_run=dry_run,
        )


def _expand_glob_pattern(pattern: str) -> T.List[str]:
    import glob

    # Handle directories (ending with /) by adding ** wildcard
    if pattern.endswith("/"):
        pattern = os.path.join(pattern, "**")

    # Expand the pattern
    return glob.glob(pattern, recursive=True)


def _copy_file(src_file: str, dest_file: str, overwrite: str, dry_run: bool) -> bool:
    # Check if destination file exists
    if os.path.exists(dest_file):
        if overwrite == "skip":
            logger.info(f"File exists, skipping: {dest_file}")
            return False
        elif overwrite == "overwrite":
            if not dry_run:
                logger.info(f"Overwriting file: {dest_file}")
            else:
                logger.info(f"Would overwrite file: {dest_file}")
        elif overwrite == "prompt" or os.path.isdir(src_file):
            # Check if we're in an interactive environment
            try:
                # Prompt user for confirmation
                response = input(f"File exists: {dest_file}. Overwrite? (y/N): ")
                if response.lower() != "y":
                    logger.info(f"Skipping file: {dest_file}")
                    return False
                logger.info(f"Overwriting file: {dest_file}")
            except (EOFError, KeyboardInterrupt):
                # Non-interactive environment fallback
                logger.warning(
                    f"File exists, prompt not supported, skipping: {dest_file}"
                )
                return False

    # Create parent directories if needed
    dest_dir = os.path.dirname(dest_file)
    if not dry_run and not os.path.exists(dest_dir):
        logger.debug(f"Creating directory: {dest_dir}")
        os.makedirs(dest_dir, exist_ok=True)

    if os.path.isdir(src_file) and os.path.exists(dest_file):
        __import__("pudb").set_trace()  # zz
        shutil.rmtree(dest_file)

    # Copy the file
    what = "file" if os.path.isfile(src_file) else "directory"
    if not dry_run:
        try:
            logger.info(f"Copying {what}: {src_file} -> {dest_file}")
            if os.path.isdir(src_file):
                __import__("pudb").set_trace()  # zz
                shutil.copytree(src_file, dest_file)
            else:
                shutil.copy2(src_file, dest_file)

            return True
        except (IOError, OSError) as e:
            logger.error(f"Error copying {what} {src_file} to {dest_file}: {e}")
            return False
    else:
        logger.info(f"Would copy {what}: {src_file} -> {dest_file}")
        return True
