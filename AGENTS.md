# Repository Guidelines

## Project Structure & Module Organization

The CLI logic resides in the `gencove/` package.
- `gencove/command/`: Contains the implementation of CLI commands, organized by resource (e.g., `projects/`, `samples/`, `upload/`). Each command typically has its own directory with a `cli.py` (Click definition) and `main.py` (logic).
- `gencove/tests/`: Mirrors the structure of `gencove/command/` and contains unit and integration tests. VCR cassettes for tests are stored in `vcr/` subdirectories within each test package.
- `tox.ini`: Orchestrates testing environments and linters.
- `pyproject.toml`: Manages dependencies and build configuration using `uv`.

## Local Setup & Environment

This project uses [uv](https://docs.astral.sh/uv/guides/install-python/) for Python management.

1.  **Install dependencies**:
    ```bash
    uv sync --extra dev --extra test
    ```

2.  **Install pre-commit hooks**:
    ```bash
    uv run pre-commit install
    ```

## Build, Test, and Development Commands

- **Run all tests and linters**:
  ```bash
  tox
  ```

- **Run specific test environment** (e.g., Python 3.9 with API key):
  ```bash
  tox -e py39-api_key
  ```

- **Run a specific test case**:
  Pass arguments after `--` to filter tests.
  ```bash
  tox -e py39-api_key -- gencove/tests/test_utils.py::test_is_valid_uuid__is_not_valid__text
  ```

- **Run CLI against local API**:
  Ensure `back_api2` is running locally.
  ```bash
  gencove <command> --host http://localhost:8200
  ```

- **Run CLI against dev API**:
  ```bash
  gencove <command> --host https://api-dev.gencove-dev.com
  ```

## Testing Guidelines

Tests use `pytest` and `vcrpy` to record and replay API interactions.

### Recording VCR Cassettes

To record new VCR cassettes, you need valid credentials.
1.  Copy the example environment file:
    ```bash
    cp gencove/tests/.env.dist gencove/tests/.env
    ```
2.  Edit `gencove/tests/.env` with valid credentials (API key, etc.).
3.  Run the test. If cassettes are missing, VCR will attempt to record them using the credentials.

### Pre-commit

Always run pre-commit hooks before pushing:
```bash
uv run pre-commit run
```

## Release Process

1.  **Check current version**:
    ```bash
    ./version-01-upgrade.sh print
    ```
2.  **Create release branch**: Create a branch named `version/X-Y-Z`.
3.  **Bump version**:
    ```bash
    ./version-01-upgrade.sh <major|minor|patch>
    ```
4.  **Merge**: Create a merge request to `master`.
5.  **Deploy**: After merging to `master`, create a merge request from `master` to `prod`.

