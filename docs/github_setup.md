# GitHub Setup

## Current Local Status

- Local Git repository: initialized
- Branch: `main`
- Remote: `https://github.com/Kuriken217/AI-Intelligence-team-dev.git`
- First checkpoint: pushed to GitHub
- Public-safe initial commit: `acc7270 Initial-public-MVP-scaffold`

## Recommended Repository Settings

Recommended repository name:

```text
AI-Intelligence-team-dev
```

Current visibility:

```text
public
```

Reason:

- The project references a personal Obsidian vault path.
- Future runs may contain private notes, decisions, and intelligence topics.
- The MVP may later connect to private source material.

## What Should Be Pushed

Push source-controlled implementation assets:

- `config/`
- `docs/`
- `examples/`
- `prompts/`
- `src/`
- `tests/`
- `README.md`
- `pyproject.toml`
- `.gitignore`

Do not push generated or private run output by default:

- `obsidian_vault/`
- `evaluation_vault/`
- `runs/`
- `reports/`
- `config/user_settings.json`

These are excluded by `.gitignore`.

Commit only `config/user_settings.example.json` as a template.

## Setup Options

### Option A: User Creates GitHub Repo

1. Create an empty private repository on GitHub.
2. Share the repository full name, such as:

```text
owner/ai-intelligence-unit-mvp
```

3. Add the remote locally.
4. Push `main`.
5. Optionally create GitHub Issues from `docs/github_issue_drafts.md`.

### Option B: Existing GitHub Repo

1. Share the repository full name.
2. Confirm it is safe to push this project there.
3. Add the remote locally.
4. Push `main` or create a new branch if the repository already has content.

## Required User Confirmation

Before pushing to GitHub, confirm:

- repository full name
- public/private
- whether pushing `main` is acceptable
- whether to create Issues from the backlog

## Current GitHub Integration Limitation

Codex can read repository metadata and files through the GitHub app, but write operations currently return:

```text
403 Resource not accessible by integration
```

This affected both file creation and issue creation through the app integration.

For now, use GitHub Web or GitHub Desktop for write operations such as pushing and creating Issues.
