# Source Policy

## Purpose

The MVP should preserve source quality before it tries to automate research. This policy helps the Collector and Red Team avoid treating all source material as equal.

## Preferred Source Order

1. Primary source
2. Regulatory filing
3. Company disclosure
4. Technical standard
5. Research paper
6. Reputable news
7. Market commentary
8. Social media

## Required Source Fields

Each source should include:

- `title`
- `url`
- `type`
- `date`
- `publisher`
- `primary_source`
- `reliability`
- `summary`

## MVP Gap Rules

The source digest should flag gaps when:

- no primary source is included
- fewer than three sources are included
- fewer than two high or medium reliability sources are included
- a decision-heavy topic lacks customer, technical, financial, or operational evidence

## Current Limitation

The MVP currently evaluates manually supplied Markdown source digests. Live browsing, API search, and private-source access come later and require user approval.

## URL Ingestion

The MVP can convert a structured URL source JSON file into a source digest Markdown file.

Example:

```bat
python -m src.intel_mvp.cli ingest-urls --input examples\url_sources.json --output work\generated_sources.md
```

The command does not fetch web pages yet. It validates URL-shaped inputs and preserves source metadata for later collection and review.

## URL Enrichment

When network access is available, the MVP can fetch HTML pages and add retrieved metadata to the URL source JSON.

```bat
python -m src.intel_mvp.cli enrich-urls --input examples\url_sources.json --output work\enriched_url_sources.json
```

The command extracts:

- fetched title
- meta description
- text excerpt
- publisher or site name
- published date
- canonical URL
- estimated reliability

This is intentionally separate from `ingest-urls` so manually curated source metadata remains possible.
