import shutil
from pathlib import Path
from typing import Dict, Optional, Callable


class FileCopier:
    def __init__(self, destination: str, dry_run: bool = False):
        self.destination = Path(destination)
        self.dry_run = dry_run
        self.copied_files = []
        self.skipped_files = []
        self.errors = []

    def copy_files(
        self,
        mapping: Dict[Path, Path],
        conflict_strategy: str = "overwrite",
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Copy files according to the provided mapping

        Args:
            mapping: Dict mapping source paths to target paths (relative to destination)
            conflict_strategy: How to handle conflicts ('overwrite', 'skip', 'prompt')
            progress_callback: Callback function for progress updates
        """
        total_files = len(mapping)
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

                self.copied_files.append((source, target))

            except Exception as e:
                self.errors.append((source, str(e)))

    def get_summary(self):
        """Get summary of the copy operation"""
        return {
            "copied": len(self.copied_files),
            "skipped": len(self.skipped_files),
            "errors": len(self.errors),
            "error_details": self.errors,
        }
