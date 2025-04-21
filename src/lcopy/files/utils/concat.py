#!/usr/bin/env python3
import argparse
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_DIRS = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
]


DEFAULT_EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.exe",
    "*.obj",
    "*.o",
    "*.a",
    "*.lib",
    "*.egg",
    "*.egg-info",
    "*.whl",
    "*.csv",
    "*.pickle",
    "*.pkl",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.log",
    "*.mp4",
    "*.mov",
    "*.avi",
    "*.mpg",
    "*.mpeg",
    "*.pdf",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.tif",
    "*.tiff",
    "*.bmp",
    "*.ico",
    "*.svg",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
]


def concatenate_directory(
    dirname, output_file, exclude_dirs=None, exclude_patterns=None
):
    """
    Recursively concatenate all files in a directory into a single file.

    Args:
        dirname (str): Directory to concatenate
        output_file (str): Output file path
        exclude_dirs (list): List of directory names to exclude
        exclude_patterns (list): List of file patterns to exclude (e.g., "*.pyc")
    """
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS

    root_path = Path(dirname).resolve()

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Count total files for progress tracking
        total_files = 0
        included_files = 0

        # First pass to count files
        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            total_files += len(files)

        logger.info(f"Found {total_files} total files in {root_path}")

        # Second pass to concatenate files
        for root, dirs, files in os.walk(root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # Process each file
            for file in sorted(files):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_path)

                # Skip files matching exclude patterns
                if any(file_path.match(pattern) for pattern in exclude_patterns):
                    continue

                # Try to read the file as text
                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()

                    # Write file header and content
                    outfile.write(f"\n\n{'=' * 80}\n")
                    outfile.write(f"=== FILE: {rel_path} ===\n")
                    outfile.write(f"{'=' * 80}\n\n")
                    outfile.write(content)

                    included_files += 1
                    if included_files % 10 == 0:
                        logger.info(
                            f"Processed {included_files}/{total_files} files..."
                        )

                except UnicodeDecodeError:
                    logger.info(f"Skipping binary file: {rel_path}")
                except Exception as e:
                    logger.info(f"Error processing {rel_path}: {e}")

    logger.info(f"\nConcatenation complete!")
    logger.info(
        f"Included {included_files} out of {total_files} files in {output_file}"
    )
    logger.info(
        f"Output file size: {os.path.getsize(output_file) / (1024 * 1024):.2f} MB"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Concatenate all files in a directory into a single file"
    )
    parser.add_argument("dirname", help="Directory to concatenate")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--include-only",
        help='Only include files with these extensions (comma separated, e.g. ".py,.md")',
    )
    parser.add_argument(
        "--exclude-dirs", help="Additional directories to exclude (comma separated)"
    )
    parser.add_argument(
        "--exclude-patterns",
        help="Additional file patterns to exclude (comma separated)",
    )

    args = parser.parse_args()

    # Process exclude directories
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    if args.exclude_dirs:
        exclude_dirs.extend(args.exclude_dirs.split(","))

    # Process exclude patterns
    exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.copy()

    if args.exclude_patterns:
        exclude_patterns.extend(args.exclude_patterns.split(","))

    # Handle include-only parameter
    if args.include_only:
        extensions = args.include_only.split(",")
        # Override exclude patterns to include only files with specified extensions
        exclude_patterns = [f"*{ext}" for ext in extensions]
        # Negate the patterns to exclude everything EXCEPT these patterns
        include_patterns = exclude_patterns
        exclude_patterns = ["*"]  # Exclude everything by default
        for pattern in include_patterns:
            # Create a pattern that matches everything EXCEPT the include patterns
            exclude_patterns.append(f"!{pattern}")

    concatenate_directory(args.dirname, args.output, exclude_dirs, exclude_patterns)


if __name__ == "__main__":
    main()
