import os
import shutil
from typing import List, Optional

from filemaps.models.filemap_node import FilemapNode
from options.models.options import Options


def copy_files(
    file_map_tree: List[FilemapNode], options: Optional[Options] = None
) -> List[str]:
    """
    Copy files according to the file map tree.

    This function traverses the file map tree and copies files from source to target
    directories. It respects the options for dry_run, conflict resolution, etc.

    Args:
        file_map_tree: List of filemap nodes defining the files to copy
        options: Optional Options object with configuration (dry_run, conflict, etc.)

    Returns:
        List[str]: List of copied file paths (relative to destination)

    Raises:
        OSError: If there's an issue creating directories or copying files
    """
    copied_files = []

    # Traverse the file map tree
    for node in file_map_tree:
        # Process this node
        node_copied_files = _process_node(node, options)
        copied_files.extend(node_copied_files)

        # Process child nodes recursively
        if node.child_nodes:
            child_copied_files = copy_files(node.child_nodes, options)
            copied_files.extend(child_copied_files)

    return copied_files


def _process_node(node: FilemapNode, options: Optional[Options] = None) -> List[str]:
    """
    Process a single filemap node, copying its files.

    Args:
        node: The filemap node to process
        options: Optional Options object with configuration

    Returns:
        List[str]: List of copied file paths (relative to destination)
    """
    copied_files = []

    # Skip if source path doesn't exist
    if not os.path.exists(node.source_path):
        return copied_files

    # Create target directory if it doesn't exist
    if not os.path.exists(node.target_path):
        if options and options.verbose:
            print(f"Creating directory: {node.target_path}")

        if not (options and options.dry_run):
            os.makedirs(node.target_path, exist_ok=True)

    # Copy each file
    for filename in node.filenames:
        source_file = os.path.join(node.source_path, filename)
        target_file = os.path.join(node.target_path, filename)

        # Skip if source file doesn't exist
        if not os.path.exists(source_file):
            if options and options.verbose:
                print(f"Source file not found, skipping: {source_file}")
            continue

        # Handle file conflicts
        if os.path.exists(target_file):
            conflict_resolved = _handle_conflict(source_file, target_file, options)
            if not conflict_resolved:
                continue  # Skip this file if conflict wasn't resolved

        # Create target subdirectories if needed
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            if options and options.verbose:
                print(f"Creating directory: {target_dir}")

            if not (options and options.dry_run):
                os.makedirs(target_dir, exist_ok=True)

        # Copy the file
        if options and options.verbose:
            print(f"Copying: {source_file} -> {target_file}")

        if not (options and options.dry_run):
            shutil.copy2(source_file, target_file)  # copy2 preserves metadata

        # Add to list of copied files
        copied_files.append(
            os.path.relpath(target_file, options.destination if options else "")
        )

    return copied_files


def _handle_conflict(
    source_file: str, target_file: str, options: Optional[Options] = None
) -> bool:
    """
    Handle conflicts when a target file already exists.

    Args:
        source_file: Path to the source file
        target_file: Path to the target file
        options: Optional Options object with conflict resolution strategy

    Returns:
        bool: True if the conflict was resolved (file should be copied), False otherwise
    """
    # Default conflict strategy if options not provided
    conflict_strategy = "prompt"
    if options and options.conflict:
        conflict_strategy = options.conflict

    # Handle conflict based on strategy
    if conflict_strategy == "overwrite":
        return True  # Always overwrite

    elif conflict_strategy == "skip":
        if options and options.verbose:
            print(f"File exists, skipping: {target_file}")
        return False  # Skip copying

    elif conflict_strategy == "prompt":
        if options and options.dry_run:
            # In dry run mode, just report the conflict
            print(f"File exists (would prompt in actual run): {target_file}")
            return True

        # Prompt the user for action
        response = (
            input(f"File already exists: {target_file}\nOverwrite? (y/n): ")
            .lower()
            .strip()
        )
        return response.startswith("y")

    # Unknown strategy, default to skipping
    return False
