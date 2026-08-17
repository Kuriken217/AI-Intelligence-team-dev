# Daily Intelligence Brief

Daily Intelligence is the user-facing news brief format for recurring monitoring topics.

## Standard Sections

1. Headline
2. Summary
3. Key Developments
4. Why It Matters
5. Potential Implications
6. Confidence / Uncertainty
7. What To Watch Next
8. Red Team Checks
9. Sources
10. User Review

## Request-Level Customization

Add a `news_brief` object to an information request to tune the brief without changing code.

```json
{
  "news_brief": {
    "headline": "Short user-facing headline",
    "why_it_matters": ["Why this matters to the user"],
    "potential_implications": ["What could change if this signal persists"],
    "watch_next": ["Next indicator or release to monitor"],
    "red_team_checks": ["What to challenge before acting"]
  }
}
```

If fields are omitted, the pipeline falls back to source summaries, scope, decision context, source quality, and generic Red Team checks.
