# Strength and activity-history guidance

Use `mcp__tonal__get_strength_scores` for Tonal's headline Strength Score: the current Overall, Upper, Core, and Lower scores plus a per-activity trend. Do not substitute `mcp__tonal__get_goal_metrics`. Its Functional Strength Score is a separate weekly goal metric, not the headline Strength Score.

Use `mcp__tonal__list_workout_activities` to enumerate performed activity dates and `workoutActivityId` values for later inspection. It discovers IDs through Strength Score history; it does not call either capped workout-list endpoint.

## Lookback semantics

The optional `days` argument on both tools is a calendar-day lookback window. It is never a workout count, activity count, or row count. Pass a positive integer only when the user requests a time window. Omit it to query available strength-score history from account creation.

A small window can legitimately return no history points when the most recent scored activity falls outside that many calendar days. This is not an error and does not establish that the account has no older history. Report it as zero scored activities in the requested window. For `get_strength_scores`, still use the current regional scores returned by the tool. If older context or IDs are needed, retry with a wider calendar-day window or omit `days`.

## Reading Strength Scores

- Current scores are the latest Overall, Upper, Core, and Lower values. Only regional rows have meaningful update timestamps; the Overall row's source timestamp is a zero date and is intentionally omitted.
- Earliest and latest name the boundaries of the returned history, not the account unless the request omitted `days`.
- Each change is newest minus oldest within the requested result. A positive value rose over that window, a negative value fell, and zero means the boundary values match.
- The activity count is the number of scored activities Tonal returned for the calendar window. It is independent of the numeric `days` value.
- The detail list contains at most the ten newest history points. A `showing 10 of N` label means the change and coverage summary still use all `N` returned points, while only the display is truncated.

## Enumerating Activity IDs

`list_workout_activities` makes one Strength Score history request per call, sorts the discovered rows newest first, and applies `startIndex` and `pageSize` only to the rendered result. These presentation arguments are not Tonal API pagination. Never claim that the capped Tonal workout lists were paged, and never describe `days` as the number of rows requested.

The discovered count and earliest/latest activity times describe the complete pre-slice result for the requested Strength Score history window. `Showing X..Y of N` describes only the rendered page. `Presentation truncated: yes` means some discovered rows are not rendered on that page. Follow `nextStartIndex` only when more presentation rows are needed; each call performs a fresh single history request and local slice.

The returned `workoutActivityId` values are enumeration keys for later activity inspection. Preserve the exact ID. When a detail-inspection tool is available, inspect one activity at a time rather than treating this compact enumeration as activity detail or a bulk export. In any later detail report, omitted load fields mean unknown, never zero.

Completeness is always source-relative: all IDs Tonal emitted through Strength Score history for the requested lookback. Do not broaden that into a claim that every possible Tonal activity class must emit a Strength Score history row. A complete presentation page is not proof of completeness outside that named source and window, and a truncated page must never be described as a complete displayed list. If a later multi-activity sweep is interrupted or any detail fails, describe the sweep as incomplete even when some records succeeded.

Keep conclusions scoped to the reported window. Strength Score is a training trend, not a medical assessment, and it should not override current pain, illness, fatigue, or the user's stated condition.
