# Welcome to Gencove's CLI documentation!

::: gencove.cli
    handler: python
    options:
        show_root_heading: false
        show_source: false
        allow_inspection: false
        show_bases: false
        members: false

Supported Python versions are 3.8 and above.

# Quickstart

## Installation

To check your default Python version, open an interactive shell and run:

```
python --version
```

To check if you have Python 3, open an interactive shell and run:

```
python3 --version
```

To install Gencove CLI Tool, open an interactive shell and run:

```
python<version> -m pip install gencove
```

If you want Gencove CLI Tool to be installed for your default Python installation, you can instead use:

```
python -m pip install gencove
```

## Using Gencove CLI Tool

To start using Gencove CLI Tool, open an interactive shell and run:

```
gencove --help
```

This will output all available commands.

::: mkdocs-click
    :module: gencove.cli
    :command: cli
    :prog_name: gencove
    :list_subcommands: true
    :depth: 0
