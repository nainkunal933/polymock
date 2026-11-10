<h1 align="center">
  <img src="assets/icon.svg" alt="" width="128" height="128"><br>
  Polymock
</h1>

Polymock is a local MCP server that generates and populates sandbox data through
your AI agent.

## Install

Both plugins require [uv](https://docs.astral.sh/uv/getting-started/installation/)
0.12.23 or newer to start the MCP server.

### Claude Code

Run this in Claude Code v2.1.275 or later:

```text
/plugin install polymock --marketplace nainkunal933/polymock
```

Confirm the marketplace when prompted, then choose an install scope.

### Codex

Run these commands in your terminal:

```sh
codex plugin marketplace add nainkunal933/polymock
codex plugin add polymock@polymock-marketplace
```

Start a new local Codex session in the project you want to use with Polymock.

## MCP tools

- `analyze`: inventories project files and provides schema analysis instructions
  for the host agent.
- `generate`: creates synthetic CSV data from SQL Server creation procedures.
- `populate`: generates and executes population SQL in a selected Docker container.

Generated project files are stored in `.polymock/`. Docker must be installed and
running Linux containers for population. See [examples](examples/README.md) for
sample databases.

## Manual setup

Use these options with other MCP hosts or for development. Polymock runs over
STDIO and needs no model-provider API key; the host handles model authentication.

### Run from source

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.23 or
newer and Python 3.12 or newer. From the project root, run:

```sh
uv sync --locked
uv run --locked src/main.py
```

Configure your MCP host to launch the same command from the project root.

### Build an executable

```sh
uv sync --locked --group build
uv run --locked --group build scripts/build.py
```

This creates `dist/polymock` (Linux/macOS) or `dist/polymock.exe` (Windows) for
the current platform. Use `--output-dir PATH` to change the destination.

### Run the executable

Configure your MCP host to launch the executable by its absolute path, with no
arguments. Python and uv are not required. To start it manually, run
`./dist/polymock` or `.\dist\polymock.exe`. It writes a startup message to stderr,
then waits for MCP requests; press Ctrl+C to stop.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for native builds and the release process.
