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

from lcopy.runtime.actions.parse_options_file import parse_options_file
from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.filemaps.models.filemap_node import FilemapNode
from lcopy.configs.actions.process_config import process_config
from lcopy.filemaps.actions.copy_files import copy_files
from lcopy.filemaps.actions.purge_files import purge_files


def cmd_copy(args, options_file):
    """Execute the copy command with the given arguments."""
    # Parse the options file
    print(f"Reading options file: {options_file}")
    options = parse_options_file(options_file)

    # Override options with command-line arguments
    if args.dry_run:
        options.dry_run = True
    if args.verbose:
        options.verbose = True
    if args.conflict:
        options.conflict = args.conflict

    # Print summary of options
    print(f"Destination directory: {options.destination}")
    print(f"Labels: {', '.join(options.labels)}")
    print(f"Conflict resolution: {options.conflict}")
    print(f"Dry run: {'Yes' if options.dry_run else 'No'}")
    print(f"Verbose: {'Yes' if options.verbose else 'No'}")
    print(f"Purge: {'Yes' if options.purge else 'No'}")

    # Parse config files
    root_config_nodes = []
    for config_file in options.configs:
        print(f"Reading config file: {config_file}")
        configs = parse_config_file(config_file, options)
        root_config_nodes.extend(configs)

    # Create an empty file map tree
    file_map_tree: List[FilemapNode] = []

    # Process each config
    for root_config_node in root_config_nodes:
        print(f"Processing config section: {root_config_node.label}")
        for config_node in root_config_node.child_nodes:
            process_config(
                config=config_node,
                file_map_tree=file_map_tree,
                current_dir=root_config_node.source_path,
                base_target_dir=options.destination,
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
    if options.purge:
        print(
            f"{'Would purge' if options.dry_run else 'Purging'} files not in copy list..."
        )
        purged_files = purge_files(options.destination, copied_files, options)

        if options.verbose:
            print("\nPurged files:")
            for file in purged_files:
                print(f"  {file}")

        print(
            f"\n{'Would have purged' if options.dry_run else 'Purged'} {len(purged_files)} files."
        )

    return 0


def cmd_listlabels(args, options_file):
    """Execute the listlabels command with the given arguments."""

    # Parse the options file to get the config files
    print(f"Reading options file: {options_file}")
    options = parse_options_file(options_file)

    # Collect all labels from all config files
    all_labels = set()
    for config_file in options.configs:
        print(f"Reading config file: {config_file}")

        # Ensure the config file exists
        if not os.path.exists(config_file):
            print(f"Warning: Config file not found: {config_file}")
            continue

        # Read and parse the config file
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)

        # Add all top-level keys (labels) to the set
        for label in config_data.keys():
            all_labels.add(label)

    # Print the results
    if all_labels:
        print("\nAvailable labels:")
        for label in sorted(all_labels):
            # Check if this label is currently selected in the options
            is_selected = label in options.labels
            marker = "*" if is_selected else " "
            print(f" {marker} {label}")

        print("\n(*) indicates labels currently selected in the options file")
    else:
        print("No labels found in the config files.")

    return 0


def main():
    """Main entry point for the lcopy tool."""
    # Create the top-level parser with the options argument
    parser = argparse.ArgumentParser(
        description="lcopy - A file copying tool with advanced configuration"
    )

    # Add options file as a required argument before the command
    parser.add_argument(
        "--options", required=True, help="Path to the options YAML file"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Parser for the 'copy' command
    copy_parser = subparsers.add_parser(
        "copy", help="Copy files according to configuration"
    )
    copy_parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual copying)"
    )
    copy_parser.add_argument(
        "--conflict",
        choices=["overwrite", "skip", "prompt"],
        help="Conflict resolution strategy",
    )

    # Parser for the 'listlabels' command
    listlabels_parser = subparsers.add_parser(
        "listlabels", help="List available labels in config files"
    )
    assert listlabels_parser

    # Parse arguments
    args = parser.parse_args()

    # Handle case when no command is provided
    if not args.command:
        parser.print_help()
        return 0

    # Execute the appropriate command
    if args.command == "copy":
        return cmd_copy(args, args.options)
    elif args.command == "listlabels":
        return cmd_listlabels(args, args.options)
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
