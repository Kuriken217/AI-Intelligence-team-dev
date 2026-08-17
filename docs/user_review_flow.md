# User Review Flow

## Purpose

The MVP needs a lightweight way to record user confirmation, decision, and result feedback without requiring a full Web UI.

## Review Intelligence

```bat
python -m src.intel_mvp.cli review --note obsidian_vault\30_Strategic_Intelligence\NOTE.md --status approved --comment "Use this as an active theme."
```

Allowed statuses:

- `approved`
- `rejected`
- `watchlist`
- `user_review`

## Record Decision

```bat
python -m src.intel_mvp.cli decide --note obsidian_vault\60_Decisions\NOTE.md --decision "Track as active theme" --reason "Relevant to AI infrastructure."
```

## Record Result

```bat
python -m src.intel_mvp.cli result --note obsidian_vault\70_Actions_and_Results\NOTE.md --action "Built supplier map" --result "Found 12 companies" --feedback "Need primary sources next."
```

## MVP Behavior

Each command updates note `status`, refreshes `updated`, and appends a log section to the note body.

Each intelligence run also creates a Review Queue note in `00_Inbox` that links to the notes the user should inspect.
