# Agent Processing Templates

The prompt templates in `prompts/` define the first operating rules for each MVP agent.

## Template Set

| Agent | Template |
|---|---|
| Commander | `prompts/commander.md` |
| Collector | `prompts/collector.md` |
| Analyst | `prompts/analyst.md` |
| Intelligence Editor | `prompts/editor.md` |
| Red Team | `prompts/red_team.md` |
| Strategist | `prompts/strategist.md` |
| Knowledge Keeper | `prompts/knowledge_keeper.md` |

## Implementation Use

These files are not just documentation. They are intended to become the exact runtime instructions when the MVP is connected to an LLM execution layer.

## Current Constraint

The current local pipeline simulates the output structure. It does not yet call a model, browse the web, or read a real Obsidian vault.

