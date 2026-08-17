# AI Intelligence Unit MVP Development Overview

## Executive Briefing

The MVP proves a repeatable intelligence cycle:

```text
Information Request
 -> Collection
 -> Analysis
 -> Editorial Integration
 -> Red Team
 -> Strategy
 -> Obsidian Save
 -> User Review
 -> Decision
 -> Result Accumulation
```

The first build focuses on structure, repeatability, and reviewability. It does not attempt full autonomous web research yet.

## Development Order

1. Define the cycle and agent responsibilities.
2. Generate Obsidian-compatible notes from a request and source digest.
3. Add user review, decision, and result templates.
4. Test the cycle with real intelligence requests.
5. Add live research, Obsidian prior-knowledge retrieval, and UI later.

## MVP Completion Conditions

- A user request can be converted into an intelligence run.
- The run creates source, intelligence, hypothesis, decision, and result notes.
- Notes include metadata, source traceability, review status, and links.
- The user can review, approve, correct, reject, decide, and later record results in Obsidian.

## Current Phase

Phase 1 and the first slice of Phase 2/4 are represented in code:

- Agent definitions: `config/agents.json`
- Agent I/O contracts: `config/io_schemas.json`
- Vault rules: `config/vault_rules.json`
- Agent templates: `prompts/`
- Pipeline: `src/intel_mvp/pipeline.py`
- CLI: `src/intel_mvp/cli.py`
- Tests: `tests/test_pipeline.py`
- Obsidian output: `obsidian_vault`

## Next Engineering Step

Make the pipeline save a full run bundle under `runs/`, including each stage's intermediate input and output. This will make the MVP auditable before adding live research or model execution.

