import logging
import os
import shutil
import typing as T

from lcopy.configs.models.target_node import TargetNode
from lcopy.files.utils.normalize_path import normalize_path

logger = logging.getLogger(__name__)


def copy_files(
    destination: str,
    target_nodes: T.List[TargetNode],
    overwrite: str = "skip",
    dry_run: bool = False,
) -> T.List[str]:
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
    elif dry_run and not os.path.exists(destination):
        logger.info(f"Would create destination directory: {destination}")

    # Process each target node
    for target_node in target_nodes:
        _process_target_node(
            target_node=target_node,
            destination=destination,
            copied_files=copied_files,
            overwrite=overwrite,
            dry_run=dry_run,
        )

    action_verb = "Would copy" if dry_run else "Copied"
    logger.info(f"{action_verb} {len(copied_files)} files to {destination}")
    return copied_files


def _process_target_node(
    target_node: TargetNode,
    destination: str,
    copied_files: T.List[str],
    overwrite: str,
    dry_run: bool,
) -> None:
    # Create target directory path based on relative_target_dir
    target_dir = destination
    if target_node.relative_target_dir:
        target_dir = os.path.join(destination, target_node.relative_target_dir)

    # Ensure target directory exists
    if not dry_run and not os.path.exists(target_dir):
        logger.info(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
    elif dry_run and not os.path.exists(target_dir):
        logger.info(f"Would create directory: {target_dir}")

    # Copy each file
    for src_file in target_node.filenames:
        # Normalize the source file path to handle any potential issues
        src_file = normalize_path(src_file)

        # Skip files that don't exist
        if not os.path.exists(src_file):
            logger.warning(f"Source file does not exist: {src_file}")
            continue

        # Determine destination filename - maintain the same basename
        basename = os.path.basename(src_file)
        dest_file = normalize_path(basename, base_path=target_dir)

        # Copy the file
        if _copy_file(src_file, dest_file, overwrite, dry_run):
            # Track the copied file
            copied_files.append(dest_file)

    # Process child nodes
    for child_node in target_node.child_nodes:
        _process_target_node(
            target_node=child_node,
            destination=target_dir,
            copied_files=copied_files,
            overwrite=overwrite,
            dry_run=dry_run,
        )


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
        elif overwrite == "prompt":
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
    elif dry_run and not os.path.exists(dest_dir):
        logger.debug(f"Would create directory: {dest_dir}")

    # Copy the file
    if not dry_run:
        try:
            logger.info(f"Copying file: {src_file} -> {dest_file}")
            shutil.copy2(src_file, dest_file)
            return True
        except (IOError, OSError) as e:
            logger.error(f"Error copying file {src_file} to {dest_file}: {e}")
            return False
    else:
        logger.info(f"Would copy file: {src_file} -> {dest_file}")
        return True
