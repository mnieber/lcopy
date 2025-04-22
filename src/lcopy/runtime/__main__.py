#!/usr/bin/env python3
"""
lcopy - A tool for copying files based on configuration
"""

import argparse
import logging
import sys

from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.configs.actions.parse_target_section import parse_target_section
from lcopy.files.actions.copy_files import copy_files
from lcopy.files.actions.create_concatenated_output import create_concatenated_output
from lcopy.files.actions.purge_files import purge_files
from lcopy.files.utils.normalize_path import normalize_path
from lcopy.runtime.rules.get_ignore_patterns import get_ignore_patterns

logger = logging.getLogger(__name__)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="lcopy - A tool for copying files based on configuration"
    )
    parser.add_argument("config_file", help="Path to lcopy config file")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Copy command
    copy_parser = subparsers.add_parser(
        "copy", help="Copy files according to configuration"
    )
    copy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    copy_parser.add_argument(
        "--labels",
        nargs="+",
        help="Specific labels to process (space-separated)",
    )

    # Listlabels command
    subparsers.add_parser(
        "listlabels", help="List all available labels in config files"
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )

    return parser.parse_args()


def _setup_logging(verbosity):
    log_level = logging.WARNING
    if verbosity >= 2:
        log_level = logging.DEBUG
    elif verbosity >= 1:
        log_level = logging.INFO

    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def main():
    args = _parse_args()
    _setup_logging(args.verbose)

    # Parse the config file
    config = parse_config_file(config_file=args.config_file)

    if not config:
        logger.error(f"Failed to parse config file: {args.config_file}")
        return 1

    # Get labels from command line or config file
    labels = []
    if args.command == "copy" and hasattr(args, "labels") and args.labels:
        labels = args.labels
    elif config.options and config.options.labels:
        labels = config.options.labels

    if args.command == "copy":
        logger.info("Running copy command")

        # Override dry_run option from command line if specified
        dry_run = config.options.dry_run if config.options else False
        if hasattr(args, "dry_run") and args.dry_run:
            dry_run = True
            logger.info("Dry run mode enabled from command line")

        # Get ignore patterns
        ignore_patterns = []
        if config.options:
            ignore_patterns = get_ignore_patterns(
                config.options.default_ignore, config.options.extra_ignore
            )

        # Parse target section to get target nodes
        parse_target_section(
            config=config,
            skip_list=[],
            ignore_patterns=ignore_patterns,
            labels=labels,
        )

        if not config.target_nodes:
            logger.warning("No target nodes found")
            return 0

        # Get destination from config options
        destination = ""
        conflict = "skip"
        purge = False
        if config.options:
            destination = config.options.destination
            conflict = config.options.conflict
            purge = config.options.purge

        # Copy the files
        copied_files = copy_files(
            destination=destination,
            target_nodes=config.target_nodes,
            overwrite=conflict,
            dry_run=dry_run,
        )

        # Purge files if enabled
        if purge:
            purge_files(
                destination=destination,
                files_to_keep=copied_files,
                dry_run=dry_run,
            )

        if config.options and config.options.concatenated_output_filename:
            create_concatenated_output(
                source_dirname=normalize_path(config.options.destination),
                output_filename=config.options.concatenated_output_filename,
                dry_run=bool(config.options and config.options.dry_run),
            )

        # Output summary of copy operation
        print(
            f"{'Would copy' if dry_run else 'Copied'} {len(copied_files)} files to {destination}"
        )
        if args.verbose > 0:
            for file in copied_files:
                print(f"  {file}")

    elif args.command == "listlabels":
        logger.info("Running listlabels command")
        from lcopy.configs.rules.get_list_of_labels import get_list_of_labels

        # Parse target section first to find all labels
        ignore_patterns = []
        if config.options:
            ignore_patterns = get_ignore_patterns(
                config.options.default_ignore, config.options.extra_ignore
            )

        # Get all labels from the config file
        all_labels = get_list_of_labels(args.config_file)

        # Output labels
        print("Available labels:")
        for label in sorted(all_labels):
            print(f"  {label}")
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
