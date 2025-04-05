#!/usr/bin/env python3
import argparse
import logging
import sys

from lcopy.runtime.actions.parse_options_file import parse_options_file
from lcopy.configs.rules.resolve_includes import resolve_includes
from lcopy.configs.actions.parse_config_file import parse_config_file
from lcopy.configs.actions.process_config import process_config
from lcopy.filemaps.actions.copy_files import copy_files
from lcopy.filemaps.actions.purge_files import purge_files

logger = logging.getLogger(__name__)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="lcopy - A tool for copying files according to configuration files"
    )

    # Global arguments
    parser.add_argument("--options", required=True, help="Path to options file")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Copy command
    copy_parser = subparsers.add_parser(
        "copy", help="Copy files according to configuration"
    )

    # Listlabels command
    listlabels_parser = subparsers.add_parser(
        "listlabels", help="List all labels in the configuration files"
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
    logger.info(f"Parsing options file: {args.options}")
    options = parse_options_file(args.options)

    # Resolve includes in each config file
    set_of_config_files = set()
    processed_files = []
    for config_file in options.configs:
        logger.info(f"Resolving includes for config file: {config_file}")
        for resolved_config in resolve_includes(config_file, options, processed_files):
            set_of_config_files.add(resolved_config)

    # Parse all config files
    list_of_configs = []
    for config_file in set_of_config_files:
        logger.info(f"Parsing config file: {config_file}")
        config = parse_config_file(config_file)
        list_of_configs.append(config)

    __import__("pudb").set_trace()  # zz
    if args.command == "copy":
        logger.info("Starting copy operation")

        # Create empty filemap tree
        filemap_nodes = list()

        # Process each config to extend the filemap tree
        for config in list_of_configs:
            for root_config_node in config.root_config_nodes:
                # Skip config nodes that don't have a matching label
                if root_config_node.label not in options.labels:
                    logger.info(
                        f"Skipping config node with label: {root_config_node.label} - not in requested labels"
                    )
                    continue

                logger.info(
                    f"Processing config node with label: {root_config_node.label}"
                )
                process_config(
                    options.destination,
                    config,
                    filemap_nodes,
                    options.get_ignore_patterns(),
                )

        # Copy files according to the filemap
        logger.info("Copying files")
        copied_files = copy_files(filemap_nodes)

        # Optionally purge files that weren't copied
        if options.purge:
            logger.info("Purging files that weren't copied")
            purge_files(copied_files)

        logger.info("Copy operation completed successfully")

    elif args.command == "listlabels":
        logger.info("Listing all labels in configuration files")

        # Output all labels present in the target directories of the config files
        labels = set()
        for config in list_of_configs:
            # Collect all labels from root config nodes
            for root_config_node in config.root_config_nodes:
                labels.add(root_config_node.label)

        # Print the labels
        for label in sorted(labels):
            print(label)

        logger.info("Label listing completed successfully")

    else:
        print("Please specify a command. Use --help for more information.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
