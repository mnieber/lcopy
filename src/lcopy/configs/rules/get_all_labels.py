import yaml
import os


def get_all_labels(options):
    # Collect all labels from all config files
    all_labels = set()
    for config_file in options.configs:
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

    return all_labels
