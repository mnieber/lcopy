import os
import yaml

from lcopy.runtime.models.options import Options


def parse_options_file(options_file: str) -> Options:
    # Ensure the options file exists
    if not os.path.exists(options_file):
        raise FileNotFoundError(f"Options file not found: {options_file}")

    # Get the directory of the options file to resolve relative paths
    options_dir = os.path.dirname(os.path.abspath(options_file))

    # Read and parse the options file
    with open(options_file, "r") as file:
        options_data = yaml.safe_load(file)

    # Resolve config file paths relative to the options file directory
    configs = options_data.get("configs", [])
    resolved_configs = []
    for config in configs:
        # If it's a relative path, resolve it relative to the options file directory
        if not os.path.isabs(config):
            config = os.path.join(options_dir, config)
        resolved_configs.append(config)

    # Resolve the destination path, expanding environment variables and home directory
    destination = options_data.get("destination", "")
    if destination:
        # Expand environment variables
        destination = os.path.expandvars(destination)
        # Expand home directory (~)
        destination = os.path.expanduser(destination)

    # Create the Options object
    options = Options(
        configs=resolved_configs,
        destination=destination,
        labels=options_data.get("labels", []),
        conflict=options_data.get("conflict", "prompt"),
        verbose=options_data.get("verbose", False),
        purge=options_data.get("purge", False),
        dry_run=options_data.get("dry_run", False),
    )

    return options
