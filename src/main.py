"""Start Sandboxer's local MCP server over STDIO."""

from pathlib import Path
import sys

from dotenv import load_dotenv

from mcp_integration import SandboxerMCPServer


def main() -> None:
    """Load the project environment and serve MCP requests."""
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    server = SandboxerMCPServer()
    print(
        "Starting Sandboxer MCP server over STDIO. Press Ctrl+C to stop.",
        file=sys.stderr,
        flush=True,
    )
    server.run()


if __name__ == "__main__":
    main()
