---
name: tonal
description: "Use Tonal data to plan training and manage workouts"
version: "1.0.0"
author: Derrick Wiest
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [tonal, fitness, recovery, workout-planning]
    category: health
---

# Tonal

Use Tonal for current muscle readiness, training history, progress,
movement discovery, and custom-workout management.

The tool schemas come from the registered `tonal` MCP server. This skill adds
the judgment that schemas cannot carry: when to check Tonal, how to combine
local fatigue with whole-body recovery, and how to preserve workout intent.

## Tool availability

The raw MCP names in Hermes configuration become these callable tools:

- `mcp__tonal__get_muscle_readiness`
- `mcp__tonal__get_user_stats`
- `mcp__tonal__get_recent_progress`
- `mcp__tonal__get_recent_workouts`
- `mcp__tonal__list_custom_workouts`
- `mcp__tonal__delete_custom_workout`
- `mcp__tonal__get_custom_workout_details`
- `mcp__tonal__create_workout`
- `mcp__tonal__get_workout_for_editing`
- `mcp__tonal__update_workout`
- `mcp__tonal__get_movements`
- `mcp__tonal__search_movements`

A read-only installation exposes nine of these. The three write tools are
`create_workout`, `update_workout`, and `delete_custom_workout`. If a write
tool is absent, explain that the read-only profile is active. Do not try to
work around the allowlist.

Never request credentials in chat, pass them as tool arguments, quote them,
or include them in a response.

## When to use Tonal

Reach for Tonal when the user asks about:

- what to train today based on local muscle recovery
- recent workouts, consistency, streaks, volume, or progress
- custom workouts already saved on Tonal
- valid Tonal movement names or movement characteristics
- creating, editing, or deleting a custom workout

Use current tool data rather than remembered readiness or workout state.
Readiness changes over time. If a tool fails, report the failure without
inventing a recovery score or workout result.

## Muscle-readiness interpretation

Interpret each reported muscle percentage with these bands:

| Readiness | Status | Guidance |
|---|---|---|
| 80-100% | Ready | Full capacity |
| 60-79% | Partial | Can train if needed |
| Below 60% | Fatigued | Prioritize recovery |

Do not turn these bands into medical claims. They are training inputs.
Consider the actual muscle values, not only an average that can hide a
fatigued area.

For push, pull, and legs suggestions, carry forward these rotation rules:

- If chest, shoulders, or triceps are below 50%, prefer pull or legs.
- If back or biceps are below 50%, prefer push or legs.
- If quads, glutes, or hamstrings are below 50%, prefer upper body.
- If the relevant groups are ready, any workout remains available.

The 50% rotation trigger is narrower than the below-60 fatigued band. Keep
the distinction rather than silently changing either threshold.

Load [references/recovery-planning.md](references/recovery-planning.md) when
giving a recovery-based session recommendation.

## Combine Tonal with Oura

Tonal answers which muscles appear recovered. Oura adds whole-body context
from sleep, HRV, and general readiness. Use both when current Oura context is
available:

| Oura context | Tonal context | Training direction |
|---|---|---|
| Low readiness, below 70 | Any muscle state | Rest or light work |
| Good recovery | Specific muscles fatigued | Train a different group |
| Good recovery | All relevant muscles ready | Full workout |

On remy-mac, treat injected Oura context as current only when its freshness
markers say so. Missing current-day data means not synced or not available
yet. It does not mean low recovery. Follow the freshness procedure in the
recovery runbook before relying on stale or partial data.

Always include Derrick's stated energy, soreness, pain, illness, and training
intent. Neither score overrides how he says he feels.

## Read workflows

For a quick training recommendation:

1. Call `mcp__tonal__get_muscle_readiness`.
2. Check current Oura context when available and fresh.
3. Apply the readiness bands and the relevant push/pull/legs rule.
4. State which inputs support the recommendation and note missing inputs.

For history or trends, choose the narrowest tool:

- `get_recent_workouts` for workout records and recent summary data.
- `get_recent_progress` for recent frequency and trend analysis.
- `get_user_stats` for broader fitness statistics and streak information.

For existing custom workouts:

1. Use `list_custom_workouts` to establish the exact name.
2. Use `get_custom_workout_details` for a human-readable inspection.
3. Use `get_workout_for_editing` only when an edit-ready structure or
   lossless per-set data is needed.

## Workout authoring

Load [references/workout-authoring.md](references/workout-authoring.md)
before creating or updating a workout. It documents `setDetails`, blocks,
alternating reps, duration-based movements, and movement setup metadata.

Core rules:

- Resolve exact movement names with `search_movements` before writing.
- Use `setDetails` when sets differ. Its length is the set count.
- Treat returned `setDetails` as the source of truth during edits.
- The same `block` number groups movements so they alternate.
- For alternating movements, prescribed reps are total reps across sides.
  Ten per side must be programmed as 20 total reps.
- Match rep-based movements with `reps` and timed movements with `duration`
  in seconds.
- Do not guess setup metadata or mode support when a result omits it.

## Mutation safety

`update_workout` replaces the workout's full set list. It is not a partial
patch. Before updating:

1. Fetch the workout with `get_workout_for_editing`.
2. Preserve every exercise and every set that should remain.
3. Apply the requested change to the complete editable structure.
4. Send the complete `exercises` array to `update_workout`.
5. Inspect the fresh workout state returned after saving.

Never construct an update from only the exercise being changed. That would
delete omitted sets and exercises.

Before deleting:

1. Resolve the exact workout name with `list_custom_workouts`.
2. State which custom workout will be deleted.
3. Obtain explicit user confirmation for that deletion.
4. Call `delete_custom_workout` with the exact name and `confirm: true`.

`confirm: true` is required by the tool. Never infer it from an earlier,
ambiguous, or unrelated request.

For creation, verify the title, movement names, block grouping, and per-set
programming before calling `create_workout`. After any mutation, report the
actual tool result rather than assuming Tonal accepted the change.

## Progressive references

- [Recovery planning](references/recovery-planning.md): readiness bands,
  push/pull/legs rotation, Oura freshness, and combined recommendations.
- [Workout authoring](references/workout-authoring.md): uniform and per-set
  shapes, full-replacement edits, blocks, timed movements, alternating reps,
  and setup compatibility.
