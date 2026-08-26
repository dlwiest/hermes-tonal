# Strength Score guidance

Use `mcp__tonal__get_strength_scores` for Tonal's headline Strength Score: the current Overall, Upper, Core, and Lower scores plus a per-activity trend. Do not substitute `mcp__tonal__get_goal_metrics`. Its Functional Strength Score is a separate weekly goal metric, not the headline Strength Score.

## Lookback semantics

The optional `days` argument is a calendar-day lookback. It is never a workout count or row count. Pass a positive integer only when the user requests a time window. Omit it to query all available strength-score history from account creation.

A small window can legitimately return no history points when the most recent scored activity falls outside that many calendar days. This is not an error and does not establish that the account has no older history. Report it as zero scored activities in the requested window while still using the current regional scores returned by the tool. If older context is needed, retry with a wider calendar-day window or omit `days` for all available history.

## Reading the report

- Current scores are the latest Overall, Upper, Core, and Lower values. Only regional rows have meaningful update timestamps; the Overall row's source timestamp is a zero date and is intentionally omitted.
- Earliest and latest name the boundaries of the returned history, not the account unless the request omitted `days`.
- Each change is newest minus oldest within the requested result. A positive value rose over that window, a negative value fell, and zero means the boundary values match.
- The activity count is the number of scored activities Tonal returned for the calendar window. It is independent of the numeric `days` value.
- The detail list contains at most the ten newest history points. A `showing 10 of N` label means the change and coverage summary still use all `N` returned points, while only the display is truncated.

Keep conclusions scoped to the reported window. Strength Score is a training trend, not a medical assessment, and it should not override current pain, illness, fatigue, or the user's stated condition.
