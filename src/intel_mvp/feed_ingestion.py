from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class FeedConfig:
    url: str
    publisher: str
    type: str
    primary_source: bool
    reliability: str


def load_feed_configs(theme: dict[str, Any]) -> list[FeedConfig]:
    configs: list[FeedConfig] = []
    for item in theme.get("source_feeds", []):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        configs.append(
            FeedConfig(
                url=url,
                publisher=str(item.get("publisher", "")).strip() or publisher_from_url(url),
                type=str(item.get("type", "feed_item")).strip() or "feed_item",
                primary_source=bool(item.get("primary_source", False)),
                reliability=str(item.get("reliability", "medium")).strip() or "medium",
            )
        )
    return configs


def collect_sources_from_feeds(feed_configs: list[FeedConfig], limit: int = 5, timeout_seconds: int = 15) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    feed_item_groups: list[list[dict[str, Any]]] = []
    for feed_config in feed_configs:
        try:
            feed_item_groups.append(parse_feed(fetch_feed_text(feed_config.url, timeout_seconds=timeout_seconds), feed_config))
        except Exception:
            continue
    max_items = max((len(items) for items in feed_item_groups), default=0)
    for index in range(max_items):
        for feed_items in feed_item_groups:
            if index >= len(feed_items):
                continue
            item = feed_items[index]
            url = str(item.get("url", ""))
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            sources.append(item)
            if len(sources) >= limit:
                return sources
    return sources


def fetch_feed_text(url: str, timeout_seconds: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "AI-Intelligence-Unit-MVP/0.1"})
    with urlopen(request, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read(1_000_000).decode(charset, errors="replace")


def parse_feed(feed_text: str, feed_config: FeedConfig) -> list[dict[str, Any]]:
    root = ET.fromstring(feed_text)
    if strip_namespace(root.tag) == "rss":
        return parse_rss(root, feed_config)
    if strip_namespace(root.tag) == "feed":
        return parse_atom(root, feed_config)
    return []


def parse_rss(root: ET.Element, feed_config: FeedConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = child_text(item, "title")
        url = child_text(item, "link") or child_text(item, "guid")
        published = child_text(item, "pubDate") or child_text(item, "date")
        summary = child_text(item, "description")
        if title and url:
            items.append(render_source(title, url, published, summary, feed_config))
    return items


def parse_atom(root: ET.Element, feed_config: FeedConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in children_by_name(root, "entry"):
        title = child_text(entry, "title")
        url = atom_entry_link(entry)
        published = child_text(entry, "updated") or child_text(entry, "published")
        summary = child_text(entry, "summary") or child_text(entry, "content")
        if title and url:
            items.append(render_source(title, url, published, summary, feed_config))
    return items


def render_source(title: str, url: str, published: str, summary: str, feed_config: FeedConfig) -> dict[str, Any]:
    cleaned_title = clean_text(title)
    cleaned_summary = clean_summary(summary, feed_config.publisher)
    return {
        "title": cleaned_title,
        "url": clean_text(url),
        "type": feed_config.type,
        "date": normalize_date(published),
        "publisher": feed_config.publisher,
        "primary_source": feed_config.primary_source,
        "reliability": feed_config.reliability,
        "summary": cleaned_summary or cleaned_title,
    }


def write_feed_sources(sources: list[dict[str, Any]], output_path: Path, theme_id: str | None = None) -> Path:
    if not sources:
        raise ValueError("No sources were collected from the configured feeds.")
    payload: dict[str, Any] = {"sources": sources}
    if theme_id:
        payload["theme_id"] = theme_id
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if strip_namespace(child.tag) == name:
            return "".join(child.itertext()).strip()
    return ""


def children_by_name(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if strip_namespace(child.tag) == name]


def atom_entry_link(entry: ET.Element) -> str:
    fallback = ""
    for child in entry:
        if strip_namespace(child.tag) != "link":
            continue
        href = child.attrib.get("href", "").strip()
        rel = child.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href
        if href and not fallback:
            fallback = href
    return fallback


def strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def clean_summary(value: str, publisher: str) -> str:
    text = clean_text(value)
    text = re.sub(r"\bThe post .+? appeared first on .+?\.?$", "", text).strip()
    if "National Hurricane Center" in publisher:
        match = re.search(r"(Tropical cyclone formation.+?next \d+ days\.)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        text = re.sub(r"^\d{3}\s+[A-Z0-9]+\s+[A-Z]+\s+\d{6}\s+[A-Z0-9]+\s+", "", text).strip()
        text = re.sub(r"\$\$.*$", "", text).strip()
    return text


def normalize_date(value: str) -> str:
    text = clean_text(value)
    if not text:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    iso_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if iso_match:
        return iso_match.group(0)
    return text[:10]


def publisher_from_url(url: str) -> str:
    return urlparse(url).netloc
