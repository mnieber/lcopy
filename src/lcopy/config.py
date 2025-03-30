import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set


class LCopyConfig:
    def __init__(self):
        self.labels = {}
        self.source_dirs = []

    def add_config_from_file(self, config_file: Path):
        """Load configuration from a specified YAML file"""
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        # Store the source directory (the directory containing the config file)
        source_dir = config_file.parent.absolute()
        self.source_dirs.append(source_dir)

        # Load and parse the YAML file
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)

        # Process each label
        for label, directory_structure in config_data.items():
            if label not in self.labels:
                self.labels[label] = {}

            # Process directory structure (target structure)
            self._process_directory_structure(
                label, directory_structure, source_dir, Path()
            )

    def _process_directory_structure(self, label, structure, source_dir, current_path):
        """
        Recursively process the directory structure for a label

        Args:
            label: The label name
            structure: The directory structure at this level
            source_dir: The source directory containing the config file
            current_path: The current relative path in the target structure
        """
        for dir_name, content in structure.items():
            # Build the target path
            target_path = current_path
            if dir_name != ".":
                target_path = target_path / dir_name

            # Process content
            if isinstance(content, list):
                # This is a list of patterns
                path_key = str(target_path) if target_path != Path() else "."
                if path_key not in self.labels[label]:
                    self.labels[label][path_key] = []

                # Add patterns with source directory information
                for pattern in content:
                    self.labels[label][path_key].append(
                        {"pattern": pattern, "source_dir": source_dir}
                    )
            elif isinstance(content, dict):
                # This is a nested directory structure
                self._process_directory_structure(
                    label, content, source_dir, target_path
                )

    def get_available_labels(self) -> List[str]:
        """Get all available labels"""
        return list(self.labels.keys())

    def get_copy_mapping(
        self, selected_labels: Optional[List[str]] = None
    ) -> Dict[Path, Path]:
        """
        Get mapping of source files to target files based on selected labels.

        Args:
            selected_labels: List of label names
                          If None, all labels are included

        Returns:
            Dict mapping source paths to target paths
        """
        # If no labels specified, include all
        if selected_labels is None:
            selected_labels = self.get_available_labels()

        # Build the mapping
        mapping = {}
        excluded_paths = set()

        # Process all selected labels
        for label in selected_labels:
            if label not in self.labels:
                continue

            self._process_exclude_patterns(label, excluded_paths)
            self._process_include_patterns(label, excluded_paths, mapping)

        return mapping

    def _process_exclude_patterns(self, label: str, excluded_paths: Set[Path]):
        """
        Process all exclude patterns for a label.

        Args:
            label: The label to process
            excluded_paths: Set to populate with excluded paths
        """
        for target_dir_str, pattern_list in self.labels[label].items():
            # First pass: process exclude patterns
            for pattern_info in pattern_list:
                pattern = pattern_info["pattern"]
                source_dir = pattern_info["source_dir"]

                # Skip if not an exclude pattern
                if not pattern.startswith("!"):
                    continue

                # Remove the '!' prefix for matching
                exclude_pattern = pattern[1:]

                self._add_excluded_paths(source_dir, exclude_pattern, excluded_paths)

    def _add_excluded_paths(
        self, source_dir: Path, exclude_pattern: str, excluded_paths: Set[Path]
    ):
        """
        Add paths matching the exclude pattern to the excluded_paths set.

        Args:
            source_dir: The source directory
            exclude_pattern: Pattern to match for exclusion
            excluded_paths: Set to populate with excluded paths
        """
        # Process directory exclude patterns (no wildcards)
        if not any(c in exclude_pattern for c in ["*", "?", "["]):
            exclude_path = source_dir / exclude_pattern
            if exclude_path.is_dir():
                # Exclude all files in the directory
                for root, _, files in os.walk(exclude_path):
                    for file in files:
                        file_path = Path(root) / file
                        excluded_paths.add(file_path)
            else:
                # Exclude a single file
                excluded_paths.add(exclude_path)
        else:
            # Process wildcard exclude patterns
            for file_path in source_dir.glob(exclude_pattern):
                if file_path.is_file():
                    excluded_paths.add(file_path)

    def _process_include_patterns(
        self, label: str, excluded_paths: Set[Path], mapping: Dict[Path, Path]
    ):
        """
        Process all include patterns for a label.

        Args:
            label: The label to process
            excluded_paths: Set of paths to exclude
            mapping: Dict to populate with source->target path mappings
        """
        for target_dir_str, pattern_list in self.labels[label].items():
            # Convert string path to Path object
            target_dir = Path(target_dir_str) if target_dir_str != "." else Path()

            # Second pass: process include patterns
            for pattern_info in pattern_list:
                pattern = pattern_info["pattern"]
                source_dir = pattern_info["source_dir"]

                # Skip exclude patterns
                if pattern.startswith("!"):
                    continue

                self._add_included_paths(
                    source_dir, pattern, target_dir, excluded_paths, mapping
                )

    def _add_included_paths(
        self,
        source_dir: Path,
        pattern: str,
        target_dir: Path,
        excluded_paths: Set[Path],
        mapping: Dict[Path, Path],
    ):
        """
        Add paths matching the include pattern to the mapping.

        Args:
            source_dir: The source directory
            pattern: Pattern to match for inclusion
            target_dir: Target directory for copying
            excluded_paths: Set of paths to exclude
            mapping: Dict to populate with source->target path mappings
        """

        def add_mapping(source_path, target_path):
            if target_path.suffix == ".pyc" or "__pycache__" in target_path.parts:
                return

            if source_path not in mapping:
                mapping[source_path] = target_path

        # Process patterns with wildcards
        if any(c in pattern for c in ["*", "?", "["]):
            for file_path in source_dir.glob(pattern):
                self._process_matched_path(
                    file_path,
                    source_dir,
                    pattern,
                    target_dir,
                    excluded_paths,
                    add_mapping,
                )
        else:
            # Process literal path (no wildcards)
            source_path = source_dir / pattern
            self._process_matched_path(
                source_path,
                source_dir,
                pattern,
                target_dir,
                excluded_paths,
                add_mapping,
            )

    def _process_matched_path(
        self,
        matched_path: Path,
        source_dir: Path,
        pattern: str,
        target_dir: Path,
        excluded_paths: Set[Path],
        add_mapping_func,
    ):
        """
        Process a path that matched a pattern.

        Args:
            matched_path: The path that matched the pattern
            source_dir: The source directory
            pattern: The pattern that matched
            target_dir: Target directory for copying
            excluded_paths: Set of paths to exclude
            add_mapping_func: Function to call to add a mapping
        """
        # For files: add directly if not excluded
        if matched_path.is_file():
            if matched_path not in excluded_paths:
                add_mapping_func(matched_path, target_dir / matched_path.name)
        # For directories: add all contained files
        elif matched_path.is_dir():
            for root, _, files in os.walk(matched_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path in excluded_paths:
                        continue

                    # Preserve directory structure from the source
                    rel_path = file_path.relative_to(source_dir)
                    base_name = Path(pattern).name
                    rel_to_base = (
                        rel_path.relative_to(Path(pattern))
                        if rel_path.is_relative_to(Path(pattern))
                        else rel_path
                    )
                    add_mapping_func(file_path, target_dir / base_name / rel_to_base)
