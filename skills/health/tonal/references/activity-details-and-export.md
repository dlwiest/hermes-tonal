# Activity details and health-export guidance

Use this runbook to inspect one completed Tonal session or create a private health export. Both workflows are read-only. Never call a create, update, or delete tool as part of either workflow.

## Inspecting one session

1. For a recent session, call `mcp__tonal__get_recent_workouts`. Its activity-summary ID is the same identifier accepted by the detail and summary tools.
2. For deeper enumeration of older history, page `mcp__tonal__list_workout_activities` with `offset` and `limit`. Offset 0 selects the account's oldest source page; increasing the offset moves toward newer activities. The tool sorts only within each selected page, so do not use its displayed order to claim global recency.
3. Call `mcp__tonal__get_workout_activity_details` with the exact activity ID for the performed sets in execution order.
4. Call `mcp__tonal__get_workout_summary` with the same activity ID when Tonal's per-movement totals or workout metadata are needed.
5. Keep the activity ID and the source field names in any report. Do not infer a zero when a load or range-of-motion field is absent.

The detail tool resolves each set's `movementId` against Tonal's movement catalog and reports the movement name, set group, block, reps, average resistance, one-rep max, on-machine volume, and range of motion. The summary tool reports Tonal's own ordered `movementSets`, including movement-level volume and individual sets. Use detail for performed-set analysis and summary for Tonal's aggregation rather than trying to reconstruct one from the other.

## Duration semantics

Completed-session durations have three names that must not be conflated:

- `totalDuration` in activity detail, and `duration` in the formatted summary, are wall-clock elapsed time.
- `activeDuration` is exactly equal to `timeUnderTension`. It is loaded time, not wall-clock workout duration.
- `restDuration` is always 0 and cannot be used to calculate or report actual rest.

A measured session had 182 minutes of wall-clock `totalDuration` and 6 minutes of `activeDuration` / `timeUnderTension`. Report both with their labels when duration matters. Never describe the 6-minute value as the elapsed workout length or subtract it from wall clock to claim a precise rest duration.

## Writing a health export

`getHealthExport` is deliberately not exposed as an MCP tool. Detailed exports can be large enough to flood model context; a full measured account export was 23 MB. Run the local wrapper, which writes the JSON to disk and prints only the absolute path:

```bash
python3 ~/Projects/hermes-tonal/scripts/tonal_health_export.py \
  --output ~/tonal-health-export.json \
  --start-date 2026-01-01 \
  --end-date 2026-09-02 \
  --limit 25 \
  --include-set-details true
```

The wrapper accepts these client options without renaming their underlying keys:

| CLI flag | `getHealthExport` option |
|---|---|
| `--start-date` | `startDate` |
| `--end-date` | `endDate` |
| `--limit` | `limit` |
| `--include-muscle-readiness` | `includeMuscleReadiness` |
| `--include-lifetime-statistics` | `includeLifetimeStatistics` |
| `--include-external-activities` | `includeExternalActivities` |
| `--include-set-details` | `includeSetDetails` |

Boolean flags require an explicit `true` or `false`. Omitted options retain the client's defaults. Use `--help` for the complete invocation.

Credentials follow the MCP launcher exactly: the macOS login Keychain item under service `tonal` wins, then `~/.hermes/.env` is the fallback. The wrapper also locates the npm client relative to the built MCP `dist/index.js`, honoring the same `TONAL_MCP_SERVER_PATH` override as the launcher. It does not require a separate client checkout.

Hermes owns output-file safety because the published npm package returns an object and does not include the client repository's example file helpers. The exporter creates a 0600 temporary file in the destination directory, flushes it, atomically renames it into place, and refuses symlink or non-file destinations. Replacing a regular file repairs its final permissions to 0600.

Treat the result as private health data. Do not `cat` it, paste it into chat, or read a full export back into model context. Report the printed path. If the user later requests analysis, inspect only the bounded portion needed for that request.
