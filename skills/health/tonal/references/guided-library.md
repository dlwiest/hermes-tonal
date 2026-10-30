# Guided library

Tonal's published guided workouts (over 3,000) and programs (over 300). This is
Tonal's catalog, not the user's custom workouts or training history.

## Finding a workout

Use `mcp__tonal__search_workout_library`. Every filter is optional and they
combine:

- `targetArea`: UPPER BODY, LOWER BODY, FULL BODY, or CORE.
- `level`: BEGINNER, INTERMEDIATE, ADVANCED, or ALL.
- `trainingType`: for example Strength, High Intensity, Yoga, Mobility,
  Cardio, Recovery, Boxing, Barre, or Pilates.
- `minMinutes` / `maxMinutes`: inclusive length bounds.
- `device`: Classic, T3, or Elite.
- `query`: text in the title or description.
- Equipment:
  - `availableEquipment` keeps only workouts that need nothing beyond what the
    user owns; pass `[]` for no equipment. Tonal lists no equipment for about
    970 workouts (mostly yoga, mobility, recovery, and cardio, which usually
    need none), so those are left out and the response says how many. For
    those kinds of workouts, search by `trainingType` without an equipment
    filter instead.
  - `requiresEquipment` keeps only workouts that use every listed accessory.
  - Accessory names are StraightBar, Handles, Rope, Bench, Mat, Roller,
    AnkleStraps, and PilatesLoops.

Results are newest first, 10 per page by default (`limit` up to 50). When the
header says more match, page with `offset` instead of claiming the list is
complete. Prefer a few tight filters over a broad search.

## Inspecting a workout

`mcp__tonal__get_library_workout` with a result's `workoutId` returns the
exercises in the same shape `create_workout` accepts. To save a guided workout
as an editable custom copy, pass those exercises to `create_workout` after the
user approves the write.

Some on-machine guided sets carry no weight percentage, and the response says
how many. `create_workout` sends 0% for a set without a weight, so give those
sets a `weight` before saving a copy, and tell the user you did. `weightLb`
also works, but only for rep counts the user has recent history at.
Off-machine sets (mat, bodyweight) correctly have no weight. If the response
lists movements missing from the catalog, replace them via `search_movements`
before saving.

## Programs

Use `mcp__tonal__search_program_library` with `weeks`, `workoutsPerWeek`,
`level`, `device`, `availableEquipment`, or `query`. Each result shows its
weekdays, for example Mon, Wed, Fri.

`mcp__tonal__get_library_program` lists the schedule by week. "Workout 2"
means the second workout of that week, not a calendar day; the program's
weekdays say when. Each entry has a `workoutId` for `get_library_workout`.

None of these tools start, schedule, or enroll the user in anything. Say so if
the user asks to start a program; enrollment happens on the Tonal.
