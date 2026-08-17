from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.intel_mvp.contracts import validate_named_contract, validate_required_fields
from src.intel_mvp.delta import build_prior_knowledge_delta
from src.intel_mvp.evaluate_cases import run_evaluation_cases
from src.intel_mvp.evaluation import evaluate_run
from src.intel_mvp import feed_ingestion as feed_ingestion_module
from src.intel_mvp.feed_ingestion import FeedConfig, clean_summary, collect_sources_from_feeds, parse_feed, write_feed_sources
from src.intel_mvp.git_check import format_preflight, GitPreflightResult
from src.intel_mvp.mobile_review import write_mobile_review_copies
from src.intel_mvp.news_brief import build_news_brief, render_news_brief_markdown
from src.intel_mvp.obsidian_direct import (
    check_obsidian_write,
    resolve_obsidian_paths,
    run_pipeline_to_obsidian,
    run_theme_feeds_to_obsidian,
    run_theme_urls_to_obsidian,
    run_urls_to_obsidian,
)
from src.intel_mvp.pipeline import PipelineResult, parse_source_digest, run_pipeline, should_write_daily_intelligence, slugify
from src.intel_mvp.prior_knowledge import build_search_terms, filter_search_terms, find_related_notes
from src.intel_mvp.review import append_decision, append_result, append_review
from src.intel_mvp.stages import build_source_digest
from src.intel_mvp.source_ingestion import is_http_url, write_source_digest_from_urls
from src.intel_mvp.source_quality import is_primary_source, source_quality_gaps
from src.intel_mvp.themes import build_request_from_theme, build_url_source_template, list_theme_rows, load_theme_registry, write_theme_request
from src.intel_mvp.url_run import run_pipeline_from_urls
from src.intel_mvp.vault import missing_frontmatter_fields
from src.intel_mvp.web_enrichment import enrich_url_sources_file, extract_page_metadata


