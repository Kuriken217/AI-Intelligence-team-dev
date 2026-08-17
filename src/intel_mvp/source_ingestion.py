from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_URL_SOURCE_FIELDS = ["title", "url", "type", "date", "publisher", "primary_source", "reliability", "summary"]


def load_url_sources(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("URL source file must contain a 'sources' list.")
    for index, source in enumerate(sources, start=1):
        validate_url_source(source, index)
    return sources


def validate_url_source(source: dict[str, Any], index: int) -> None:
    missing = [field for field in REQUIRED_URL_SOURCE_FIELDS if field not in source or source[field] in ("", None)]
    if missing:
        raise ValueError(f"Source {index} is missing required fields: {', '.join(missing)}")
    if not is_http_url(str(source["url"])):
        raise ValueError(f"Source {index} has an invalid URL: {source['url']}")


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def render_source_digest(sources: list[dict[str, Any]]) -> str:
    blocks = ["# Source Digest"]
    for index, source in enumerate(sources, start=1):
        blocks.append(render_source_block(source, index))
    return "\n\n".join(blocks) + "\n"


def render_source_block(source: dict[str, Any], index: int) -> str:
    primary_source = str(source["primary_source"]).lower()
    return f"""## Source {index}

- title: {source["title"]}
- url: {source["url"]}
- type: {source["type"]}
- date: {source["date"]}
- publisher: {source["publisher"]}
- primary_source: {primary_source}
- reliability: {source["reliability"]}
- summary: {source["summary"]}"""


def write_source_digest_from_urls(input_path: Path, output_path: Path) -> Path:
    sources = load_url_sources(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_source_digest(sources), encoding="utf-8")
    return output_path

