# lcopy

A flexible file copying tool that uses YAML configuration files to define complex directory structures and file selection patterns.

## Overview

The lcopy tool allows you to copy files from source directories to a destination directory based on configurable rules. It's particularly useful for:

- Creating curated subsets of large codebases
- Organizing files from multiple sources into a unified structure
- Building documentation or example collections
- Creating filtered copies with specific file patterns

## Features

- **Pattern-based file selection** with glob patterns and inclusion/exclusion rules
- **Label-based filtering** to copy only files matching specific labels
- **Multi-source support** to include files from multiple directories
- **Flexible directory mapping** with source and destination directory transforms
- **Dry-run mode** to preview operations before execution
- **File purging** to keep destination directories clean
- **Conflict resolution** with configurable overwrite behavior
- **Concatenated output** to combine all copied files into a single file

## Installation

```bash
git clone git@github.com:mnieber/lcopy.git
pip install lcopy
```

## Quick Start

1. Create a `.lcopy.yaml` configuration file:

```yaml
options:
  destination: ./output
  conflict: overwrite

files:
  documentation:
    "docs/*.md": true
    "README.md": true
  source:
    "src/**/*.py": true
    "src/**/*.pyc": false
```

2. Run lcopy:

```bash
lcopy .lcopy.yaml
```

## Configuration File Structure

### Basic Structure

```yaml
# Optional: Global options
options:
  destination: ~/output
  conflict: skip
  dry_run: false
  purge: true

# Required: File copying rules
files:
  target-directory:
    "pattern": true/false
    subdirectory:
      "another-pattern": true
```

### Sources Section

Define external directories that can be referenced in the files section (as explained further down below):

```yaml
sources:
  ../sibling-project: sibling    # Relative path
  /absolute/path: absolute       # Absolute path
```

### Options Section

```yaml
options:
  # Destination directory (required)
  destination: ~/projects/output

  # Conflict resolution: 'skip', 'overwrite', or 'prompt'
  conflict: overwrite

  # Enable verbose output
  verbose: true

  # Remove files in destination not copied by lcopy
  purge: true

  # Preview mode - don't actually copy files
  dry_run: false

  # Use default ignore patterns (.git, __pycache__, etc.)
  default_ignore: true

  # Additional patterns to ignore
  extra_ignore:
    - "*.tmp"
    - ".custom"

  # Optional: Create concatenated output file
  concatenated_output_filename: combined_output.txt
```

### Files Section

The files section defines the directory structure and file patterns:

#### Basic File Patterns

```yaml
files:
  docs:
    "*.md": true           # Include all .md files
    "*.txt": false         # Exclude all .txt files
    "README.md": true      # Include specific file
    "temp/": false         # Exclude entire directory
```

#### Directory Mapping with `__cd__`

Change the source directory for a target node:

```yaml
files:
  output-docs:
    __cd__: documentation  # Copy from ./documentation/ instead of ./
    "*.md": true
```

#### Shorthand with Parentheses

Use parentheses as shorthand for `__cd__`:

```yaml
files:
  # These are equivalent:
  (src):
    "*.py": true

  src:
    __cd__: src
    "*.py": true
```

#### Labels for Conditional Copying

Use labels to conditionally include sections:

```yaml
files:
  development:
    __labels__: [dev, debug]
    "test/**/*.py": true

  production:
    __labels__: [prod]
    "src/**/*.py": true
    "test/": false
```

Copy only labeled sections:

```bash
lcopy .lcopy.yaml --label dev --label debug
```

#### Including External Sources

Reference external sources defined in the sources section:

```yaml
sources:
  ../shared-lib: shared

files:
  libraries:
    __include__: [shared]           # Include 'shared' without specifying any labels

  specific:
    __include__: [shared.docs]      # Include 'shared' and include files with the 'docs' label
```

#### Complex Example

```yaml
sources:
  ../backend: api
  ../frontend: ui
  /shared/utils: utils

options:
  destination: ~/project-bundle
  conflict: overwrite
  purge: true
  concatenated_output_filename: complete_source.txt

files:
  ".":
    __labels__: [bundle]

    # Core documentation
    documentation:
      "README.md": true
      "docs/**/*.md": true
      "docs/internal/": false

    # Backend code (from external source)
    backend:
      __include__: [api.production]

    # Frontend assets
    frontend:
      __include__: [ui.build, ui.assets]

    # Shared utilities
    (shared):
      __include__: [utils]
      "local-utils/**/*.py": true

    # Development files (only with dev label)
    development:
      __labels__: [dev]
      "scripts/**/*.sh": true
      "Makefile": true
```

## Command Line Usage

### Basic Usage

```bash
# Copy files using config
lcopy config.yaml

# Copy with specific labels
lcopy config.yaml --label production --label docs

# Dry run to preview
lcopy config.yaml --dry-run

# Verbose output
lcopy config.yaml -v

# List all available labels
lcopy config.yaml --list-labels
```

### Command Line Options

- `config_file` - Path to lcopy configuration file (required)
- `--label LABEL` - Label to process (can be used multiple times)
- `--dry-run` - Show what would be copied without actually copying
- `--list-labels` - List all available labels in config files
- `--print-nodes` - Debug option to print target nodes
- `-v, --verbose` - Increase verbosity (use -vv for debug level)

## Examples

### Simple Documentation Copy

```yaml
# .lcopy.yaml
options:
  destination: ./docs-export

files:
  ".":
    "README.md": true
    "docs/**/*.md": true
    "examples/**/*.py": true
    "tests/": false
```

### Multi-Project Bundle

```yaml
# .lcopy.yaml
sources:
  ../project-a: proj-a
  ../project-b: proj-b

options:
  destination: ./combined-project
  concatenated_output_filename: ./all-source.txt

files:
  project-a:
    __include__: [proj-a.src]

  project-b:
    __include__: [proj-b.src]

  shared:
    "common/**/*.py": true
```

### Conditional Development vs Production

```yaml
# .lcopy.yaml
options:
  destination: ./deployment

files:
  app:
    __labels__: [prod, dev]
    "src/**/*.py": true

  config:
    development:
      __labels__: [dev]
      "config/dev.yaml": true

    production:
      __labels__: [prod]
      "config/prod.yaml": true

  tests:
    __labels__: [dev]
    "tests/**/*.py": true
```

Usage:
```bash
# Development bundle
lcopy .lcopy.yaml --label dev

# Production bundle
lcopy .lcopy.yaml --label prod
```

## License

MIT License - see LICENSE file for details.