class PipelineTest(unittest.TestCase):
    def test_parse_source_digest(self) -> None:
        sources = parse_source_digest(
            """# Source Digest

## Source 1

- title: Example
- url: https://example.com
- type: news
- date: 2026-08-11
- summary: Example summary.
"""
        )

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["title"], "Example")
        self.assertEqual(sources[0]["summary"], "Example summary.")

    def test_parse_source_quality_fields(self) -> None:
        sources = parse_source_digest(
            """# Source Digest

## Source 1

- title: Example
- publisher: Example Publisher
- primary_source: true
- reliability: high
- summary: Example summary.
"""
        )

        self.assertEqual(sources[0]["publisher"], "Example Publisher")
        self.assertEqual(sources[0]["primary_source"], "true")
        self.assertEqual(sources[0]["reliability"], "high")

    def test_source_quality_gaps(self) -> None:
        gaps = source_quality_gaps([{"primary_source": "false", "reliability": "low"}])

        self.assertIn("Fewer than three sources are included.", gaps)
        self.assertIn("No primary source is currently included.", gaps)
        self.assertFalse(is_primary_source({"primary_source": "false"}))
        self.assertTrue(is_primary_source({"primary_source": "true"}))

    def test_build_source_digest_records_no_immediate_gaps(self) -> None:
        digest = build_source_digest(
            [
                {
                    "title": f"Official source {index}",
                    "summary": f"Official summary {index}.",
                    "primary_source": "true",
                    "reliability": "high",
                }
                for index in range(1, 4)
            ]
        )

        self.assertEqual(
            digest["collection_gaps"],
            ["No immediate source quality gaps detected in the current source set."],
        )

    def test_build_search_terms(self) -> None:
        terms = build_search_terms(
            {
                "title": "AIデータセンター向け液冷市場の変化",
                "objective": "AI infrastructure",
                "scope": ["市場動向"],
                "related_project": "AI Infrastructure Intelligence",
                "tags": ["liquid-cooling"],
            }
        )

        self.assertIn("ai", terms)
        self.assertIn("infrastructure", terms)
        self.assertIn("liquid", terms)

        filtered = filter_search_terms(terms, ["ai"])
        self.assertNotIn("ai", filtered)

    def test_find_related_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            note = vault / "AI Infrastructure.md"
            note.write_text(
                "# AI Infrastructure\n\n液冷 and AI infrastructure notes.",
                encoding="utf-8",
            )

            results = find_related_notes(
                vault,
                {
                    "title": "AIデータセンター向け液冷市場の変化",
                    "objective": "AI infrastructure",
                    "scope": ["市場動向"],
                    "related_project": "AI Infrastructure Intelligence",
                    "tags": ["liquid-cooling"],
                },
                ignored_terms=["ai"],
                min_score=2,
            )

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, "AI Infrastructure")

    def test_build_prior_knowledge_delta(self) -> None:
        delta = build_prior_knowledge_delta(
            {"related_note_count": 1, "notes": [{"excerpt": "Already known fact."}]},
            {"fact_candidates": ["Already known fact.", "New fact."]},
        )

        self.assertEqual(delta["already_seen_candidates"], ["Already known fact."])
        self.assertEqual(delta["new_fact_candidates"], ["New fact."])

    def test_append_review_updates_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            note = Path(temp_dir) / "review.md"
            note.write_text("---\nstatus: user_review\nupdated: 2026-08-11\n---\n\n# Review\n", encoding="utf-8")

            append_review(note, "approved", "Looks useful.")

            text = note.read_text(encoding="utf-8")
            self.assertIn("status: approved", text)
            self.assertIn("## User Review Log", text)
            self.assertIn("- Comment: Looks useful.", text)

    def test_append_decision_and_result_update_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            decision_note = Path(temp_dir) / "decision.md"
            result_note = Path(temp_dir) / "result.md"
            decision_note.write_text("---\nstatus: pending\nupdated: 2026-08-11\n---\n\n# Decision\n", encoding="utf-8")
            result_note.write_text("---\nstatus: waiting\nupdated: 2026-08-11\n---\n\n# Result\n", encoding="utf-8")

            append_decision(decision_note, "Track it", "Strong strategic fit.")
            append_result(result_note, "Built map", "Found useful candidates.", "Need more sources.")

            self.assertIn("status: decided", decision_note.read_text(encoding="utf-8"))
            self.assertIn("## Decision Log", decision_note.read_text(encoding="utf-8"))
            self.assertIn("status: completed", result_note.read_text(encoding="utf-8"))
            self.assertIn("## Result Log", result_note.read_text(encoding="utf-8"))

    def test_slugify_keeps_japanese_titles(self) -> None:
        self.assertEqual(slugify("AIデータセンター向け液冷市場の変化"), "AIデータセンター向け液冷市場の変化")

    def test_should_write_daily_intelligence_for_news_requests(self) -> None:
        self.assertTrue(should_write_daily_intelligence({"requested_output": "Daily Intelligence / News Brief"}))
        self.assertTrue(should_write_daily_intelligence({"title": "Environment news"}))
        self.assertFalse(should_write_daily_intelligence({"requested_output": "Strategic Intelligence"}))

    def test_news_brief_uses_request_customization(self) -> None:
        from datetime import datetime

        request = {
            "title": "Climate News",
            "objective": "Create a daily brief",
            "decision_context": "Decide whether to monitor it",
            "scope": ["climate", "ocean"],
            "requested_output": "Daily Intelligence / News Brief",
            "tags": ["test"],
            "news_brief": {
                "headline": "Custom headline",
                "why_it_matters": ["Custom reason"],
                "potential_implications": ["Custom implication"],
                "watch_next": ["Custom watch item"],
                "red_team_checks": ["Custom challenge"],
            },
        }
        sources = [
            {
                "title": "Official update",
                "url": "https://example.gov/update",
                "publisher": "Example Agency",
                "date": "2026-08-18",
                "primary_source": "true",
                "reliability": "high",
                "summary": "Official source summary.",
            }
        ]

        brief = build_news_brief(request, sources, datetime(2026, 8, 18))
        markdown = render_news_brief_markdown(request, brief, "run-1", datetime(2026, 8, 18), "report")

        self.assertEqual(brief.headline, "Custom headline")
        self.assertIn("Custom implication", markdown)
        self.assertIn("Custom watch item", markdown)
        self.assertIn("Custom challenge", markdown)
        self.assertIn("https://example.gov/update", markdown)

    def test_daily_intelligence_theme_registry_builds_request(self) -> None:
        registry = load_theme_registry(Path("config/daily_intelligence_themes.json"))
        rows = list_theme_rows(registry)
        request = build_request_from_theme(registry, "climate_public_agencies")
        url_template = build_url_source_template(registry, "climate_public_agencies")

        self.assertIn(("climate_public_agencies", "Climate / Public Agencies", "high"), rows)
        self.assertEqual(request["requested_output"], "Daily Intelligence / News Brief")
        self.assertIn("news_brief", request)
        self.assertEqual(url_template["theme_id"], "climate_public_agencies")
        self.assertIn("source_feeds", url_template)
        self.assertEqual(len(url_template["sources"]), 1)

    def test_write_theme_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "request.json"

            write_theme_request(
                registry_path=Path("config/daily_intelligence_themes.json"),
                theme_id="ai_infrastructure",
                output_path=output_path,
                title="Custom AI Infra News",
                related_project="AI Watch",
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["title"], "Custom AI Infra News")
            self.assertEqual(payload["related_project"], "AI Watch")
            self.assertIn("ai", payload["tags"])

    def test_parse_rss_feed_sources(self) -> None:
        feed = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>Climate update</title>
      <link>https://example.gov/climate</link>
      <pubDate>Tue, 18 Aug 2026 00:00:00 GMT</pubDate>
      <description><![CDATA[<p>Climate summary.</p>]]></description>
    </item>
  </channel>
