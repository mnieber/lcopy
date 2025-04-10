#!/usr/bin/env python3
"""
lcopy - A tool for copying files based on configuration
"""

import argparse
import logging
import sys

from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.files.actions.copy_files import copy_files
from lcopy.files.actions.purge_files import purge_files
from lcopy.runtime.actions.parse_options_file import parse_options_file
from lcopy.runtime.rules.get_ignore_patterns import get_ignore_patterns

logger = logging.getLogger(__name__)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="lcopy - A tool for copying files based on configuration"
    )
    parser.add_argument("--options", required=True, help="Path to options file")

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

    # Listlabels command
    listlabels_parser = subparsers.add_parser(
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

    # Parse the options file
    options = None
    if hasattr(args, "options") and args.options:
        logger.info(f"Parsing options file: {args.options}")
        options = parse_options_file(args.options)

    if args.command == "copy":
        logger.info("Running copy command")

        # Override dry_run option from command line if specified
        if hasattr(args, "dry_run") and args.dry_run:
            options.dry_run = True
            logger.info("Dry run mode enabled from command line")

        # Parse each config file specified in options
        # parse_config_file will handle the target node parsing internally
        configs = []
        config_file_skip_list = []
        for config_fn in options.config_fns:
            config_list = parse_config_file(
                config_file=config_fn,
                labels=options.labels,
                config_file_skip_list=config_file_skip_list,
                ignore_patterns=get_ignore_patterns(
                    options.default_ignore, options.extra_ignore
                ),
            )
            configs.extend(config_list)

        # Collect all target nodes from the configs
        target_nodes = []
        for config in configs:
            target_nodes.extend(config.target_nodes)

        # Copy the files
        copied_files = copy_files(
            destination=options.destination,
            target_nodes=target_nodes,
            overwrite=options.conflict,
            dry_run=options.dry_run,
        )

        # Purge files if enabled
        if options.purge:
            purge_files(
                destination=options.destination,
                files_to_keep=copied_files,
                dry_run=options.dry_run,
            )

        # Output summary of copy operation
        print(
            f"{'Would copy' if options.dry_run else 'Copied'} {len(copied_files)} files to {options.destination}"
        )
        if options.verbose > 0:
            for file in copied_files:
                print(f"  {file}")

    elif args.command == "listlabels":
        logger.info("Running listlabels command")
        from lcopy.configs.rules.get_list_of_labels import get_list_of_labels

        # Parse config files and extract labels
        all_labels = set()
        for config_fn in options.config_fns:
            labels = get_list_of_labels(config_file=config_fn)
            all_labels.update(labels)

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
