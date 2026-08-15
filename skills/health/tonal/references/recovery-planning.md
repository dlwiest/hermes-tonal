# Recovery planning runbook

Use this runbook for same-day workout recommendations that combine Tonal
muscle readiness with Oura recovery context.

## Gather current inputs

1. Call `mcp__tonal__get_muscle_readiness` for current muscle percentages.
2. Read today's Oura context when it is available and fresh.
3. Ask about Derrick's stated condition only when it is not already in the
   request or conversation.
4. Note the planned training goal, if one was supplied.

Never substitute an old readiness result for a current tool call. Never treat
missing Oura data as a low score.

## Tonal readiness bands

Apply these bands to each muscle:

| Percentage | Interpretation | Training use |
|---|---|---|
| 80-100% | Ready | Full capacity |
| 60-79% | Partial | Can train if needed |
| Below 60% | Fatigued | Prioritize recovery |

An overall average can hide a single fatigued target. Inspect the muscles that
the proposed workout actually uses.

## Push, pull, and legs rotation

Use the carried-forward rotation guidance when a target group is especially
fatigued:

- Push fatigued: chest, shoulders, or triceps below 50%. Prefer pull or legs.
- Pull fatigued: back or biceps below 50%. Prefer push or legs.
- Legs fatigued: quads, glutes, or hamstrings below 50%. Prefer upper body.
- Relevant groups ready: any workout remains available.

The rotation trigger is below 50%. The broader fatigued band begins below 60%.
Do not merge the two thresholds.

## Oura freshness on remy-mac

remy-mac already collects private, read-only Oura context. Before using it:

- Check whether today's readiness and long sleep are present.
- If injected context is partial or stale after 09:00 local time, run:

```bash
/Users/dlwiest/Projects/oura-context/scheduled_refresh.py --if-stale
```

- If current-day data is still missing, describe it as not synced or not
  available yet.
- Do not infer low capacity from stale or missing data.

Oura is a non-diagnostic input. Derrick's reported energy, soreness, pain,
illness, and intent remain part of the decision.

## Combine the signals

Use this evidence table:

| Oura | Tonal | Direction |
|---|---|---|
| Low readiness, below 70 | Any muscle state | Rest or light work |
| Good recovery | Proposed muscles fatigued | Train a different group |
| Good recovery | Relevant muscles ready | Full workout |

If Oura and Tonal point in different directions, explain the difference.
Oura describes whole-body recovery while Tonal localizes muscle readiness.
Prefer a recommendation that respects the more limiting current signal and
Derrick's stated condition.

## Response shape

A useful recommendation should state:

1. the current Oura status or that it is unavailable
2. the Tonal values for the muscles that matter
3. the readiness band or rotation rule applied
4. a concrete training direction
5. any missing or stale input that limits confidence

Do not present the recommendation as diagnosis or certainty. Keep the data and
the interpretation distinguishable.