</rss>
"""
        sources = parse_feed(
            feed,
            FeedConfig(
                url="https://example.gov/feed.xml",
                publisher="Example Agency",
                type="public_agency_feed",
                primary_source=True,
                reliability="high",
            ),
        )

        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["title"], "Climate update")
        self.assertEqual(sources[0]["date"], "2026-08-18")
        self.assertEqual(sources[0]["summary"], "Climate summary.")

    def test_write_feed_sources_rejects_empty_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                write_feed_sources([], Path(temp_dir) / "sources.json", theme_id="test")

    def test_clean_summary_removes_feed_boilerplate(self) -> None:
        self.assertEqual(
            clean_summary("Smoke plume observed. The post Fire Update appeared first on NASA Science .", "NASA Earth Observatory"),
            "Smoke plume observed.",
        )
        self.assertEqual(
            clean_summary(
                "000 ABNT20 KNHC 172317 TWOAT Tropical Weather Outlook NWS National Hurricane Center Miami FL "
                "For the North Atlantic...Caribbean Sea and the Gulf of America: "
                "Tropical cyclone formation is not expected during the next 7 days. $$ Forecaster Pasch",
                "NOAA National Hurricane Center",
            ),
            "Tropical cyclone formation is not expected during the next 7 days.",
        )

    def test_collect_sources_from_feeds_skips_failed_feed(self) -> None:
        original_fetch = feed_ingestion_module.fetch_feed_text

        def fake_fetch(url: str, timeout_seconds: int = 15) -> str:
            if "bad" in url:
                raise OSError("feed unavailable")
            title = "Valid item"
            link = "https://example.gov/valid"
            if "second" in url:
                title = "Second feed item"
                link = "https://example.gov/second"
            return f"""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <pubDate>Tue, 18 Aug 2026 00:00:00 GMT</pubDate>
      <description>Valid summary.</description>
    </item>
  </channel>
