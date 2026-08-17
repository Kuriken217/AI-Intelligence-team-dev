from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from .evaluation import write_evaluation_report
    from .obsidian_direct import (
        check_obsidian_write,
        run_pipeline_to_obsidian,
        run_theme_feeds_to_obsidian,
        run_theme_urls_to_obsidian,
        run_urls_to_obsidian,
    )
    from .pipeline import run_pipeline
    from .review import append_decision, append_result, append_review
    from .source_ingestion import write_source_digest_from_urls
    from .themes import collect_theme_feed_sources, load_theme_registry, list_theme_rows, write_theme_request, write_theme_url_template
    from .url_run import run_pipeline_from_urls
    from .web_enrichment import enrich_url_sources_file
except ImportError:
    from evaluation import write_evaluation_report
    from obsidian_direct import (
        check_obsidian_write,
        run_pipeline_to_obsidian,
        run_theme_feeds_to_obsidian,
        run_theme_urls_to_obsidian,
        run_urls_to_obsidian,
    )
    from pipeline import run_pipeline
    from review import append_decision, append_result, append_review
    from source_ingestion import write_source_digest_from_urls
    from themes import collect_theme_feed_sources, load_theme_registry, list_theme_rows, write_theme_request, write_theme_url_template
    from url_run import run_pipeline_from_urls
    from web_enrichment import enrich_url_sources_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI Intelligence Unit MVP pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Generate Obsidian notes from a request and source digest.")
    run_parser.add_argument("--request", required=True, help="Path to the information request JSON file.")
    run_parser.add_argument("--sources", required=True, help="Path to the source digest Markdown file.")
    run_parser.add_argument("--vault", required=True, help="Path to the Obsidian vault output directory.")

    obsidian_check_parser = subparsers.add_parser("check-obsidian-write", help="Verify direct write access to the configured Obsidian vault.")
    obsidian_check_parser.add_argument("--settings", default="config/user_settings.json", help="Path to local user settings JSON.")

    run_obsidian_parser = subparsers.add_parser("run-to-obsidian", help="Generate notes directly into the configured Obsidian vault.")
    run_obsidian_parser.add_argument("--request", required=True, help="Path to the information request JSON file.")
    run_obsidian_parser.add_argument("--sources", required=True, help="Path to the source digest Markdown file.")
    run_obsidian_parser.add_argument("--settings", default="config/user_settings.json", help="Path to local user settings JSON.")

    run_urls_obsidian_parser = subparsers.add_parser(
        "run-urls-to-obsidian",
        help="Fetch URL sources and generate notes directly into the configured Obsidian vault.",
    )
    run_urls_obsidian_parser.add_argument("--request", required=True, help="Path to the information request JSON file.")
    run_urls_obsidian_parser.add_argument("--urls", required=True, help="Path to URL source JSON file.")
    run_urls_obsidian_parser.add_argument("--settings", default="config/user_settings.json", help="Path to local user settings JSON.")
    run_urls_obsidian_parser.add_argument("--work-dir", default="work/url_runs", help="Directory for generated source digests.")
    run_urls_obsidian_parser.add_argument("--enrich", action="store_true", help="Fetch URL pages before creating the source digest.")
    run_urls_obsidian_parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds when --enrich is used.")

    review_parser = subparsers.add_parser("review", help="Append a user review to an Obsidian note.")
    review_parser.add_argument("--note", required=True, help="Path to the note to update.")
    review_parser.add_argument("--status", required=True, choices=["approved", "rejected", "watchlist", "user_review"])
    review_parser.add_argument("--comment", default="", help="Review comment.")

    decide_parser = subparsers.add_parser("decide", help="Append a user decision to a decision note.")
    decide_parser.add_argument("--note", required=True, help="Path to the decision note to update.")
    decide_parser.add_argument("--decision", required=True, help="Decision text.")
    decide_parser.add_argument("--reason", default="", help="Decision rationale.")

    result_parser = subparsers.add_parser("result", help="Append an action result to a result note.")
    result_parser.add_argument("--note", required=True, help="Path to the result note to update.")
    result_parser.add_argument("--action", required=True, help="Action taken.")
    result_parser.add_argument("--result", required=True, help="Observed result.")
    result_parser.add_argument("--feedback", default="", help="Feedback for future intelligence.")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate an intelligence run bundle.")
    evaluate_parser.add_argument("--run", required=True, help="Path to the run bundle directory.")
    evaluate_parser.add_argument("--output", required=True, help="Path to write the evaluation JSON report.")

    ingest_parser = subparsers.add_parser("ingest-urls", help="Convert URL source JSON into a source digest Markdown file.")
    ingest_parser.add_argument("--input", required=True, help="Path to URL source JSON file.")
    ingest_parser.add_argument("--output", required=True, help="Path to write source digest Markdown.")

    enrich_parser = subparsers.add_parser("enrich-urls", help="Fetch URL pages and add metadata to URL source JSON.")
    enrich_parser.add_argument("--input", required=True, help="Path to URL source JSON file.")
    enrich_parser.add_argument("--output", required=True, help="Path to write enriched URL source JSON.")
    enrich_parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds.")

    run_urls_parser = subparsers.add_parser("run-from-urls", help="Generate an intelligence run from URL source JSON.")
    run_urls_parser.add_argument("--request", required=True, help="Path to the information request JSON file.")
    run_urls_parser.add_argument("--urls", required=True, help="Path to URL source JSON file.")
    run_urls_parser.add_argument("--vault", required=True, help="Path to the Obsidian vault output directory.")
    run_urls_parser.add_argument("--work-dir", default="work/url_runs", help="Directory for generated source digests.")
    run_urls_parser.add_argument("--enrich", action="store_true", help="Fetch URL pages before creating the source digest.")
    run_urls_parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds when --enrich is used.")

    list_themes_parser = subparsers.add_parser("list-themes", help="List configured Daily Intelligence themes.")
    list_themes_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")

    create_theme_request_parser = subparsers.add_parser("create-theme-request", help="Create an information request JSON from a theme.")
    create_theme_request_parser.add_argument("--theme", required=True, help="Theme id from the theme registry.")
    create_theme_request_parser.add_argument("--output", required=True, help="Path to write the generated request JSON.")
    create_theme_request_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")
    create_theme_request_parser.add_argument("--title", default=None, help="Optional title override.")
    create_theme_request_parser.add_argument("--related-project", default=None, help="Optional related_project override.")

    create_theme_urls_parser = subparsers.add_parser("create-theme-urls", help="Create a URL source template JSON from a theme.")
    create_theme_urls_parser.add_argument("--theme", required=True, help="Theme id from the theme registry.")
    create_theme_urls_parser.add_argument("--output", required=True, help="Path to write the generated URL source JSON.")
    create_theme_urls_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")

    run_theme_parser = subparsers.add_parser("run-theme-to-obsidian", help="Generate a themed Daily Intelligence run directly into Obsidian.")
    run_theme_parser.add_argument("--theme", required=True, help="Theme id from the theme registry.")
    run_theme_parser.add_argument("--urls", required=True, help="Path to filled URL source JSON file.")
    run_theme_parser.add_argument("--settings", default="config/user_settings.json", help="Path to local user settings JSON.")
    run_theme_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")
    run_theme_parser.add_argument("--work-dir", default="work/theme_runs", help="Directory for generated theme request and source digests.")
    run_theme_parser.add_argument("--title", default=None, help="Optional title override.")
    run_theme_parser.add_argument("--related-project", default=None, help="Optional related_project override.")
    run_theme_parser.add_argument("--enrich", action="store_true", help="Fetch URL pages before creating the source digest.")
    run_theme_parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds when --enrich is used.")

    collect_theme_feeds_parser = subparsers.add_parser("collect-theme-feeds", help="Collect URL sources from a theme's configured feeds.")
    collect_theme_feeds_parser.add_argument("--theme", required=True, help="Theme id from the theme registry.")
    collect_theme_feeds_parser.add_argument("--output", required=True, help="Path to write collected URL source JSON.")
    collect_theme_feeds_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")
    collect_theme_feeds_parser.add_argument("--limit", type=int, default=5, help="Maximum number of feed items to collect.")
    collect_theme_feeds_parser.add_argument("--timeout", type=int, default=15, help="Feed fetch timeout in seconds.")

    run_theme_feeds_parser = subparsers.add_parser(
        "run-theme-feeds-to-obsidian",
        help="Collect a theme's configured feeds and run the Daily Intelligence flow into Obsidian.",
    )
    run_theme_feeds_parser.add_argument("--theme", required=True, help="Theme id from the theme registry.")
    run_theme_feeds_parser.add_argument("--settings", default="config/user_settings.json", help="Path to local user settings JSON.")
    run_theme_feeds_parser.add_argument("--registry", default="config/daily_intelligence_themes.json", help="Path to theme registry JSON.")
    run_theme_feeds_parser.add_argument("--work-dir", default="work/theme_feed_runs", help="Directory for generated feed sources and theme request.")
    run_theme_feeds_parser.add_argument("--title", default=None, help="Optional title override.")
    run_theme_feeds_parser.add_argument("--related-project", default=None, help="Optional related_project override.")
    run_theme_feeds_parser.add_argument("--limit", type=int, default=5, help="Maximum number of feed items to collect.")
    run_theme_feeds_parser.add_argument("--enrich", action="store_true", help="Fetch collected URL pages before creating the source digest.")
    run_theme_feeds_parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds.")

    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        result = run_pipeline(
            request_path=Path(args.request),
            sources_path=Path(args.sources),
            vault_path=Path(args.vault),
        )
        print(f"Created intelligence run: {result.run_id}")
        print("Run files:")
        for run_file in result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in result.created_notes:
            print(f"- {note}")
        if result.mobile_files:
            print("Mobile review files:")
            for mobile_file in result.mobile_files:
                print(f"- {mobile_file}")
        return 0

    if args.command == "check-obsidian-write":
        result = check_obsidian_write(Path(args.settings))
        print(f"ok={str(result.ok).lower()}")
        print(f"vault_path={result.vault_path}")
        print(f"output_root={result.output_root}")
        print(f"message={result.message}")
        return 0 if result.ok else 1

    if args.command == "run-to-obsidian":
        result = run_pipeline_to_obsidian(
            request_path=Path(args.request),
            sources_path=Path(args.sources),
            settings_path=Path(args.settings),
        )
        print(f"Created intelligence run: {result.run_id}")
        print("Run files:")
        for run_file in result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in result.created_notes:
            print(f"- {note}")
        if result.mobile_files:
            print("Mobile review files:")
            for mobile_file in result.mobile_files:
                print(f"- {mobile_file}")
        return 0

    if args.command == "run-urls-to-obsidian":
        result = run_urls_to_obsidian(
            request_path=Path(args.request),
            url_sources_path=Path(args.urls),
            settings_path=Path(args.settings),
            work_dir=Path(args.work_dir),
            enrich=args.enrich,
            timeout_seconds=args.timeout,
        )
        print(f"Wrote source digest: {result.source_digest_path}")
        if result.enriched_sources_path:
            print(f"Wrote enriched URL sources: {result.enriched_sources_path}")
        print(f"Created intelligence run: {result.pipeline_result.run_id}")
        print("Run files:")
        for run_file in result.pipeline_result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in result.pipeline_result.created_notes:
            print(f"- {note}")
        if result.pipeline_result.mobile_files:
            print("Mobile review files:")
            for mobile_file in result.pipeline_result.mobile_files:
                print(f"- {mobile_file}")
        return 0

    if args.command == "review":
        append_review(Path(args.note), args.status, args.comment)
        print(f"Updated review note: {args.note}")
        return 0

    if args.command == "decide":
        append_decision(Path(args.note), args.decision, args.reason)
        print(f"Updated decision note: {args.note}")
        return 0

    if args.command == "result":
        append_result(Path(args.note), args.action, args.result, args.feedback)
        print(f"Updated result note: {args.note}")
        return 0

    if args.command == "evaluate":
        output_path = write_evaluation_report(Path(args.run), Path(args.output))
        print(f"Wrote evaluation report: {output_path}")
        return 0

    if args.command == "ingest-urls":
        output_path = write_source_digest_from_urls(Path(args.input), Path(args.output))
        print(f"Wrote source digest: {output_path}")
        return 0

    if args.command == "enrich-urls":
        output_path = enrich_url_sources_file(Path(args.input), Path(args.output), timeout_seconds=args.timeout)
        print(f"Wrote enriched URL sources: {output_path}")
        return 0

    if args.command == "run-from-urls":
        result = run_pipeline_from_urls(
            request_path=Path(args.request),
            url_sources_path=Path(args.urls),
            vault_path=Path(args.vault),
            work_dir=Path(args.work_dir),
            enrich=args.enrich,
            timeout_seconds=args.timeout,
        )
        print(f"Wrote source digest: {result.source_digest_path}")
        if result.enriched_sources_path:
            print(f"Wrote enriched URL sources: {result.enriched_sources_path}")
        print(f"Created intelligence run: {result.pipeline_result.run_id}")
        print("Run files:")
        for run_file in result.pipeline_result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in result.pipeline_result.created_notes:
            print(f"- {note}")
        return 0

    if args.command == "list-themes":
        registry = load_theme_registry(Path(args.registry))
        print("Daily Intelligence themes:")
        for theme_id, display_name, priority in list_theme_rows(registry):
            suffix = f" ({priority})" if priority else ""
            print(f"- {theme_id}: {display_name}{suffix}")
        return 0

    if args.command == "create-theme-request":
        output_path = write_theme_request(
            registry_path=Path(args.registry),
            theme_id=args.theme,
            output_path=Path(args.output),
            title=args.title,
            related_project=args.related_project,
        )
        print(f"Wrote theme request: {output_path}")
        return 0

    if args.command == "create-theme-urls":
        output_path = write_theme_url_template(
            registry_path=Path(args.registry),
            theme_id=args.theme,
            output_path=Path(args.output),
        )
        print(f"Wrote theme URL template: {output_path}")
        return 0

    if args.command == "run-theme-to-obsidian":
        result = run_theme_urls_to_obsidian(
            theme_id=args.theme,
            url_sources_path=Path(args.urls),
            settings_path=Path(args.settings),
            registry_path=Path(args.registry),
            work_dir=Path(args.work_dir),
            title=args.title,
            related_project=args.related_project,
            enrich=args.enrich,
            timeout_seconds=args.timeout,
        )
        url_run = result.url_run_result
        print(f"Wrote theme request: {result.request_path}")
        print(f"Wrote source digest: {url_run.source_digest_path}")
        if url_run.enriched_sources_path:
            print(f"Wrote enriched URL sources: {url_run.enriched_sources_path}")
        print(f"Created intelligence run: {url_run.pipeline_result.run_id}")
        print("Run files:")
        for run_file in url_run.pipeline_result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in url_run.pipeline_result.created_notes:
            print(f"- {note}")
        if url_run.pipeline_result.mobile_files:
            print("Mobile review files:")
            for mobile_file in url_run.pipeline_result.mobile_files:
                print(f"- {mobile_file}")
        return 0

    if args.command == "collect-theme-feeds":
        output_path = collect_theme_feed_sources(
            registry_path=Path(args.registry),
            theme_id=args.theme,
            output_path=Path(args.output),
            limit=args.limit,
            timeout_seconds=args.timeout,
        )
        print(f"Wrote collected theme feed sources: {output_path}")
        return 0

    if args.command == "run-theme-feeds-to-obsidian":
        result = run_theme_feeds_to_obsidian(
            theme_id=args.theme,
            settings_path=Path(args.settings),
            registry_path=Path(args.registry),
            work_dir=Path(args.work_dir),
            title=args.title,
            related_project=args.related_project,
            limit=args.limit,
            enrich=args.enrich,
            timeout_seconds=args.timeout,
        )
        url_run = result.url_run_result
        print(f"Wrote theme request: {result.request_path}")
        print(f"Wrote source digest: {url_run.source_digest_path}")
        if url_run.enriched_sources_path:
            print(f"Wrote enriched URL sources: {url_run.enriched_sources_path}")
        print(f"Created intelligence run: {url_run.pipeline_result.run_id}")
        print("Run files:")
        for run_file in url_run.pipeline_result.run_files:
            print(f"- {run_file}")
        print("Obsidian notes:")
        for note in url_run.pipeline_result.created_notes:
            print(f"- {note}")
        if url_run.pipeline_result.mobile_files:
            print("Mobile review files:")
            for mobile_file in url_run.pipeline_result.mobile_files:
                print(f"- {mobile_file}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
