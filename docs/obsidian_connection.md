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
