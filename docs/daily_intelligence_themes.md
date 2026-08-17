# Daily Intelligence Themes

Daily Intelligence themes are reusable monitoring definitions.

They live in:

```text
config/daily_intelligence_themes.json
```

Each theme defines:

- default information request fields
- scope and tags
- the `news_brief` tone and sections
- source guidance for URL collection

## Current Themes

- `climate_public_agencies`
- `ai_infrastructure`
- `financial_markets`
- `geopolitics`
- `company_watch`

## Commands

```bat
python src\intel_mvp\cli.py list-themes
python src\intel_mvp\cli.py create-theme-request --theme climate_public_agencies --output work\theme_requests\climate_request.json
python src\intel_mvp\cli.py create-theme-urls --theme climate_public_agencies --output work\theme_requests\climate_urls.json
```

The generated request can be used with `run-to-obsidian` or `run-urls-to-obsidian` after URL sources are filled in.

To generate the themed request and run it into Obsidian in one command:

```bat
python src\intel_mvp\cli.py run-theme-to-obsidian --theme climate_public_agencies --urls examples\environment_public_agency_urls.json --settings config\user_settings.json --work-dir work\theme_runs
```
