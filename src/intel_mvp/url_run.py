from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .pipeline import PipelineResult, run_pipeline
    from .source_ingestion import write_source_digest_from_urls
    from .web_enrichment import enrich_url_sources_file
except ImportError:
    from pipeline import PipelineResult, run_pipeline
    from source_ingestion import write_source_digest_from_urls
    from web_enrichment import enrich_url_sources_file


@dataclass(frozen=True)
class UrlRunResult:
    pipeline_result: PipelineResult
    source_digest_path: Path
    enriched_sources_path: Path | None


def run_pipeline_from_urls(
    request_path: Path,
    url_sources_path: Path,
    vault_path: Path,
    work_dir: Path,
    enrich: bool = False,
    timeout_seconds: int = 15,
) -> UrlRunResult:
    work_dir.mkdir(parents=True, exist_ok=True)

    input_for_digest = url_sources_path
    enriched_sources_path = None
    if enrich:
        enriched_sources_path = work_dir / f"{url_sources_path.stem}.enriched.json"
        enrich_url_sources_file(url_sources_path, enriched_sources_path, timeout_seconds=timeout_seconds)
        input_for_digest = enriched_sources_path

    source_digest_path = work_dir / f"{url_sources_path.stem}.sources.md"
    write_source_digest_from_urls(input_for_digest, source_digest_path)

    pipeline_result = run_pipeline(
        request_path=request_path,
        sources_path=source_digest_path,
        vault_path=vault_path,
    )

    return UrlRunResult(
        pipeline_result=pipeline_result,
        source_digest_path=source_digest_path,
        enriched_sources_path=enriched_sources_path,
    )

