import click
from pathlib import Path
import yaml



def load_options_file(ctx, param, value):
    """
    Load options from a YAML file and add them to the Click context.
    This function is used as a callback for the --options parameter.
    """
    if not value:
        return None

    try:
        # Convert value to Path for better path operations
        options_file_path = Path(value)
        options_dir = options_file_path.parent.absolute()

        with open(options_file_path, "r") as f:
            options = yaml.safe_load(f)

        if not isinstance(options, dict):
            raise click.BadParameter(
                f"Options file {value} must contain a YAML dictionary"
            )

        # Make config paths absolute if they're relative
        if "config" in options and options["config"]:
            # Handle both single string and list configurations
            if isinstance(options["config"], str):
                config_path = Path(options["config"])
                if not config_path.is_absolute():
                    options["config"] = str(options_dir / config_path)
            elif isinstance(options["config"], list):
                for i, config_file in enumerate(options["config"]):
                    config_path = Path(config_file)
                    if not config_path.is_absolute():
                        options["config"][i] = str(options_dir / config_path)

        # Store the options in the context for later access
        ctx.obj = ctx.obj or {}
        ctx.obj["options_file"] = options

        return value
    except FileNotFoundError:
        raise click.BadParameter(f"Options file {value} not found")
    except yaml.YAMLError as e:
        raise click.BadParameter(f"Invalid YAML in options file {value}: {e}")


def get_option(ctx, option_name, option_value):
    """
    Get option value from options file if not provided on command line.
    Command line values take precedence over options file values.
    """
    # If the value is provided on the command line, use it
    has_option = bool(option_value)
    if not has_option:
        if option_name == "config" and option_value == tuple():
            has_option = False

    if has_option:
        return option_value

    # Otherwise, try to get it from the options file
    options = ctx.obj.get("options_file", {}) if ctx.obj else {}
    return options.get(option_name)
