import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable, Set


class FileCopier:
    def __init__(self, destination: str, dry_run: bool = False):
        self.destination = Path(destination)
        self.dry_run = dry_run
        self.copied_files = []
        self.skipped_files = []
        self.purged_files = []
        self.purged_dirs = []
        self.errors = []

    def copy_files(
        self,
        mapping: Dict[Path, Path],
        conflict_strategy: str = "overwrite",
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        purge: bool = False,
    ):
        """
        Copy files according to the provided mapping

        Args:
            mapping: Dict mapping source paths to target paths (relative to destination)
            conflict_strategy: How to handle conflicts ('overwrite', 'skip', 'prompt')
            progress_callback: Callback function for progress updates
            purge: Whether to remove files in destination that were not copied
        """
        total_files = len(mapping)

        # Create set of all target files for purging
        if purge and not self.dry_run:
            existing_files = self._get_all_files_in_target()
        else:
            existing_files = set()

        # Perform the copy operations
        for idx, (source, rel_target) in enumerate(mapping.items()):
            try:
                # Calculate absolute target path
                target = self.destination / rel_target

                # Ensure target directory exists
                target.parent.mkdir(parents=True, exist_ok=True)

                # Check for conflicts
                if target.exists():
                    if conflict_strategy == "skip":
                        self.skipped_files.append((source, target))
                        continue
                    elif conflict_strategy == "prompt":
                        # In a real implementation, this would prompt the user
                        # For simplicity, we'll just overwrite
                        pass

                # Report progress
                if progress_callback:
                    progress_callback(str(source), idx + 1, total_files)

                if not self.dry_run:
                    # Perform the copy
                    shutil.copy2(source, target)

                    # Remove from existing files list if it's there
                    if purge and target in existing_files:
                        existing_files.remove(target)

                self.copied_files.append((source, target))

            except Exception as e:
                self.errors.append((source, str(e)))

        # Purge remaining files and empty directories if requested
        if purge and not self.dry_run:
            self._purge_files_and_dirs(existing_files)

    def _get_all_files_in_target(self) -> Set[Path]:
        """Get a set of all files in the destination directory"""
        if not self.destination.exists():
            return set()

        result = set()
        for root, _, files in os.walk(self.destination):
            for file in files:
                result.add(Path(root) / file)

        return result

    def _purge_files_and_dirs(self, files_to_purge: Set[Path]):
        """
        Remove files and empty directories that weren't copied

        Args:
            files_to_purge: Set of file paths to remove
        """
        # Remove files
        for file_path in files_to_purge:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.purged_files.append(file_path)
            except Exception as e:
                self.errors.append((file_path, f"Failed to purge: {str(e)}"))

        # Find and remove empty directories (bottom-up)
        dirs_to_check = set()
        for file_path in files_to_purge:
            dirs_to_check.add(file_path.parent)

        # Keep removing empty directories until no more can be removed
        # We need to sort in reverse to ensure we process deepest directories first
        while dirs_to_check:
            # Get a sorted list of directories to check (deepest first)
            sorted_dirs = sorted(dirs_to_check, key=lambda p: len(str(p)), reverse=True)
            dirs_to_check = set()

            for dir_path in sorted_dirs:
                # Skip if this isn't inside our destination
                if not dir_path.is_relative_to(self.destination):
                    continue

                # Skip if it's the destination itself
                if dir_path == self.destination:
                    continue

                try:
                    # Check if directory is empty
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        # Remove empty directory
                        dir_path.rmdir()
                        self.purged_dirs.append(dir_path)
                        # Add parent to check next
                        dirs_to_check.add(dir_path.parent)
                except Exception as e:
                    self.errors.append(
                        (dir_path, f"Failed to purge directory: {str(e)}")
                    )

    def get_summary(self):
        """Get summary of the copy operation"""
        return {
            "copied": len(self.copied_files),
            "skipped": len(self.skipped_files),
            "purged_files": len(self.purged_files),
            "purged_dirs": len(self.purged_dirs),
            "errors": len(self.errors),
            "error_details": self.errors,
        }