</rss>
"""

        try:
            feed_ingestion_module.fetch_feed_text = fake_fetch
            sources = collect_sources_from_feeds(
                [
                    FeedConfig("https://example.gov/bad.xml", "Bad", "feed", True, "high"),
                    FeedConfig("https://example.gov/good.xml", "Good", "feed", True, "high"),
                    FeedConfig("https://example.gov/second.xml", "Second", "feed", True, "high"),
                ],
                limit=3,
            )
        finally:
            feed_ingestion_module.fetch_feed_text = original_fetch

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["title"], "Valid item")
        self.assertEqual(sources[1]["title"], "Second feed item")

    def test_validate_required_fields_reports_missing_values(self) -> None:
        result = validate_required_fields({"title": "Only title"}, {"required": ["title", "objective"]})

        self.assertFalse(result.valid)
        self.assertEqual(result.missing_fields, ["objective"])

    def test_missing_frontmatter_fields(self) -> None:
        rules = {"frontmatter_required": ["type", "status", "run_id"]}
        missing = missing_frontmatter_fields({"type": "decision"}, rules)

        self.assertEqual(missing, ["status", "run_id"])

    def test_validate_named_contract(self) -> None:
        contracts_path = Path("config/io_schemas.json")
        payload = {
            "sources": [{"title": "Example"}],
            "fact_candidates": ["Example fact candidate"],
            "collection_gaps": ["Example gap"],
        }

        result = validate_named_contract(payload, "source_digest", contracts_path)

        self.assertTrue(result.valid)

    def test_run_pipeline_creates_obsidian_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            sources_path = root / "sources.md"
            vault_path = root / "vault"

            request_path.write_text(
                json.dumps(
                    {
                        "title": "Test Request",
                        "objective": "Evaluate a topic",
                        "decision_context": "Decide whether to track it",
                        "scope": ["market"],
                        "related_project": "Test Project",
                        "priority": "high",
                        "requested_output": "Strategic Intelligence",
                        "tags": ["test"],
                    }
                ),
                encoding="utf-8",
            )
            sources_path.write_text(
                """# Source Digest

## Source 1

- title: Example
- url: https://example.com
- type: news
- date: 2026-08-11
- summary: Example summary.
""",
                encoding="utf-8",
            )

            result = run_pipeline(request_path, sources_path, vault_path)

            self.assertEqual(len(result.created_notes), 6)
            self.assertEqual(len(result.run_files), 9)
            for note in result.created_notes:
                self.assertTrue(note.exists())
            for run_file in result.run_files:
                self.assertTrue(run_file.exists())
            self.assertTrue((vault_path / "Templates" / "Intelligence Report.md").exists())

            evaluation = evaluate_run(root / "runs" / result.run_id)
            self.assertGreaterEqual(evaluation["score"], 80)
            self.assertTrue(evaluation["passed"])

    def test_run_pipeline_creates_daily_intelligence_for_news_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            sources_path = root / "sources.md"
            vault_path = root / "vault"
            request_path.write_text(
                json.dumps(
                    {
                        "title": "Environment News",
                        "objective": "Create a news brief",
                        "decision_context": "Decide whether to track it",
                        "scope": ["climate"],
                        "related_project": "Test Project",
                        "priority": "high",
                        "requested_output": "Daily Intelligence / News Brief",
                        "tags": ["test"],
                    }
                ),
                encoding="utf-8",
            )
            sources_path.write_text(
                """# Source Digest

## Source 1

