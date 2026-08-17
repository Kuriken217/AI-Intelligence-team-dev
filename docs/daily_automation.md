# Daily Automation

The daily automation phase reduces operating load by making one configured command responsible for the full loop:

```text
Configured profile
 -> Theme feeds
 -> Source digest
 -> Intelligence run
 -> Obsidian notes
 -> Mobile txt copies
 -> Evaluation
 -> Latest summary
```

## Current Profile

`config/daily_runs.json` defines `morning_climate`.

It currently uses:

- Theme: `climate_public_agencies`
- Schedule target: JST 06:00
- Sources: official feeds configured in `config/daily_intelligence_themes.json`
- Output: configured Obsidian vault under `AI_Intelligence_Unit`
- Mobile output: each note category's `For Mobile\latest.txt`
- Evaluation output: `work\reports\daily_runs`
- Latest run summary: `work\daily_runs\morning_climate\summaries\latest_summary.json`

## Manual Run

```bat
python src\intel_mvp\cli.py daily-run --profile morning_climate --config config\daily_runs.json
```

## Windows Scheduled Task

Register the task:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_morning_climate_task.ps1
```

The default task name is `AI Intelligence Daily Climate Brief`.
It runs every day at `06:00` local time.

To use a specific Python runtime:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_morning_climate_task.ps1 -PythonPath "C:\Path\To\python.exe"
```

## ChatGPT / Codex Operation

The same command can be triggered from a ChatGPT/Codex instruction.
The useful prompt shape is:

```text
Run the morning_climate daily profile, verify the evaluation passed,
and report the newest Mobile latest.txt path.
```

## Web UI Options

A Web UI is optional after daily automation is stable. The most useful first UI would read the Obsidian output and expose:

- Today's Daily Intelligence brief
- Source list and source quality flags
- Red Team checks
- Approve / reject / watchlist review controls
- Decision and result input
- Theme and feed configuration
- Run history and evaluation score

For the MVP, Obsidian plus mobile `.txt` files remain the source of truth.
The Web UI should be treated as a review and control layer, not as the knowledge base itself.
