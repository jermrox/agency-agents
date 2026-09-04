"""CATS (catsone.com) career portals.

CATS renders a portal as plain HTML with no JSON endpoint and no schema.org
markup: the list page is a table of links, and a job page carries the title
in its header, the station in its first tag, and the description after a
horizontal rule. There is no posting date anywhere on the portal, so these
postings carry none and are never aged out as stale on that basis.

Reef Systems (Air Force HPO, AFSPECWAR and OHWS human performance contracts)
is the portal this was written against.

Options: ``subdomain`` (required), ``portal`` (required, the numeric portal
id in the URL), ``employer``, ``detail_limit`` (default 60),
``delay_seconds`` (default 0).
"""

from __future__ import annotations

import html
import logging
import re
import time
from typing import Any, Iterable

from ..http import fetch
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, place_from_title

log = logging.getLogger(__name__)

_ROW_SPLIT_RE = re.compile(r'class="table-row"')
_LOCATION_CELL_RE = re.compile(r'data-label="Location"[^>]*>(.*?)</', re.S)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
_TAGS_RE = re.compile(r'<ul class="job-tags">(.*?)</ul>', re.S)
_TAG_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.S)
_BODY_RE = re.compile(r'class="job-description-container".*?<hr\s*/?>(.*?)</main>', re.S)


def _clean(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _link_re(portal: str) -> re.Pattern[str]:
    return re.compile(
        r'href="(?P<path>/careers/' + re.escape(portal) + r'(?:-[^/"]*)?/jobs/(?P<id>\d+)[^"?#]*)"[^>]*>(?P<text>.*?)</a>',
        re.S,
    )


def _list_jobs(page: str, portal: str) -> list[dict[str, str]]:
    """Every job on the list page: id, path, title, and the row's location."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    link_re = _link_re(portal)
    for chunk in _ROW_SPLIT_RE.split(page)[1:]:
        link = link_re.search(chunk)
        if not link or link.group("id") in seen:
            continue
        seen.add(link.group("id"))
        cell = _LOCATION_CELL_RE.search(chunk)
        out.append(
            {
                "id": link.group("id"),
                "path": html.unescape(link.group("path")),
                "title": _clean(link.group("text")),
                "location": _clean(cell.group(1)) if cell else "",
            }
        )
    return out


def _parse_detail(page: str) -> dict[str, Any]:
    title = _H1_RE.search(page)
    tags_block = _TAGS_RE.search(page)
    tags = [_clean(t) for t in _TAG_RE.findall(tags_block.group(1))] if tags_block else []
    body = _BODY_RE.search(page)
    return {
        "title": _clean(title.group(1)) if title else "",
        "tags": [t for t in tags if t],
        "description": html_to_text(body.group(1)) if body else "",
    }


class CATSOneSource(Source):
    kind = "catsone"

    def fetch(self) -> Iterable[JobPosting]:
        subdomain = str(self.require("subdomain")).strip().strip("/")
        portal = str(self.require("portal")).strip()
        employer = self.options.get("employer") or subdomain
        detail_limit = int(self.options.get("detail_limit", 60) or 0)
        delay = float(self.options.get("delay_seconds", 0) or 0)
        base = f"https://{subdomain}.catsone.com"

        page = fetch(f"{base}/careers/{portal}").decode("utf-8", "replace")
        jobs = _list_jobs(page, portal)
        log.info("%s: %d job(s) on the portal list", self.name, len(jobs))

        for index, job in enumerate(jobs):
            url = base + job["path"]
            detail: dict[str, Any] = {}
            if index < detail_limit:
                try:
                    if delay and index:
                        time.sleep(delay)
                    detail = _parse_detail(fetch(url).decode("utf-8", "replace"))
                except Exception as exc:
                    log.warning("%s: detail fetch failed for %s: %s", self.name, url, exc)
            title = detail.get("title") or job["title"]
            tags = detail.get("tags") or []
            # Reef writes a clean "Station, ST" at the end of each title, while
            # its tags are uneven ("Moody, AFB", "Davis_Monthan, Arizona"), so
            # the title's place wins; the first tag and the list cell follow.
            location = place_from_title(title) or (tags[0] if tags else "") or job["location"]
            description = detail.get("description") or title
            if len(tags) > 1:
                description = f"{description}\nCategory: {tags[1]}."
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=job["id"],
                url=url,
                title=title,
                employer=employer,
                location=location,
                description=description,
                posted_at=None,
                remote=looks_remote(location, title),
                raw={"listing": job, "tags": tags},
            )


CATS_SOURCES: tuple[type[Source], ...] = (CATSOneSource,)