- title: Example
- url: https://example.com
- type: news
- date: 2026-08-17
- summary: Example climate summary.
""",
                encoding="utf-8",
            )

            result = run_pipeline(request_path, sources_path, vault_path)

            self.assertEqual(len(result.created_notes), 7)
            self.assertTrue(any(note.parent.name == "10_Daily_Intelligence" for note in result.created_notes))
            daily_note = next(note for note in result.created_notes if note.parent.name == "10_Daily_Intelligence")
            daily_text = daily_note.read_text(encoding="utf-8")
            self.assertIn("## Potential Implications", daily_text)
            self.assertIn("## Confidence / Uncertainty", daily_text)

    def test_check_obsidian_write_uses_configured_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            vault_path = root / "vault"
            settings_path = root / "settings.json"
            vault_path.mkdir()
            settings_path.write_text(
                json.dumps(
                    {
                        "obsidian_vault_path": str(vault_path),
                        "obsidian_output_root": "AI_Intelligence_Unit",
                    }
                ),
                encoding="utf-8",
            )

            vault, output_root = resolve_obsidian_paths(settings_path)
            result = check_obsidian_write(settings_path)

            self.assertEqual(vault, vault_path)
            self.assertEqual(output_root, vault_path / "AI_Intelligence_Unit")
            self.assertTrue(result.ok)
            self.assertTrue(output_root.exists())
            self.assertFalse((output_root / ".codex_write_test.md").exists())

    def test_run_pipeline_to_obsidian_writes_under_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            sources_path = root / "sources.md"
            vault_path = root / "vault"
            settings_path = root / "settings.json"
            vault_path.mkdir()
            settings_path.write_text(
                json.dumps(
                    {
                        "obsidian_vault_path": str(vault_path),
                        "obsidian_output_root": "AI_Intelligence_Unit",
                    }
                ),
                encoding="utf-8",
            )
            request_path.write_text(
                json.dumps(
                    {
                        "title": "Direct Obsidian Test",
                        "objective": "Verify direct Obsidian storage",
                        "decision_context": "Decide whether direct writing works",
                        "scope": ["storage"],
                        "related_project": "Test Project",
                        "priority": "high",
                        "requested_output": "Strategic Intelligence",
                        "tags": ["test"],
                    }
                ),
                encoding="utf-8",
            )
            sources_path.write_text(
                """# Source Digest

## Source 1

- title: Example
- url: https://example.com
- type: web_page
- date: 2026-08-17
- publisher: Example
- primary_source: false
- reliability: medium
- summary: Example summary.
""",
                encoding="utf-8",
            )

            result = run_pipeline_to_obsidian(request_path, sources_path, settings_path)
            output_root = vault_path / "AI_Intelligence_Unit"

            self.assertEqual(len(result.created_notes), 6)
            self.assertTrue((output_root / "runs" / result.run_id).exists())
            self.assertTrue((output_root / "30_Strategic_Intelligence" / "For Mobile" / "latest.txt").exists())
            self.assertGreaterEqual(len(result.mobile_files), 2)
            for note in result.created_notes:
                self.assertTrue(note.exists())
                self.assertTrue(output_root in note.parents)

    def test_write_mobile_review_copies_creates_txt_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_root = root / "vault"
            daily_note = output_root / "10_Daily_Intelligence" / "daily.md"
            report_note = output_root / "30_Strategic_Intelligence" / "report.md"
            daily_note.parent.mkdir(parents=True)
            report_note.parent.mkdir(parents=True)
            daily_note.write_text("---\ntype: daily_intelligence\n---\n\n# Daily\n\nMobile readable.", encoding="utf-8")
            report_note.write_text("# Report\n\n[Source](https://example.com)\n\n[[Decision Note]]", encoding="utf-8")

            files = write_mobile_review_copies(
                output_root=output_root,
                pipeline_result=PipelineResult(
                    run_id="20260817-000000-000000",
                    created_notes=[report_note, daily_note],
                    run_files=[],
                ),
                settings={"mobile_review_copy": {"enabled": True, "folder_name": "For Mobile"}},
                title="Mobile Test",
            )

            daily_txt = output_root / "10_Daily_Intelligence" / "For Mobile" / "daily.txt"
            report_txt = output_root / "30_Strategic_Intelligence" / "For Mobile" / "report.txt"
            self.assertTrue(daily_txt.exists())
            self.assertTrue((output_root / "10_Daily_Intelligence" / "For Mobile" / "latest.txt").exists())
            self.assertTrue(report_txt.exists())
            self.assertNotIn("type: daily_intelligence", daily_txt.read_text(encoding="utf-8"))
            self.assertIn("Mobile readable.", daily_txt.read_text(encoding="utf-8"))
            self.assertIn("URL: https://example.com", report_txt.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(files), 4)

    def test_run_evaluation_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cases_path = root / "cases"
            cases_path.mkdir()
            for case_id in ["liquid_cooling", "obsidian_ai_workflow", "agent_red_team"]:
                (cases_path / f"{case_id}_request.json").write_text(
                    json.dumps(
                        {
                            "title": f"{case_id} request",
                            "objective": "Evaluate the case",
                            "decision_context": "Decide whether to continue",
                            "scope": ["market"],
                            "related_project": "Test Project",
                            "priority": "high",
                            "requested_output": "Strategic Intelligence",
                            "tags": ["test"],
                        }
                    ),
                    encoding="utf-8",
                )
                (cases_path / f"{case_id}_sources.md").write_text(
                    """# Source Digest

