# Workout authoring runbook

Load this runbook before calling `mcp__tonal__create_workout` or
`mcp__tonal__update_workout`.

## Safe authoring sequence

1. Use `mcp__tonal__search_movements` to find valid movement names.
2. Use the exact returned movement name in each exercise.
3. Decide whether each movement counts repetitions or time.
4. Decide which exercises belong in the same block.
5. Inspect available setup metadata before grouping movements.
6. Choose uniform programming or explicit `setDetails` for each exercise.
7. Check alternating-movement totals.
8. Preview the complete exercise list before a write.

Do not infer a movement identifier or exact name from ordinary gym naming.
The MCP server resolves the supplied name against Tonal's movement list.

## Uniform exercise programming

When every set has the same prescription, omit `setDetails` and use the
uniform fields:

```json
{
  "movementName": "Bench Press",
  "sets": 3,
  "reps": 10,
  "weight": 70,
  "block": 1
}
```

For a timed movement, use `duration` in seconds instead of `reps`:

```json
{
  "movementName": "Plank",
  "sets": 3,
  "duration": 30,
  "block": 2
}
```

`weight` is Tonal's weight percentage from 0 through 100, not a value in
pounds. The MCP tool schema determines which top-level fields are accepted.

## Per-set programming with `setDetails`

Use `setDetails` when the prescription changes across sets or when preserving
an edit returned by Tonal:

```json
{
  "movementName": "Bench Press",
  "block": 1,
  "setDetails": [
    {
      "reps": 12,
      "weight": 50,
      "warmUp": true,
      "description": "Warm-up"
    },
    {
      "reps": 10,
      "weight": 70
    },
    {
      "reps": 8,
      "weight": 75
    }
  ]
}
```

Each entry describes one Tonal set. Supported per-set keys are:

| Key | Meaning |
|---|---|
| `reps` | Prescribed total repetitions for a rep-based movement |
| `duration` | Prescribed seconds for a duration-based movement |
| `weight` | Tonal weight percentage from 0 through 100 |
| `warmUp` | Marks that set as a warm-up |
| `dropSet` | Marks that set as a drop set |
| `burnout` | Enables burnout for that set when the movement supports it |
| `description` | Description attached to that set |

When `setDetails` is present, it is authoritative:

- Its array length defines the set count.
- The MCP server emits one Tonal set for each entry.
- Top-level `sets`, `reps`, `duration`, and `weight` do not define the
  resulting sets.
- Keep the entries in the intended execution order.

Do not add redundant uniform fields beside `setDetails`. A stale top-level
value makes the request harder to review even though `setDetails` wins.

## Reading an editable workout

`mcp__tonal__get_workout_for_editing` always reconstructs `setDetails` from
the real Tonal sets. Use those entries as the source of truth.

The response also fills the convenience `sets`, `reps`, and `weight` fields
when every set agrees. Those fields are summaries. They do not replace the
per-set details during a read-modify-write workflow.

A timed set remains a timed set through its per-set `duration`. Do not turn it
into a rep prescription merely because a convenience `reps` field is absent.

## Updating without data loss

`mcp__tonal__update_workout` replaces the full set list. It does not merge a
partial exercise fragment into the existing workout.

Use this sequence:

1. Fetch the exact workout with `get_workout_for_editing`.
2. Copy the complete returned exercise structure.
3. Modify only the requested title, description, exercise, or set details.
4. Keep every unchanged exercise, block, and `setDetails` entry.
5. Submit the complete `exercises` array to `update_workout`.
6. Review the fresh workout state returned by the tool.

If a workout has five exercises and only one is changing, the update request
must still contain all five exercises. Omitting four removes their sets.

## Rep-based and duration-based movements

Tonal movements determine whether programming is repetition-based or
duration-based. The predecessor integration used the movement's `countReps`
metadata to make that distinction.

- Rep-based movement: prescribe `reps`.
- Duration-based movement: prescribe `duration` in seconds.
- Do not substitute an estimated rep count for a timed movement.
- Do not prescribe both forms merely to hedge. Follow the movement metadata.

If the available MCP result does not make the distinction clear, search the
movement more narrowly or ask for clarification. Do not guess and write.

## Alternating-movement total reps

For an alternating movement, Tonal treats prescribed reps as the total across
both sides, not the count per side.

If the intent is 10 reps on the left and 10 on the right, prescribe:

```json
{ "reps": 20 }
```

Apply this conversion to every relevant uniform set or `setDetails` entry.
First verify that movement metadata identifies the movement as alternating.
Do not double the value for bilateral movements where both sides work at the
same time.

## Blocks and supersets

The `block` field groups exercises. Exercises with the same block number are
placed in one Tonal block and alternate by round. This is the superset
mechanism.

```json
[
  {
    "movementName": "Tricep Pushdown",
    "sets": 3,
    "reps": 12,
    "block": 2
  },
  {
    "movementName": "Overhead Tricep Extension",
    "sets": 3,
    "reps": 12,
    "block": 2
  }
]
```

Different block numbers produce different blocks. An exercise without a
`block` value gets its own separate block. Block labels express grouping, not
movement identity.

## Setup-aware block building

Do not infer compatibility from movement names alone. When movement metadata
is available, use this order of operations:

1. Prefer easy setup handling within the block.
2. Prefer matching `accessory`.
3. Prefer matching `baseOfSupport` when practical.
4. Use `armAngle` and `cartHeight` as strong guides.
5. Then, when possible, alternate muscle groups within the block.

Relevant on-machine metadata includes:

- `armAngle`: Low, Middle, or High
- `cartHeight`: Low, Middle, or High
- `accessory`: Handles, Rope, StraightBar, and other returned values
- `baseOfSupport`: the returned support/setup value

Search results can expose only part of this metadata. Missing metadata means
unknown. It is not evidence that two setups match.

Before enabling a mode, inspect the movement's corresponding support flag when
that metadata is available:

- `spotterDisabled`
- `burnoutDisabled`
- `chainsDisabled`
- `eccentricDisabled`
- `smartFlexDisabled`
- `autoWeightOffDisabled`

A disabled flag is a reason not to program that mode automatically. The
current per-set shape supports `burnout`, `dropSet`, and `warmUp`; it does not
provide fields for every Tonal mode named above. Do not invent unsupported
request keys.

## Final write check

Before creating or updating, verify:

- every movement name came from Tonal search results
- every movement uses reps or duration as its metadata requires
- alternating rep prescriptions represent total reps across sides
- every block groups movements intentionally
- setup metadata supports the grouping, or missing data is acknowledged
- `setDetails` is used wherever sets differ
- an update contains the complete exercise and set list
