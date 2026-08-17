# MVP Backlog

## Completion Definition

The MVP is complete when one real information request can move through the full cycle:

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

## Phase 1: Foundation

- [x] Create project scaffold
- [x] Define agent responsibilities
- [x] Define I/O contracts
- [x] Define Obsidian vault rules
- [x] Generate initial Obsidian notes from sample request
- [x] Add basic tests

Done when: a sample request creates reviewable Obsidian-compatible notes.

## Phase 2: Agent Runtime Contract

- [x] Add per-agent processing templates
- [x] Add structured intermediate files for each agent output
- [x] Make the pipeline write a full run bundle under `runs/`
- [x] Add validation for each intermediate output

Done when: every agent stage has a saved input, saved output, and validation result.

## Phase 3: Real Research Input

- [x] Add source ingestion from manually provided URLs or Markdown
- [x] Add source quality fields
- [x] Add primary-source preference rules
- [x] Add source gap reporting

Done when: the user can provide real source material and get traceable intelligence notes.

Requires user approval or input when: browsing the web, connecting search APIs, or accessing private sources.

## Phase 4: Obsidian Prior Knowledge

- [x] Read existing Obsidian notes from a configured vault path
- [x] Search related notes by tags, project, and title
- [x] Add prior-knowledge summary to mission brief
- [x] Add difference analysis against prior notes

Done when: new intelligence can reference and update prior knowledge.

Requires user approval or input when: selecting the real Obsidian vault path.

## Phase 5: User Review Flow

- [x] Add review status update command
- [x] Add decision recording command
- [x] Add result recording command
- [x] Add review queue note

Done when: approval, correction, rejection, decision, and result can be saved without manually editing every note.

## Phase 6: Evaluation

- [x] Add three local evaluation requests
- [ ] Run three user-selected real test requests
- [x] Score usefulness, traceability, uncertainty, and actionability
- [x] Add Red Team quality checklist
- [x] Write MVP evaluation report

Done when: at least three different information requests complete and reveal clear improvement items.

## Phase 7: GitHub And VSCode Setup

- [x] Initialize Git repository
- [x] Add `.gitignore`
- [x] Commit first local checkpoint
- [x] Draft GitHub setup guide
- [x] Draft GitHub Issues from backlog
- [ ] Create GitHub repository
- [x] Push first checkpoint
- [ ] Convert backlog into GitHub Issues if useful

Done when: implementation history and issue tracking are in place.

Requires user approval or input when: creating or connecting a GitHub repository.

## Phase 8: Optional UI

- [ ] Decide whether Obsidian-only review is enough for MVP
- [ ] If needed, build a small local review UI
- [ ] Read notes from the Obsidian vault
- [ ] Display report, Red Team review, decision form, and result form

Done when: the user can review and record decisions from a simple UI.

Requires user approval or input when: choosing whether to build the UI before or after real research integration.
