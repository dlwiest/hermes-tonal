#!/usr/bin/env python3
"""Launch the Tonal MCP server with a minimal credential environment."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_ASSIGNMENT_RE = re.compile(
    r"^[ \t]*(?:export[ \t]+)?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*(?P<value>.*)$"
)
DEFAULT_SERVER_PATH = Path.home() / "Projects" / "ts-tonal-mcp" / "dist" / "index.js"
KEYCHAIN_SERVICE = "tonal"


def hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".hermes"


def _decode_value(raw_value: str, name: str, line_number: int) -> str:
    value = raw_value.strip()
    if not value:
        return ""

    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(
                f"invalid quoted value for {name} on line {line_number}"
            ) from error
        if not isinstance(decoded, str):
            raise ValueError(
                f"non-string value for {name} on line {line_number}"
            )
        return decoded

    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise ValueError(
                f"invalid quoted value for {name} on line {line_number}"
            )
        return value[1:-1]

    return value


def load_tonal_values(env_path: Path) -> dict[str, str]:
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    contents = env_path.read_bytes().decode("utf-8")
    for line_number, line in enumerate(contents.splitlines(), start=1):
        match = _ASSIGNMENT_RE.match(line)
        if not match:
            continue

        name = match.group("name")
        if not name.startswith("TONAL_"):
            continue

        values[name] = _decode_value(match.group("value"), name, line_number)

    return values


def load_keychain_values() -> dict[str, str]:
    """Read Tonal credentials from the macOS login Keychain, if present.

    Preferred over the plaintext env file. Returns {} on any non-macOS platform,
    a missing `security` binary, or a missing keychain item -- callers fall back
    to the env file rather than failing.
    """
    if sys.platform != "darwin":
        return {}

    security = shutil.which("security")
    if not security:
        return {}

    def query(*args: str) -> str | None:
        try:
            result = subprocess.run(
                [security, "find-generic-password", "-s", KEYCHAIN_SERVICE, *args],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout

    password_output = query("-w")
    metadata = query()
    if password_output is None or metadata is None:
        return {}

    password = password_output.rstrip("\n")
    username = ""
    for line in metadata.splitlines():
        stripped = line.strip()
        if stripped.startswith('"acct"'):
            _, _, value = stripped.partition("<blob>=")
            username = value.strip().strip('"')
            break

    if not username or not password:
        return {}

    return {"TONAL_USERNAME": username, "TONAL_PASSWORD": password}


def _server_path(values: dict[str, str]) -> Path:
    configured = os.environ.get("TONAL_MCP_SERVER_PATH") or values.get(
        "TONAL_MCP_SERVER_PATH"
    )
    if not configured:
        return DEFAULT_SERVER_PATH

    expanded = os.path.expandvars(os.path.expanduser(configured))
    return Path(expanded)


def _minimal_environment(values: dict[str, str]) -> dict[str, str]:
    environment = {
        "HOME": str(Path.home()),
        "PATH": os.environ.get("PATH", os.defpath),
        "TONAL_USERNAME": values["TONAL_USERNAME"],
        "TONAL_PASSWORD": values["TONAL_PASSWORD"],
    }
    for name in ("LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "XDG_CACHE_HOME"):
        if name in os.environ:
            environment[name] = os.environ[name]
    return environment


def resolve_tonal_values() -> tuple[dict[str, str], str, Path]:
    """Load Tonal settings, preferring Keychain credentials over the env file."""
    env_path = hermes_home() / ".env"
    values = load_tonal_values(env_path)

    # Keychain wins over the plaintext env file when both are present. Non-secret
    # settings such as TONAL_MCP_SERVER_PATH belong in config.yaml (the server's
    # `env:` block, which Hermes merges into this process environment); the env
    # file is still read as a fallback.
    source = f"env file {env_path}"
    keychain_values = load_keychain_values()
    if keychain_values:
        values = {**values, **keychain_values}
        source = f"login Keychain (service '{KEYCHAIN_SERVICE}')"

    return values, source, env_path


def fail(message: str) -> int:
    print(f"tonal_mcp_server.py: {message}", file=sys.stderr)
    return 1


def main() -> int:
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
        env_setter = Path(__file__).with_name("set_tonal_env.py")
        keychain_setter = Path(__file__).with_name("set_tonal_keychain.py")
        return fail(
            f"missing {', '.join(missing)} (checked the login Keychain under service "
            f"'{KEYCHAIN_SERVICE}' and {env_path}). Run "
            f"'python3 {keychain_setter}' to store them in the Keychain (preferred), "
            f"or 'python3 {env_setter}' to write them to the env file."
        )

    print(f"tonal_mcp_server.py: credentials from {source}", file=sys.stderr)

    server_path = _server_path(values)
    if not server_path.is_file():
        return fail(
            f"MCP server entry point not found at {server_path}. "
            "Clone and build ts-tonal-mcp there, or set TONAL_MCP_SERVER_PATH in "
            "the mcp_servers.tonal env block of ~/.hermes/config.yaml "
            f"(or, as a fallback, in {env_path})."
        )

    node = shutil.which("node", path=os.environ.get("PATH", os.defpath))
    if not node:
        return fail("Node.js was not found on PATH. Install Node.js and retry.")

    try:
        os.execvpe(
            node,
            [node, str(server_path)],
            _minimal_environment(values),
        )
    except OSError as error:
        return fail(f"could not execute {server_path} with Node.js: {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
