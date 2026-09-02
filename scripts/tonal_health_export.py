#!/usr/bin/env python3
"""Run the Tonal health exporter with launcher-compatible credentials."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from tonal_mcp_server import (
    KEYCHAIN_SERVICE,
    _minimal_environment,
    _server_path,
    hermes_home,
    resolve_tonal_values,
)


def fail(message: str) -> int:
    print(f"tonal_health_export.py: {message}", file=sys.stderr)
    return 1


def launch_exporter(values: dict[str, str], server_path: Path) -> int:
    node = shutil.which("node", path=os.environ.get("PATH", os.defpath))
    if not node:
        return fail("Node.js was not found on PATH. Install Node.js and retry.")

    exporter = Path(__file__).with_name("tonal_health_export.mjs")
    try:
        os.execvpe(
            node,
            [node, str(exporter), str(server_path), *sys.argv[1:]],
            _minimal_environment(values),
        )
    except OSError as error:
        return fail(f"could not execute the Node.js exporter: {error}")

    return 0


def main() -> int:
    if any(argument in ("-h", "--help") for argument in sys.argv[1:]):
        return launch_exporter(
            {"TONAL_USERNAME": "", "TONAL_PASSWORD": ""},
            _server_path({}),
        )

    try:
        values, source, env_path = resolve_tonal_values()
    except (OSError, UnicodeError, ValueError) as error:
        return fail(f"could not read {hermes_home() / '.env'}: {error}")

    missing = [
        name
        for name in ("TONAL_USERNAME", "TONAL_PASSWORD")
        if not values.get(name)
    ]
    if missing:
        return fail(
            f"missing {', '.join(missing)} (checked the login Keychain under service "
            f"'{KEYCHAIN_SERVICE}' and {env_path})"
        )

    server_path = _server_path(values)
    if not server_path.is_file():
        return fail(
            f"MCP server entry point not found at {server_path}. "
            "Clone and build ts-tonal-mcp there, or configure "
            "TONAL_MCP_SERVER_PATH."
        )

    print(f"tonal_health_export.py: credentials from {source}", file=sys.stderr)
    return launch_exporter(values, server_path)


if __name__ == "__main__":
    raise SystemExit(main())
