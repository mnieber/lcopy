import logging
import os

from lcopy.files.utils.concat import concatenate_directory

logger = logging.getLogger(__name__)


def create_concatenated_output(
    source_dirname: str, output_filename: str, dry_run: bool = False
) -> None:
    if dry_run:
        logger.info(f"Would create concatenated output file at: {output_filename}")
        return

    # Make sure the directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    logger.info(f"Creating concatenated output file at: {output_filename}")
    concatenate_directory(dirname=source_dirname, output_file=output_filename)

    logger.info(f"Concatenated output created at: {output_filename}")
