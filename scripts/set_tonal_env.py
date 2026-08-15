#!/usr/bin/env python3
"""Prompt for Tonal credentials and update the Hermes environment file."""

from __future__ import annotations

import getpass
import json
import os
import re
import tempfile
from pathlib import Path

MANAGED_KEYS = ("TONAL_USERNAME", "TONAL_PASSWORD")
_ASSIGNMENT_RE = re.compile(
    r"^(?P<prefix>[ \t]*(?:export[ \t]+)?"
    r"(?P<key>TONAL_USERNAME|TONAL_PASSWORD)[ \t]*=[ \t]*).*$"
)


def hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".hermes"


def _split_line_ending(line: str) -> tuple[str, str]:
    for ending in ("\r\n", "\n", "\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, ""


def _encode_value(value: str) -> str:
    return json.dumps(value)


def update_managed_lines(contents: str, values: dict[str, str]) -> str:
    """Replace managed assignments once while preserving every unrelated byte."""
    output: list[str] = []
    seen: set[str] = set()

    for line in contents.splitlines(keepends=True):
        body, ending = _split_line_ending(line)
        match = _ASSIGNMENT_RE.match(body)
        if not match:
            output.append(line)
            continue

        key = match.group("key")
        if key in seen:
            continue

        output.append(f"{match.group('prefix')}{_encode_value(values[key])}{ending}")
        seen.add(key)

    missing = [key for key in MANAGED_KEYS if key not in seen]
    if missing and output and not output[-1].endswith(("\n", "\r")):
        output.append("\n")

    for key in missing:
        output.append(f"{key}={_encode_value(values[key])}\n")

    return "".join(output)


def write_credentials(env_path: Path, username: str, password: str) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    current = env_path.read_bytes().decode("utf-8") if env_path.exists() else ""
    updated = update_managed_lines(
        current,
        {
            "TONAL_USERNAME": username,
            "TONAL_PASSWORD": password,
        },
    )

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".env.", dir=env_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(
            file_descriptor, "w", encoding="utf-8", newline=""
        ) as handle:
            handle.write(updated)
        os.replace(temporary_path, env_path)
        os.chmod(env_path, 0o600)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> None:
    username = input("Tonal username: ").strip()
    if not username:
        raise SystemExit("Tonal username cannot be empty.")

    password = getpass.getpass("Tonal password: ")
    if not password:
        raise SystemExit("Tonal password cannot be empty.")

    env_path = hermes_home() / ".env"
    write_credentials(env_path, username, password)
    print(f"Updated Tonal credentials in {env_path}")


if __name__ == "__main__":
    main()
