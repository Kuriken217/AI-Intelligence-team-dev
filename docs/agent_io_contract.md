# Agent I/O Contract

This document defines the first MVP contract for the AI Intelligence Unit agents.

The contract is intentionally lightweight. It is designed to make every stage reviewable before adding live web research, automations, or a UI.

## Cycle

```text
information_request
 -> mission_brief
 -> source_digest
 -> analysis_packet
 -> integrated_intelligence
 -> red_team_review
 -> strategy_packet
 -> obsidian_note
 -> user_decision
 -> result_feedback
```

## Global Rules

- Every important claim must remain traceable to a source or be marked as an interpretation.
- Facts, interpretations, hypotheses, recommendations, and decisions must not be merged into one undifferentiated summary.
- Confidence and likelihood must be explicit when the output influences a decision.
- Red Team review happens before final strategy.
- Obsidian is the source of truth after saving.
- User decision and result feedback must be saved for future analysis.

## Agent Inputs And Outputs

| Agent | Input | Output |
|---|---|---|
| Commander | information_request, project context, prior Obsidian knowledge | mission_brief |
| Collector | mission_brief, source instructions | source_digest |
| Analyst | source_digest, mission_brief | analysis_packet |
| Intelligence Editor | analysis_packet, mission_brief | integrated_intelligence |
| Red Team | integrated_intelligence, analysis_packet, strategy draft | red_team_review |
| Strategist | integrated_intelligence, red_team_review, user context | strategy_packet |
| Knowledge Keeper | all packets, vault rules | obsidian_note set |

## MVP Rule Of Thumb

If a stage cannot produce its required output, it should produce a gap instead of pretending the answer is complete.

