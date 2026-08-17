from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .evaluation import write_evaluation_report
    from .pipeline import run_pipeline
    from .review import append_decision, append_result, append_review
except ImportError:
    from evaluation import write_evaluation_report
    from pipeline import run_pipeline
    from review import append_decision, append_result, append_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI Intelligence Unit MVP pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Generate Obsidian notes from a request and source digest.")
    run_parser.add_argument("--request", required=True, help="Path to the information request JSON file.")
    run_parser.add_argument("--sources", required=True, help="Path to the source digest Markdown file.")
    run_parser.add_argument("--vault", required=True, help="Path to the Obsidian vault output directory.")

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

    return parser


def main() -> int:
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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
