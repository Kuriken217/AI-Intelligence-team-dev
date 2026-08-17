# Obsidian Connection

## User Vault

The user's Obsidian vault path is configured locally in `config/user_settings.json`.

Use `config/user_settings.example.json` as the committed template.

```text
C:\path\to\your\obsidian\vault
```

## Current Access Status

The original Google Drive mounted path was recorded first, but the current execution environment could not read it directly because Windows returned an access denied error.

Latest check: 2026-08-17. Read permission was requested and granted in Codex, but Windows still returned access denied for the Google Drive mounted path.

The working local setup uses a local synced vault path in `config/user_settings.json`.

That file is intentionally ignored by Git so personal environment paths are not pushed to GitHub.

Generated MVP notes are written under `obsidian_output_root` inside the vault. The default is:

```text
AI_Intelligence_Unit
```

This keeps direct pipeline output separated from the user's existing Obsidian folders while still making the notes visible in Obsidian.

## Direct Write Check

Use this command to verify direct write access before running the pipeline against the real vault:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py check-obsidian-write --settings config\user_settings.json
```

The command creates, reads, and removes a temporary `.codex_write_test.md` file in the configured output folder.

## Mobile Google Drive Review

Obsidian notes stay in `.md` format because that is the vault source format.

Some mobile Google Drive clients do not preview Markdown or JSON reliably, so direct Obsidian runs also write plain-text copies under:

```text
AI_Intelligence_Unit\99_Mobile_Review
```

Use `latest_review.txt` for the newest mobile-friendly brief. Each run also gets its own folder with `00_index.txt` and numbered `.txt` files.

## Direct Obsidian Run

Use this command to generate the MVP note set directly into the configured Obsidian output folder:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-to-obsidian --request examples\information_request.json --sources examples\sources.md --settings config\user_settings.json
```

Use this command when the source material starts as URLs:

```bat
C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe src\intel_mvp\cli.py run-urls-to-obsidian --request examples\environment_public_agency_request.json --urls examples\environment_public_agency_urls.json --settings config\user_settings.json --work-dir work\environment_public_agency --enrich
```

## MVP Behavior

When the configured vault is readable, the pipeline will:

1. scan Markdown notes
2. match notes against the information request title, tags, project, scope, and objective
3. save related note candidates into the run bundle
4. include a prior-knowledge summary before collection and analysis
5. save a lightweight difference analysis against prior note excerpts

## User Input Needed Later

If direct access to the local synced path becomes blocked, one of the following will be needed:

- run the tool from an environment that can read the local synced path
- copy/export a subset of relevant Obsidian notes into the project workspace
- provide a synced local path that the execution environment can read
