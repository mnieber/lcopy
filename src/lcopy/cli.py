import click
from pathlib import Path

from .config import LCopyConfig
from .copier import FileCopier
from .options import load_options_file, get_option


@click.group()
@click.option(
    "--options", callback=load_options_file, help="YAML file containing command options"
)
@click.pass_context
def cli(ctx, options):
    """Tool for copying files based on configuration files"""
    # Initialize context object if not already done
    ctx.obj = ctx.obj or {}


@cli.command()
@click.option("--config", "-c", multiple=True, help="Configuration file to use")
@click.pass_context
def list_labels(ctx, config):
    """List all available labels in the specified configuration files"""
    __import__("pudb").set_trace()  # zz

    # Get config from options file if not provided on command line
    config_files = get_option(ctx, "config", config)

    if not config_files:
        click.echo(
            "Error: No configuration files specified. Use --config or add 'config' to your options file.",
            err=True,
        )
        ctx.exit(1)

    # Load configuration
    lcopy_config = LCopyConfig()

    for config_file in config_files:
        try:
            lcopy_config.add_config_from_file(Path(config_file))
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            continue

    # Display available labels
    labels = lcopy_config.get_available_labels()
    if not labels:
        click.echo("No labels found in the specified configuration files.")
        return

    click.echo("Available labels:")
    for label in labels:
        click.echo(f"  - {label}")


@cli.command()
@click.option("--config", "-c", multiple=True, help="Configuration file to use")
@click.option("--destination", "-d", help="Destination directory")
@click.option("--labels", "-l", multiple=True, help="Labels to include")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be copied without actually copying"
)
@click.option(
    "--conflict",
    type=click.Choice(["overwrite", "skip", "prompt"]),
    default=None,
    help="Strategy for handling conflicts",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--purge", is_flag=True, help="Remove files in destination that were not copied"
)
@click.pass_context
def copy(ctx, config, destination, labels, dry_run, conflict, verbose, purge):
    """Copy files according to the specified labels"""

    # Get options from options file if not provided on command line
    config_files = get_option(ctx, "config", config)
    destination_dir = get_option(ctx, "destination", destination)
    label_list = get_option(ctx, "labels", labels)
    dry_run_option = get_option(ctx, "dry_run", dry_run)
    conflict_strategy = (
        get_option(ctx, "conflict", conflict) or "overwrite"
    )  # Default if not specified
    verbose_option = get_option(ctx, "verbose", verbose)
    purge_option = get_option(ctx, "purge", purge)

    # Validate required options
    if not config_files:
        click.echo(
            "Error: No configuration files specified. Use --config or add 'config' to your options file.",
            err=True,
        )
        ctx.exit(1)

    if not destination_dir:
        click.echo(
            "Error: No destination directory specified. Use --destination or add 'destination' to your options file.",
            err=True,
        )
        ctx.exit(1)

    # Load configuration
    lcopy_config = LCopyConfig()

    for config_file in config_files:
        try:
            lcopy_config.add_config_from_file(Path(config_file))
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            continue

    if not lcopy_config.labels:
        click.echo("No valid configuration files found.")
        return

    # Get the copy mapping
    selected_labels = list(label_list) if label_list else None
    __import__("pudb").set_trace()  # zz
    mapping = lcopy_config.get_copy_mapping(selected_labels)

    if not mapping:
        click.echo("No files to copy based on the selected labels.")
        return

    # Show what will be copied
    if verbose_option or dry_run_option:
        click.echo(f"Files to copy ({len(mapping)}):")
        for source, target in mapping.items():
            click.echo(f"  {source} -> {Path(destination_dir) / target}")

    # Define progress callback if verbose
    def progress_callback(source, current, total):
        if verbose_option:
            click.echo(f"Copying {current}/{total}: {source}")

    # Perform the copy
    copier = FileCopier(destination_dir, dry_run=dry_run_option)
    copier.copy_files(
        mapping,
        conflict_strategy=conflict_strategy,
        progress_callback=progress_callback if verbose_option else None,
        purge=purge_option,
    )

    # Show summary
    summary = copier.get_summary()
    if dry_run_option:
        if purge_option:
            click.echo(
                f"Dry run complete. {len(mapping)} files would be copied, files in destination not in the copied set would be purged."
            )
        else:
            click.echo(f"Dry run complete. {len(mapping)} files would be copied.")
    else:
        purge_msg = ""
        if purge_option:
            purge_msg = f", {summary['purged_files']} files purged, {summary['purged_dirs']} directories purged"

        click.echo(
            f"Copy complete. {summary['copied']} files copied, "
            f"{summary['skipped']} skipped{purge_msg}, {summary['errors']} errors."
        )

    if summary["errors"] and verbose_option:
        click.echo("Errors:")
        for source, error in summary["error_details"]:
            click.echo(f"  {source}: {error}")
