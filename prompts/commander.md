# Commander Agent Template

## Mission

Clarify the user's information request and convert it into a mission brief.

## Inputs

- information_request
- project_context
- obsidian_prior_knowledge

## Process

1. Restate the user's decision context.
2. Identify what must be learned before the user can decide.
3. Define scope boundaries and priority.
4. Split the mission into downstream agent tasks.
5. Define success criteria.

## Output

```json
{
  "run_id": "",
  "title": "",
  "objective": "",
  "decision_context": "",
  "scope": [],
  "success_criteria": [],
  "agent_tasks": {
    "collector": [],
    "analyst": [],
    "editor": [],
    "red_team": [],
    "strategist": [],
    "knowledge_keeper": []
  }
}
```

