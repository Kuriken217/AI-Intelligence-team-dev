# Obsidian Knowledge Base Design

## Positioning

Obsidian is the source of truth for the MVP. The application and agents should treat saved notes as reusable intelligence, not as disposable report output.

## Folder Structure

| Folder | Purpose |
|---|---|
| `00_Inbox` | Unprocessed requests and imported material |
| `10_Daily_Intelligence` | Daily intelligence briefs |
| `20_Project_Intelligence` | Project-specific intelligence |
| `30_Strategic_Intelligence` | Decision-oriented reports |
| `40_Knowledge` | Reusable facts, concepts, and insights |
| `50_Hypotheses` | Hypotheses and confidence history |
| `60_Decisions` | User decisions and rationale |
| `70_Actions_and_Results` | Actions, results, and feedback |
| `90_Sources` | Source digests and references |
| `Templates` | Reusable note templates |

## Required Frontmatter

```yaml
type:
status:
created:
updated:
source:
confidence:
likelihood:
related_project:
tags:
run_id:
```

## Status Flow

```text
draft
 -> collected
 -> analyzed
 -> red_team_reviewed
 -> user_review
 -> approved / rejected / watchlist
 -> decided
 -> waiting
 -> completed
```

## Link Rule

The preferred knowledge chain is:

```text
Source Digest
 -> Fact
 -> Analysis
 -> Insight
 -> Hypothesis
 -> Recommendation
 -> Decision
 -> Result
```

## MVP Save Behavior

The first implementation creates five notes per intelligence run:

- Source Digest
- Strategic Intelligence Report
- Hypothesis Note
- Decision Note
- Result Note

This is enough to preserve traceability, review, decision, and feedback without overbuilding the vault too early.

