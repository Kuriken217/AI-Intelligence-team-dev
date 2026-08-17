from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PageMetadata:
    title: str
    description: str
    text_excerpt: str


def fetch_url_text(url: str, timeout_seconds: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "AI-Intelligence-Unit-MVP/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("content-type", "")
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read(1_000_000)
    except URLError as error:
        raise ValueError(f"Could not fetch URL: {url}") from error

    if "html" not in content_type and content_type:
        raise ValueError(f"URL did not return HTML content: {content_type}")
    return body.decode(charset, errors="replace")


def extract_page_metadata(html_text: str, max_excerpt_chars: int = 700) -> PageMetadata:
    title = extract_title(html_text)
    description = extract_meta_description(html_text)
    text_excerpt = extract_text_excerpt(html_text, max_excerpt_chars)
    return PageMetadata(title=title, description=description, text_excerpt=text_excerpt)


def extract_title(html_text: str) -> str:
    og_title = extract_meta_property(html_text, "og:title")
    if og_title:
        return og_title
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_meta_description(html_text: str) -> str:
    return extract_meta_name(html_text, "description") or extract_meta_property(html_text, "og:description")


def extract_meta_name(html_text: str, name: str) -> str:
    pattern = rf"<meta\b(?=[^>]*\bname=[\"']{re.escape(name)}[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>"
    match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_meta_property(html_text: str, property_name: str) -> str:
    pattern = rf"<meta\b(?=[^>]*\bproperty=[\"']{re.escape(property_name)}[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>"
    match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_text_excerpt(html_text: str, max_chars: int) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return clean_html_text(without_tags)[:max_chars].strip()


def clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def enrich_url_sources_file(input_path: Path, output_path: Path, timeout_seconds: int = 15) -> Path:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("URL source file must contain a 'sources' list.")

    enriched_sources: list[dict[str, Any]] = []
    for source in sources:
        enriched = dict(source)
        try:
            metadata = extract_page_metadata(fetch_url_text(str(source["url"]), timeout_seconds=timeout_seconds))
        except ValueError as error:
            enriched["fetch_error"] = str(error)
            enriched_sources.append(enriched)
            continue
        enriched["fetched_title"] = metadata.title
        enriched["fetched_description"] = metadata.description
        enriched["fetched_text_excerpt"] = metadata.text_excerpt
        if not enriched.get("title") and metadata.title:
            enriched["title"] = metadata.title
        if not enriched.get("summary"):
            enriched["summary"] = metadata.description or metadata.text_excerpt
        enriched_sources.append(enriched)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"sources": enriched_sources}, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
