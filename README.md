# Polymock

Polymock is a local MCP server that generates and populates sandbox data through
your AI agent.

## Run from source

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.23 or newer.
The project requires Python 3.12 or newer. From the project root, run:

```sh
uv sync --locked
uv run --locked src/main.py
```

This starts the MCP server over STDIO. Configure your MCP host to launch the same
command from the project root. The host manages model authentication; Polymock
does not require a model-provider API key for its MCP tools.

## MCP tools

- `analyze`: inventories project files and provides schema analysis instructions
  for the host agent.
- `generate`: creates synthetic CSV data from SQL Server creation procedures.
- `populate`: generates and executes population SQL in a selected Docker container.

Generated project files are stored in `.polymock/`. Docker must be installed and
running Linux containers for population. See [examples](examples/README.md) for
sample databases.

## Build a standalone executable

```sh
uv sync --locked --group build
uv run --locked --group build scripts/build.py
```

The output is `dist/polymock` on Linux/macOS or `dist/polymock.exe` on Windows.
Use `--output-dir PATH` to choose a different destination. Builds target the
operating system and architecture where the build runs.

## Run the executable

Configure your MCP host to launch the executable by its absolute path, without
arguments. The standalone executable does not require Python or uv installed.

To launch it manually on Linux/macOS:

```sh
./dist/polymock
```

On Windows:

```powershell
.\dist\polymock.exe
```

A startup message is written to stderr, then the server waits for MCP requests.
Press Ctrl+C to stop a manually launched instance.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for native builds and the release process.
