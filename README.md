# Bookscrapper

## Setup

This codebase uses Python 3.14.0. Library dependencies, as well as developer dependencies, can be found in `pyproject.toml`

`uv` is used for package management and developer environment setup. To setup the local development environment for this project,
follow the installation instructions for uv [here](https://docs.astral.sh/uv/getting-started/installation/). After installing uv and cloning the Git repository,
run:

``` 
uv sync
# or add the --no-dev if you want just the project dependencies without developer dependencies 
```

To setup a virtual environment with all the project and developer dependencies installed.

To launch the local server run: `uv run uvicorn src.api.app:app --reload` at the root of the project directory.

Additionally, you can run `source .venv/bin/activate` to enter a shell with CLI program dependencies active.

Run tests with `uv run pytest`
