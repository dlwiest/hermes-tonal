# Strength and activity-history guidance

Use `mcp__tonal__get_strength_scores` for Tonal's headline Strength Score: the current Overall, Upper, Core, and Lower scores plus a per-activity trend. Do not substitute `mcp__tonal__get_goal_metrics`. Its Functional Strength Score is a separate weekly goal metric, not the headline Strength Score.

Use `mcp__tonal__list_workout_activities` to page completed workout activities
and obtain exact activity IDs for later inspection.

## Lookback semantics

The optional `days` argument on `get_strength_scores` is a calendar-day
lookback window. It is never a workout count, activity count, or row count.
Pass a positive integer only when the user requests a time window. Omit it to
query available strength-score history from account creation.

A small window can legitimately return no history points when the most recent
scored activity falls outside that many calendar days. This is not an error
and does not establish that the account has no older history. Report it as
zero scored activities in the requested window. For `get_strength_scores`,
still use the current regional scores returned by the tool. If older trend
context is needed, retry with a wider calendar-day window or omit `days`.

## Reading Strength Scores

- Current scores are the latest Overall, Upper, Core, and Lower values. Only regional rows have meaningful update timestamps; the Overall row's source timestamp is a zero date and is intentionally omitted.
- Earliest and latest name the boundaries of the returned history, not the account unless the request omitted `days`.
- Each change is newest minus oldest within the requested result. A positive value rose over that window, a negative value fell, and zero means the boundary values match.
- The activity count is the number of scored activities Tonal returned for the calendar window. It is independent of the numeric `days` value.
- The detail list contains at most the ten newest history points. A `showing 10 of N` label means the change and coverage summary still use all `N` returned points, while only the display is truncated.

## Enumerating Activity IDs

`list_workout_activities` passes `offset` and `limit` to Tonal's completed
workout-activity endpoint. `offset` defaults to 0; `limit` defaults to 20 and
must be between 1 and 100.

Tonal returns this collection oldest first: offset 0 selects the account's
oldest activities, and increasing the offset moves toward newer activities.
The tool sorts only the selected page by `beginTime` descending for
readability. Its oldest/newest `beginTime` range describes that page, not the
account. A `nextOffset` is shown when Tonal returns a full page; follow it to
inspect the next source page. For recent history, use `get_recent_workouts`
instead. Its activity-summary IDs are the same IDs accepted by
`get_workout_activity_details` and `get_workout_summary`.

Preserve an activity's exact ID. Call `get_workout_activity_details` for
performed sets or `get_workout_summary` for Tonal's movement-level summary.
Inspect one activity at a time rather than treating the compact list as detail
or a bulk export. Omitted load fields mean unknown, never zero.

Completeness is page-relative unless every source page was fetched. If a
multi-page sweep is interrupted or any request fails, describe it as
incomplete even when some records succeeded.

Keep conclusions scoped to the reported window. Strength Score is a training trend, not a medical assessment, and it should not override current pain, illness, fatigue, or the user's stated condition.
