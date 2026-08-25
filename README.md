# hermes-tonal

Hermes Agent integration for Tonal. It registers
[`ts-tonal-mcp`](https://github.com/dlwiest/ts-tonal-mcp) as a local MCP
server and adds a companion skill for recovery interpretation and workout
authoring.

The MCP server owns the schemas and conversion logic. This repo does not copy
that logic into another CLI.

## Layout

- `scripts/set_tonal_keychain.py` stores Tonal credentials in the macOS login
  Keychain (preferred).
- `scripts/set_tonal_env.py` writes them to `~/.hermes/.env` instead (portable
  fallback).
- `scripts/tonal_mcp_server.py` launches the built MCP server with a minimal
  environment, reading credentials from the Keychain first and the env file
  second.
- `config/` contains read-only and full-access Hermes MCP snippets.
- `skills/health/tonal/` contains the companion skill and its runbooks.

These instructions target remy-mac. Run them on that machine. This repository
does not install or change `~/.hermes` by itself.

## 1. Clone and build the MCP server

Use `~/Projects` on remy-mac so the launcher defaults work without extra
configuration.

```bash
mkdir -p ~/Projects
cd ~/Projects

git clone https://github.com/dlwiest/ts-tonal-mcp.git
cd ts-tonal-mcp
npm install
npm run build
test -f ~/Projects/ts-tonal-mcp/dist/index.js
```

`npm install` pulls `@dlwiest/ts-tonal-client` from npm, so there is no need to
clone or link the client separately. Verified from a clean clone: install,
build, and the test suite all pass against the published package.

The launcher defaults to:

```text
~/Projects/ts-tonal-mcp/dist/index.js
```

If the MCP repo lives elsewhere, override the path. `TONAL_MCP_SERVER_PATH` is a
non-secret setting, so it belongs in `config.yaml` rather than the env file —
Hermes convention is secrets in `.env` or the Keychain, everything else in
`config.yaml`. Add it to the server's `env:` block:

```yaml
mcp_servers:
  tonal:
    env:
      TONAL_MCP_SERVER_PATH: /absolute/path/to/ts-tonal-mcp/dist/index.js
```

Hermes merges that block into the launcher's process environment, and the
launcher prefers a process-environment value over the env file.

Setting it in `~/.hermes/.env` still works as a fallback:

```dotenv
TONAL_MCP_SERVER_PATH=/absolute/path/to/ts-tonal-mcp/dist/index.js
```

The credential scripts preserve that line. If both are set, `config.yaml` wins.

## 2. Store Tonal credentials locally

Two options. The launcher checks the Keychain first and falls back to the env
file, so pick one.

### Keychain (preferred, macOS)

```bash
python3 ~/Projects/hermes-tonal/scripts/set_tonal_keychain.py
```

Prompts for the username and password (hidden, entered twice), then writes one
generic-password item to the login Keychain under service `tonal` and verifies
it by reading it back. No plaintext credential is ever written to disk.

It purges any prior `tonal` entry first. Keychain items are keyed by
(service, account), so `add -U` only replaces when the account also matches —
entering a different email would otherwise leave two items and the launcher
would pick between them nondeterministically.

Remove it with:

```bash
security delete-generic-password -s tonal
```

### Env file (portable fallback)

```bash
python3 ~/Projects/hermes-tonal/scripts/set_tonal_env.py
```

Updates only `TONAL_USERNAME` and `TONAL_PASSWORD` in the single flat Hermes
environment file `~/.hermes/.env`, hiding password input, preserving unrelated
lines, and forcing mode `0600`. This is the only option on Linux.

Both scripts honor `HERMES_HOME` and neither prints a credential. The launcher
reports which source it used on stderr at startup. Do not put credentials in
`config.yaml`, a Telegram message, or this repository.

## 3. Merge the MCP configuration

Choose one config file:

- `config/mcp_servers.tonal.yaml` exposes eleven read-only tools. This is the
  recommended default because an accidental call cannot change custom
  workouts.
- `config/mcp_servers.tonal.full.yaml` exposes all 14 tools, including create,
  update, and delete.

Merge the `tonal` mapping under the existing `mcp_servers` key in
`~/.hermes/config.yaml`. Do not replace the whole config file and do not add a
second `mcp_servers` key. The checked-in launcher path assumes this repo is at
`/Users/dlwiest/Projects/hermes-tonal`; update that argument if the clone is
elsewhere.

Both snippets set `timeout: 300` explicitly. Their `tools.include` entries are
raw MCP tool names such as `get_muscle_readiness`. Prefixed registry names such
as `mcp__tonal__get_muscle_readiness` do not match this filter and would
silently hide the tools.

Both snippets use `trust: untrusted`. Hermes then requests approval for each
tool that lacks `readOnlyHint: true`. In the full profile, that covers create,
update, and delete. Changing the setting to `full` skips this MCP
write-approval gate.

Hermes also creates a toolset named `mcp-tonal`. No action is normally needed:
enabled MCP servers are available on every platform by default. A platform only
restricts them if its `platform_toolsets` list explicitly names one or more MCP
**server** names (`tonal`, not `mcp-tonal`), which turns that list into an
allowlist — or if it contains the `no_mcp` sentinel, which disables all MCP
servers for that platform. Listing ordinary toolsets such as `terminal` does not
restrict MCP.

## 4. Reload Hermes

Reload or restart the Hermes gateway and its MCP connections after merging the
configuration. If the gateway is run directly, stop the existing process and
start `hermes gateway` again. If it is supervised, use the same service manager
that normally restarts it.

This reload is required before the Tonal tools appear in Telegram sessions.
Changing the YAML while the gateway keeps running is not enough.

## 5. Install the companion skill

Hermes discovers skills recursively. There is no
`hermes skills install <local-dir>` command and no separate registration step.

The recommended setup keeps this Git checkout as the source of truth. Merge
this into `~/.hermes/config.yaml`:

```yaml
skills:
  external_dirs:
    - /Users/dlwiest/Projects/hermes-tonal/skills
```

This survives `git pull` without a second copy step. If `skills` or
`external_dirs` already exists, add the directory to the existing mapping or
list instead of creating a duplicate key.

The copy-based alternative is:

```bash
mkdir -p ~/.hermes/skills/health/tonal
cp -R ~/Projects/hermes-tonal/skills/health/tonal/. \
  ~/.hermes/skills/health/tonal/
```

The containing directory must remain named `tonal`, exactly matching
`name: tonal` in `SKILL.md`.

A skill added during a session is invisible to that session. Start a new
Hermes or Telegram session after installation.

## 6. Verify discovery

Run:

```bash
hermes mcp list
```

The recommended profile should show the Tonal equivalent of:

```text
tonal ... 11 selected ✓ enabled
```

The full profile should show:

```text
tonal ... 14 selected ✓ enabled
```

If it reports zero selected tools, check that `tools.include` uses raw names
without `mcp__tonal__`. If Tonal is absent, check the launcher path, the built
`dist/index.js`, and gateway logs. The launcher reports missing credentials or
entry points without printing secret values.

After discovery, start a new session and ask for current muscle readiness. A
successful answer proves the gateway, MCP server, Tonal login, and companion
skill are working together.

## Security model

Credentials live in the macOS login Keychain when available, falling back to
the single flat `~/.hermes/.env`. The Keychain path is preferred because it
keeps the password out of a plaintext file entirely; Hermes itself has no
Keychain secret source, so the launcher bridges the two.

The launcher reads only `TONAL_*` values from whichever source it uses, then
execs the server with a MINIMAL environment: the two Tonal credentials plus a
small allowlist of system variables Node needs. The rest of the Hermes process
environment is not inherited. Verified by probe: the child sees 7 variables,
and planted `ANTHROPIC_API_KEY` / `AWS_SECRET_ACCESS_KEY` values do not reach
it.

The skill deliberately declares NO `required_environment_variables`. The MCP
launcher owns authentication, and the MCP subprocess environment is built from
`mcp_servers.tonal` alone — `tools/mcp_tool.py::_build_safe_env` passes a safe
baseline (PATH, HOME, `XDG_*`), secret-source values, and the server config's
own `env:` block, and never consults a skill. The skill-declaration mechanism
(`tools/env_passthrough.py`) is read only by the `terminal` and `execute_code`
sandboxes, which this skill does not use. Declaring the variables would have
prompted for credentials the Keychain already holds, for no benefit.

If a future CLI one-shot is ever added here, that is when the declaration
becomes necessary.

## Related projects

This integration supersedes
[`clawdbot-tonal`](https://github.com/dlwiest/clawdbot-tonal), whose recovery
and workout-planning guidance is carried into the companion skill.

- [`ts-tonal-mcp`](https://github.com/dlwiest/ts-tonal-mcp) provides the MCP
  tools and workout conversion.
- [`ts-tonal-client`](https://github.com/dlwiest/ts-tonal-client) provides the
  Tonal API client.

There is intentionally no copied `tonal.mjs` or one-shot CLI here. If a future
cron workflow has a concrete need that MCP cannot serve, a narrow one-shot can
be considered then without duplicating workout conversion.