## Source 1

- title: Example
- url: https://example.com
- type: news
- date: 2026-08-11
- publisher: Example
- primary_source: false
- reliability: medium
- summary: Example summary.

## Source 2

- title: Example 2
- url: https://example.com/2
- type: news
- date: 2026-08-11
- publisher: Example
- primary_source: false
- reliability: medium
- summary: Example summary 2.

## Source 3

- title: Example 3
- url: https://example.com/3
- type: news
- date: 2026-08-11
- publisher: Example
- primary_source: false
- reliability: medium
- summary: Example summary 3.
""",
                    encoding="utf-8",
                )

            report_path = run_evaluation_cases(
                cases_path=cases_path,
                vault_path=root / "evaluation_vault",
                report_path=root / "reports" / "summary.json",
            )

            summary = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["case_count"], 3)
            self.assertTrue(summary["all_passed"])

    def test_format_git_preflight(self) -> None:
        text = format_preflight(
            GitPreflightResult(
                is_git_repo=True,
                branch="main",
                clean=True,
                has_remote=False,
                gh_available=False,
                status="",
                remotes="",
            )
        )

        self.assertIn("is_git_repo=true", text)
        self.assertIn("branch=main", text)
        self.assertIn("has_remote=false", text)

    def test_write_source_digest_from_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "urls.json"
            output_path = root / "sources.md"
            input_path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "title": "Example",
                                "url": "https://example.com/source",
                                "type": "web_page",
                                "date": "2026-08-17",
                                "publisher": "Example Publisher",
                                "primary_source": False,
                                "reliability": "medium",
                                "summary": "Example summary.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            write_source_digest_from_urls(input_path, output_path)

            text = output_path.read_text(encoding="utf-8")
            self.assertIn("# Source Digest", text)
            self.assertIn("- url: https://example.com/source", text)
            self.assertIn("- primary_source: false", text)
            self.assertTrue(is_http_url("https://example.com/source"))
            self.assertFalse(is_http_url("not-a-url"))

    def test_extract_page_metadata(self) -> None:
        metadata = extract_page_metadata(
            """<!doctype html>
<html>
<head>
  <title>Fallback Title</title>
  <meta property="og:title" content="Open Graph Title">
  <meta name="description" content="Example description.">
</head>
<body>
  <script>ignored()</script>
  <h1>Heading</h1>
  <p>Main body text for extraction.</p>
</body>
</html>"""
        )

        self.assertEqual(metadata.title, "Open Graph Title")
        self.assertEqual(metadata.description, "Example description.")
        self.assertIn("Main body text", metadata.text_excerpt)

    def test_extract_page_metadata_citation_fields(self) -> None:
        metadata = extract_page_metadata(
            """<!doctype html>
