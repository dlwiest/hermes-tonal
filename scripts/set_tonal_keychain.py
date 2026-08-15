#!/usr/bin/env python3
"""Store Tonal credentials in the macOS login Keychain.

Interactive. Prompts for a Tonal username and password, hides the password input,
and writes a single generic-password item to the login Keychain. Nothing is echoed,
logged, or written to disk in plaintext.

  Service: tonal
  Account: <the username you enter>
  Password: <the password you enter>

Read them back with:
  security find-generic-password -s tonal -w        # password only
  security find-generic-password -s tonal | grep acct

Remove them with:
  security delete-generic-password -s tonal
"""

from __future__ import annotations

import getpass
import subprocess
import sys

SERVICE = "tonal"


def existing_account() -> str | None:
    """Return the account already stored for SERVICE, if any."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICE],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith('"acct"'):
            _, _, value = stripped.partition("<blob>=")
            return value.strip().strip('"') or None
    return None


def purge_existing() -> int:
    """Delete every generic-password item for SERVICE. Returns how many were removed.

    Keychain items are keyed by (service, account), so `add -U` only REPLACES when the
    account also matches. Entering a different username would otherwise leave two
    `-s tonal` items, and `find-generic-password -s tonal` picks between them
    nondeterministically -- meaning the launcher could authenticate as the stale
    account. Deleting until none remain guarantees exactly one item afterward.
    """
    removed = 0
    while True:
        result = subprocess.run(
            ["security", "delete-generic-password", "-s", SERVICE],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return removed
        removed += 1
        if removed > 25:  # paranoia: never spin forever on an unexpected `security`
            return removed


def store(account: str, password: str) -> None:
    """Write the Keychain item, having first purged any prior entries."""
    # The password is passed via -w on argv. That is visible to `ps` for the
    # lifetime of this call, which is the same tradeoff `security` itself imposes;
    # there is no stdin form of add-generic-password.
    result = subprocess.run(
        [
            "security", "add-generic-password",
            "-s", SERVICE,
            "-a", account,
            "-w", password,
            "-U",
            "-D", "application password",
            "-j", "Tonal account used by ts-tonal-client / ts-tonal-mcp",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(f"security failed: {result.stderr.strip()}\n")
        raise SystemExit(1)


def main() -> None:
    current = existing_account()
    if current:
        print(f"A Tonal entry already exists for: {current}")
        print("Continuing will replace it.\n")

    default = current or ""
    prompt = f"Tonal username{f' [{default}]' if default else ''}: "
    username = input(prompt).strip() or default
    if not username:
        sys.stderr.write("A username is required.\n")
        raise SystemExit(1)

    password = getpass.getpass("Tonal password (hidden): ")
    if not password:
        sys.stderr.write("A password is required.\n")
        raise SystemExit(1)

    confirm = getpass.getpass("Confirm password (hidden): ")
    if password != confirm:
        sys.stderr.write("Passwords did not match. Nothing was stored.\n")
        raise SystemExit(1)

    # Purge first so a changed username cannot leave a second, stale `-s tonal` item.
    purged = purge_existing()
    store(username, password)

    # Verify by reading it back rather than trusting the write.
    check = subprocess.run(
        ["security", "find-generic-password", "-s", SERVICE, "-w"],
        capture_output=True,
        text=True,
    )
    stored_account = existing_account()
    ok = (
        check.returncode == 0
        and check.stdout.rstrip("\n") == password
        and stored_account == username
    )

    print()
    print(f"Stored in the login Keychain under service '{SERVICE}'.")
    print(f"  account:  {username}")
    print(f"  replaced: {purged} prior entr{'y' if purged == 1 else 'ies'}")
    print(f"  readback: {'verified' if ok else 'FAILED — check Keychain Access'}")
    print()
    print(f"Remove it later with:  security delete-generic-password -s {SERVICE}")

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
