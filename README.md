# AI Intelligence Unit MVP

This is the first development scaffold for the AI Intelligence Unit MVP.

The goal of this MVP is to prove the core cycle:

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

## What This Version Provides

- Agent responsibility definitions in `config/agents.json`
- Agent I/O contracts in `config/io_schemas.json`
- Obsidian vault rules in `config/vault_rules.json`
- User-local settings template in `config/user_settings.example.json`
- A sample information request in `examples/information_request.json`
- A sample source digest in `examples/sources.md`
- A local pipeline that writes structured Markdown notes into an Obsidian-style vault
- Basic tests for the note-generation cycle

## Run The MVP Pipeline

Use the bundled Python runtime if Python is not available in your normal terminal.

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run --request examples\information_request.json --sources examples\sources.md --vault obsidian_vault
```

## Write Directly To Obsidian

Set `obsidian_vault_path` and `obsidian_output_root` in `config/user_settings.json`, then verify write access:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py check-obsidian-write --settings config\user_settings.json
```

Generate notes directly under the configured Obsidian output folder:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-to-obsidian --request examples\information_request.json --sources examples\sources.md --settings config\user_settings.json
```

Fetch public URLs, build a source digest, and write the intelligence brief directly to Obsidian:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-urls-to-obsidian --request examples\environment_public_agency_request.json --urls examples\environment_public_agency_urls.json --settings config\user_settings.json --work-dir work\environment_public_agency --enrich
```

Daily Intelligence news briefs use the standard sections documented in `docs\daily_intelligence_brief.md`.
Add a `news_brief` object to a request JSON to tune headline, implications, watch items, and Red Team checks for a specific topic.

List and create reusable Daily Intelligence theme templates:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py list-themes
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py create-theme-request --theme climate_public_agencies --output work\theme_requests\climate_request.json
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py create-theme-urls --theme climate_public_agencies --output work\theme_requests\climate_urls.json
```

Run a filled theme URL source file directly into Obsidian:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-theme-to-obsidian --theme climate_public_agencies --urls examples\environment_public_agency_urls.json --settings config\user_settings.json --work-dir work\theme_runs
```

Collect a theme's configured feeds and run them directly into Obsidian:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py collect-theme-feeds --theme climate_public_agencies --output work\theme_feed_runs\climate_public_agencies\feed_sources.json --limit 3
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-theme-feeds-to-obsidian --theme climate_public_agencies --settings config\user_settings.json --work-dir work\theme_feed_runs --limit 3
```

Run the configured morning Daily Intelligence profile end to end:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py daily-run --profile morning_climate --config config\daily_runs.json
```

To register a local Windows Scheduled Task for daily 06:00 execution:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_morning_climate_task.ps1
```

The task runs `scripts\run_daily_morning_climate.ps1`, which writes the Obsidian notes, mobile `.txt` files, evaluation report, and latest daily summary.

See `docs\daily_automation.md` for the automation flow and Web UI options.

## Run Tests

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests
```

## GitHub Preflight

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m src.intel_mvp.git_check
```

## Local Obsidian Settings

Copy `config/user_settings.example.json` to `config/user_settings.json` and set your local Obsidian vault path.
`config/user_settings.json` is intentionally ignored by Git.

Generated MVP notes are written under the configured `obsidian_output_root` folder inside the vault so the project output stays grouped together.

For mobile Google Drive review, the Obsidian direct commands also create plain `.txt` copies under each note category's `For Mobile` folder.
For example, use `10_Daily_Intelligence\For Mobile\latest.txt` for the newest mobile-friendly daily brief.

## MVP Completion Target

The MVP is complete when one real user information request can be processed end-to-end and produces:

- A structured intelligence report
- Source notes
- Red Team review
- Strategic recommendations
- Obsidian-compatible knowledge notes
- A user decision note
- A result/feedback note ready for later updates
