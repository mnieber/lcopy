import click
from pathlib import Path

from .config import LCopyConfig
from .copier import FileCopier


@click.group()
def cli():
    """Tool for copying files based on configuration files"""


@cli.command()
@click.option(
    "--config", "-c", multiple=True, required=True, help="Configuration file to use"
)
def list_labels(config):
    """List all available labels in the specified configuration files"""
    # Load configuration
    lcopy_config = LCopyConfig()

    for config_file in config:
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
@click.option(
    "--config", "-c", multiple=True, required=True, help="Configuration file to use"
)
@click.option("--destination", "-d", required=True, help="Destination directory")
@click.option("--labels", "-l", multiple=True, help="Labels to include")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be copied without actually copying"
)
@click.option(
    "--conflict",
    type=click.Choice(["overwrite", "skip", "prompt"]),
    default="overwrite",
    help="Strategy for handling conflicts",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def copy(config, destination, labels, dry_run, conflict, verbose):
    """Copy files according to the specified labels"""
    # Load configuration
    lcopy_config = LCopyConfig()

    for config_file in config:
        try:
            lcopy_config.add_config_from_file(Path(config_file))
        except FileNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            continue

    if not lcopy_config.labels:
        click.echo("No valid configuration files found.")
        return

    # Get the copy mapping
    selected_labels = list(labels) if labels else None
    mapping = lcopy_config.get_copy_mapping(selected_labels)

    if not mapping:
        click.echo("No files to copy based on the selected labels.")
        return

    # Show what will be copied
    if verbose or dry_run:
        click.echo(f"Files to copy ({len(mapping)}):")
        for source, target in mapping.items():
            click.echo(f"  {source} -> {Path(destination) / target}")

    # Define progress callback if verbose
    def progress_callback(source, current, total):
        if verbose:
            click.echo(f"Copying {current}/{total}: {source}")

    # Perform the copy
    copier = FileCopier(destination, dry_run=dry_run)
    copier.copy_files(
        mapping,
        conflict_strategy=conflict,
        progress_callback=progress_callback if verbose else None,
    )

    # Show summary
    summary = copier.get_summary()
    if dry_run:
        click.echo(f"Dry run complete. {len(mapping)} files would be copied.")
    else:
        click.echo(
            f"Copy complete. {summary['copied']} files copied, "
            f"{summary['skipped']} skipped, {summary['errors']} errors."
        )

    if summary["errors"] and verbose:
        click.echo("Errors:")
        for source, error in summary["error_details"]:
            click.echo(f"  {source}: {error}")