<html>
<head>
  <title>Example</title>
  <link rel="canonical" href="https://example.gov/report">
  <meta property="og:site_name" content="Example Government">
  <meta property="article:published_time" content="2026-08-17">
</head>
<body><p>Report body.</p></body>
</html>"""
        )

        self.assertEqual(metadata.publisher, "Example Government")
        self.assertEqual(metadata.published_date, "2026-08-17")
        self.assertEqual(metadata.canonical_url, "https://example.gov/report")
        self.assertEqual(metadata.reliability, "high")

    def test_enrich_url_sources_records_fetch_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "urls.json"
            output_path = root / "enriched.json"
            input_path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "title": "Invalid local URL",
                                "url": "https://127.0.0.1:1/unreachable",
                                "type": "web_page",
                                "date": "2026-08-17",
                                "publisher": "Local",
                                "primary_source": False,
                                "reliability": "unknown",
                                "summary": "Expected to fail.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            enrich_url_sources_file(input_path, output_path, timeout_seconds=1)

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("fetch_error", payload["sources"][0])

    def test_run_pipeline_from_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            urls_path = root / "urls.json"
            vault_path = root / "vault"
            work_dir = root / "work"
            request_path.write_text(
                json.dumps(
                    {
                        "title": "URL Run Test",
                        "objective": "Evaluate URL sources",
                        "decision_context": "Decide whether URL flow works",
                        "scope": ["sources"],
                        "related_project": "Test Project",
                        "priority": "high",
                        "requested_output": "Strategic Intelligence",
                        "tags": ["test"],
                    }
                ),
                encoding="utf-8",
            )
            urls_path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "title": "Example",
                                "url": "https://example.com/source",
                                "type": "web_page",
                                "date": "2026-08-17",
                                "publisher": "Example Publisher",
                                "primary_source": False,
                                "reliability": "medium",
                                "summary": "Example summary.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_pipeline_from_urls(request_path, urls_path, vault_path, work_dir)

            self.assertTrue(result.source_digest_path.exists())
            self.assertEqual(len(result.pipeline_result.created_notes), 6)

    def test_run_urls_to_obsidian_writes_under_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            request_path = root / "request.json"
            urls_path = root / "urls.json"
            settings_path = root / "settings.json"
            vault_path = root / "vault"
            work_dir = root / "work"
            vault_path.mkdir()
            settings_path.write_text(
                json.dumps(
                    {
                        "obsidian_vault_path": str(vault_path),
                        "obsidian_output_root": "AI_Intelligence_Unit",
                    }
                ),
                encoding="utf-8",
            )
            request_path.write_text(
                json.dumps(
                    {
                        "title": "URL Direct Obsidian Test",
                        "objective": "Verify URL direct Obsidian storage",
                        "decision_context": "Decide whether the URL direct flow works",
                        "scope": ["sources"],
                        "related_project": "Test Project",
                        "priority": "high",
                        "requested_output": "Strategic Intelligence",
                        "tags": ["test"],
                    }
                ),
                encoding="utf-8",
            )
            urls_path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "title": "Example",
                                "url": "https://example.com/source",
                                "type": "web_page",
                                "date": "2026-08-17",
                                "publisher": "Example Publisher",
                                "primary_source": False,
                                "reliability": "medium",
                                "summary": "Example summary.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_urls_to_obsidian(request_path, urls_path, settings_path, work_dir)
            output_root = vault_path / "AI_Intelligence_Unit"

            self.assertTrue(result.source_digest_path.exists())
            self.assertEqual(len(result.pipeline_result.created_notes), 6)
            self.assertTrue((output_root / "runs" / result.pipeline_result.run_id).exists())
            self.assertTrue((output_root / "30_Strategic_Intelligence" / "For Mobile" / "latest.txt").exists())
            self.assertGreaterEqual(len(result.pipeline_result.mobile_files), 2)

    def test_run_theme_urls_to_obsidian(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            urls_path = root / "urls.json"
            settings_path = root / "settings.json"
            vault_path = root / "vault"
            work_dir = root / "work"
            vault_path.mkdir()
            settings_path.write_text(
                json.dumps(
                    {
                        "obsidian_vault_path": str(vault_path),
                        "obsidian_output_root": "AI_Intelligence_Unit",
                    }
                ),
                encoding="utf-8",
            )
            urls_path.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "title": "Climate source",
                                "url": "https://example.com/climate",
                                "type": "public_agency_news",
                                "date": "2026-08-18",
                                "publisher": "Example Agency",
                                "primary_source": True,
                                "reliability": "high",
                                "summary": "Climate monitoring summary.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_theme_urls_to_obsidian(
                theme_id="climate_public_agencies",
                url_sources_path=urls_path,
                settings_path=settings_path,
                registry_path=Path("config/daily_intelligence_themes.json"),
                work_dir=work_dir,
            )
            output_root = vault_path / "AI_Intelligence_Unit"

            self.assertTrue(result.request_path.exists())
            self.assertTrue(result.url_run_result.source_digest_path.exists())
            self.assertTrue(any(note.parent.name == "10_Daily_Intelligence" for note in result.url_run_result.pipeline_result.created_notes))
            self.assertTrue((output_root / "10_Daily_Intelligence" / "For Mobile" / "latest.txt").exists())

    def test_run_theme_feeds_to_obsidian_with_mocked_collector(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            settings_path = root / "settings.json"
            vault_path = root / "vault"
            registry_path = root / "themes.json"
            work_dir = root / "work"
            vault_path.mkdir()
            settings_path.write_text(
                json.dumps(
                    {
                        "obsidian_vault_path": str(vault_path),
                        "obsidian_output_root": "AI_Intelligence_Unit",
                    }
                ),
                encoding="utf-8",
            )
            registry_path.write_text(
                json.dumps(
                    {
                        "themes": {
                            "mock_theme": {
                                "title": "Mock Feed News",
                                "objective": "Create feed news.",
                                "decision_context": "Decide whether to monitor it.",
                                "scope": ["mock"],
                                "related_project": "Daily Intelligence",
                                "priority": "high",
                                "tags": ["mock"],
                                "news_brief": {"headline": "Mock headline"},
                                "source_feeds": [
                                    {
                                        "url": "https://example.gov/feed.xml",
                                        "publisher": "Example Agency",
                                        "type": "public_agency_feed",
                                        "primary_source": True,
                                        "reliability": "high",
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            import src.intel_mvp.themes as themes_module

            original = themes_module.collect_sources_from_feeds

            def fake_collect(_feed_configs, limit=5, timeout_seconds=15):
                return [
                    {
                        "title": "Mock source",
                        "url": "https://example.gov/mock",
                        "type": "public_agency_feed",
                        "date": "2026-08-18",
                        "publisher": "Example Agency",
                        "primary_source": True,
                        "reliability": "high",
                        "summary": "Mock feed summary.",
                    }
                ]

            themes_module.collect_sources_from_feeds = fake_collect
            try:
                result = run_theme_feeds_to_obsidian(
                    theme_id="mock_theme",
                    settings_path=settings_path,
                    registry_path=registry_path,
                    work_dir=work_dir,
                )
            finally:
                themes_module.collect_sources_from_feeds = original

            output_root = vault_path / "AI_Intelligence_Unit"
            self.assertTrue((work_dir / "mock_theme" / "mock_theme.feed_sources.json").exists())
            self.assertTrue(result.request_path.exists())
            self.assertTrue((output_root / "10_Daily_Intelligence" / "For Mobile" / "latest.txt").exists())


if __name__ == "__main__":
    unittest.main()
