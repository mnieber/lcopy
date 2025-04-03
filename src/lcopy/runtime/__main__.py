#!/usr/bin/env python3
"""
lcopy - A file copying tool with advanced configuration options

This tool copies files based on configuration files that specify source and target
directory patterns, with support for regex matching and variable extraction.
"""

import os
import sys
import argparse
from typing import List

from lcopy.options.actions.parse_options_file import parse_options_file
from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.filemaps.models.filemap_node import FilemapNode
from lcopy.configs.actions.process_config import process_config
from lcopy.filemaps.actions.copy_files import copy_files


def main():
    """Main entry point for the lcopy tool."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="lcopy - A file copying tool with advanced configuration"
    )
    parser.add_argument("options_file", help="Path to the options YAML file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual copying)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    try:
        # Parse the options file
        print(f"Reading options file: {args.options_file}")
        options = parse_options_file(args.options_file)

        # Override options with command-line arguments
        if args.dry_run:
            options.dry_run = True
        if args.verbose:
            options.verbose = True

        # Print summary of options
        print(f"Destination directory: {options.destination}")
        print(f"Labels: {', '.join(options.labels)}")
        print(f"Conflict resolution: {options.conflict}")
        print(f"Dry run: {'Yes' if options.dry_run else 'No'}")
        print(f"Verbose: {'Yes' if options.verbose else 'No'}")
        print(f"Purge: {'Yes' if options.purge else 'No'}")

        # Parse config files
        config_list = []
        for config_file in options.configs:
            print(f"Reading config file: {config_file}")
            configs = parse_config_file(config_file, options)
            config_list.extend(configs)

        # Create an empty file map tree
        file_map_tree: List[FilemapNode] = []

        # Process each config
        options_dir = os.path.dirname(os.path.abspath(args.options_file))
        for root_config in config_list:
            print(f"Processing config section: {root_config.label}")
            for config_node in root_config.child_nodes:
                process_config(
                    config=config_node,
                    file_map_tree=file_map_tree,
                    current_dir=options_dir,
                    base_target_dir=os.path.join(
                        options.destination, root_config.label
                    ),
                    options=options,
                )

        # Copy files
        if not file_map_tree:
            print("No files to copy.")
            return 0

        print(f"{'Would copy' if options.dry_run else 'Copying'} files...")
        copied_files = copy_files(file_map_tree, options)

        # Print summary
        if options.verbose:
            print("\nCopied files:")
            for file in copied_files:
                print(f"  {file}")

        print(
            f"\n{'Would have copied' if options.dry_run else 'Copied'} {len(copied_files)} files."
        )

        # Handle purge if enabled
        if options.purge and not options.dry_run:
            # TODO: Implement purge functionality
            print("Purge functionality not implemented yet.")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if options.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
