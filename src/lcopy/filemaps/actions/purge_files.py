import os
from typing import List, Optional

from lcopy.runtime.models.options import Options


def purge_files(
    destination_dir: str, copied_files: List[str], options: Optional[Options] = None
) -> List[str]:
    if not os.path.exists(destination_dir):
        return []

    purged_files = []

    # Walk the destination directory
    for root, dirs, files in os.walk(destination_dir, topdown=False):
        # Process files in current directory
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))

            # If the file wasn't copied, remove it
            if file_path not in copied_files:
                if options and options.verbose:
                    print(f"Purging file: {file_path}")

                if not (options and options.dry_run):
                    os.remove(file_path)

                purged_files.append(file_path)

        # Remove empty directories (only if no files or subdirectories remain)
        if not os.listdir(root) and root != destination_dir:
            if options and options.verbose:
                print(f"Removing empty directory: {root}")

            if not (options and options.dry_run):
                os.rmdir(root)

    return purged_files
