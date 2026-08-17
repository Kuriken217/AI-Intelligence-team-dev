from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.intel_mvp.contracts import validate_named_contract, validate_required_fields
from src.intel_mvp.delta import build_prior_knowledge_delta
from src.intel_mvp.evaluate_cases import run_evaluation_cases
from src.intel_mvp.evaluation import evaluate_run
from src.intel_mvp.git_check import format_preflight, GitPreflightResult
from src.intel_mvp.pipeline import parse_source_digest, run_pipeline, slugify
from src.intel_mvp.prior_knowledge import build_search_terms, filter_search_terms, find_related_notes
from src.intel_mvp.review import append_decision, append_result, append_review
from src.intel_mvp.source_ingestion import is_http_url, write_source_digest_from_urls
from src.intel_mvp.source_quality import is_primary_source, source_quality_gaps
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


if __name__ == "__main__":
    unittest.main()
