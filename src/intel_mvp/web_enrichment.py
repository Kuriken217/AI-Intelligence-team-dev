from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PageMetadata:
    title: str
    description: str
    text_excerpt: str
    publisher: str
    published_date: str
    canonical_url: str
    reliability: str


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
    publisher = extract_publisher(html_text)
    published_date = extract_published_date(html_text)
    canonical_url = extract_canonical_url(html_text)
    reliability = estimate_reliability(publisher, canonical_url)
    return PageMetadata(
        title=title,
        description=description,
        text_excerpt=text_excerpt,
        publisher=publisher,
        published_date=published_date,
        canonical_url=canonical_url,
        reliability=reliability,
    )


def extract_title(html_text: str) -> str:
    og_title = extract_meta_property(html_text, "og:title")
    if og_title:
        return og_title
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_meta_description(html_text: str) -> str:
    return extract_meta_name(html_text, "description") or extract_meta_property(html_text, "og:description")


def extract_publisher(html_text: str) -> str:
    return (
        extract_meta_property(html_text, "og:site_name")
        or extract_meta_name(html_text, "author")
        or extract_json_ld_value(html_text, "publisher")
    )


def extract_published_date(html_text: str) -> str:
    return (
        extract_meta_property(html_text, "article:published_time")
        or extract_meta_name(html_text, "date")
        or extract_meta_name(html_text, "pubdate")
        or extract_json_ld_value(html_text, "datePublished")
    )


def extract_canonical_url(html_text: str) -> str:
    match = re.search(
        r"<link\b(?=[^>]*\brel=[\"']canonical[\"'])(?=[^>]*\bhref=[\"']([^\"']*)[\"'])[^>]*>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return clean_html_text(match.group(1)) if match else ""


def extract_meta_name(html_text: str, name: str) -> str:
    pattern = rf"<meta\b(?=[^>]*\bname=[\"']{re.escape(name)}[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>"
    match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_meta_property(html_text: str, property_name: str) -> str:
    pattern = rf"<meta\b(?=[^>]*\bproperty=[\"']{re.escape(property_name)}[\"'])(?=[^>]*\bcontent=[\"']([^\"']*)[\"'])[^>]*>"
    match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
    return clean_html_text(match.group(1)) if match else ""


def extract_json_ld_value(html_text: str, key: str) -> str:
    for match in re.finditer(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        text = clean_html_text(match.group(1))
        value_match = re.search(rf'"{re.escape(key)}"\s*:\s*("[^"]*"|\{{.*?\}})', text)
        if not value_match:
            continue
        raw_value = value_match.group(1)
        if raw_value.startswith('"'):
            return clean_html_text(raw_value.strip('"'))
        name_match = re.search(r'"name"\s*:\s*"([^"]*)"', raw_value)
        if name_match:
            return clean_html_text(name_match.group(1))
    return ""


def extract_text_excerpt(html_text: str, max_chars: int) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return clean_html_text(without_tags)[:max_chars].strip()


def clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def estimate_reliability(publisher: str, canonical_url: str) -> str:
    host = urlparse(canonical_url).netloc.lower()
    publisher_lower = publisher.lower()
    if host.endswith(".gov") or host.endswith(".go.jp") or host.endswith(".edu"):
        return "high"
    if any(token in publisher_lower for token in ["official", "investor relations", "press release"]):
        return "high"
    if publisher or host:
        return "medium"
    return "unknown"


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
        enriched["fetched_publisher"] = metadata.publisher
        enriched["fetched_date"] = metadata.published_date
        enriched["canonical_url"] = metadata.canonical_url
        enriched["fetched_reliability"] = metadata.reliability
        if not enriched.get("title") and metadata.title:
            enriched["title"] = metadata.title
        if not enriched.get("publisher") and metadata.publisher:
            enriched["publisher"] = metadata.publisher
        if not enriched.get("date") and metadata.published_date:
            enriched["date"] = metadata.published_date
        if (not enriched.get("reliability") or enriched.get("reliability") == "unknown") and metadata.reliability:
            enriched["reliability"] = metadata.reliability
        if not enriched.get("summary"):
            enriched["summary"] = metadata.description or metadata.text_excerpt
        enriched_sources.append(enriched)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"sources": enriched_sources}, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
