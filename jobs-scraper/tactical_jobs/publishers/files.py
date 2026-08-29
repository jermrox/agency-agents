"""File-emitting publishers: JSON Feed, RSS, and the Markdown review queue.

These are the backbone of the Squarespace path. Squarespace has no public
content-write API for pages or blog posts, so nothing can POST a job onto the
site directly. What *does* work reliably is:

1. this publisher writes ``jobs.json`` to a static host (GitHub Pages, a
   Cloudflare/S3 bucket -- anywhere with CORS enabled), and
2. a small code block on the Squarespace page fetches and renders it.

See ``embed/squarespace-jobs.html`` for the drop-in snippet. The upside over
any "post into the CMS" approach is that the board stays live: removing a job
from the feed removes it from the page, with no stale-post cleanup.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Sequence
from xml.sax.saxutils import escape

from ..models import JobPosting
from .base import Publisher

EXCERPT_CHARS = 400


def _as_datetime(value: str | None) -> datetime:
    """Parse an ISO timestamp for RSS, defaulting to now on anything unusable."""
    if value:
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    """Trim to ``limit`` on a word boundary.

    Republishing a full job description is both a copyright risk and bad for
    the employer, who wants the click. Excerpt plus link is the right shape.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    cut = collapsed[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def load_board(path: Path) -> list[dict]:
    """Read the live board from a JSON feed file, tolerating a missing/bad file."""
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text()).get("jobs", [])
    except (json.JSONDecodeError, OSError, AttributeError):
        return []


class JSONFeedPublisher(Publisher):
    """Write the board as JSON, appending to (not replacing) prior runs.

    The file is the complete current board, not a delta -- the embed renders
    whatever is in it.
    """

    kind = "jsonfeed"

    def publish(self, postings: Sequence[JobPosting]) -> str:
        path = Path(self.options.get("path", "output/jobs.json"))
        retain_days = int(self.options.get("retain_days", 45))
        # 0 (or negative) keeps the complete description. The board excerpts by
        # default because a card on the site only needs a teaser and the
        # employer wants the click -- but the full text is always preserved in
        # the archive, and set excerpt_chars = 0 to carry it into the feed too.
        excerpt_chars = int(self.options.get("excerpt_chars", EXCERPT_CHARS))
        path.parent.mkdir(parents=True, exist_ok=True)

        existing = load_board(path)
        merged: dict[str, dict] = {job["id"]: job for job in existing if "id" in job}
        now = datetime.now(timezone.utc)
        added = 0
        for posting in postings:
            entry = posting.to_public_dict()
            if excerpt_chars > 0:
                entry["description"] = _excerpt(entry["description"], excerpt_chars)
            previous = merged.get(entry["id"])
            # Keep the ORIGINAL listing date when refreshing an entry that is
            # already on the board. Stamping it with now would restart the
            # retention clock every run, and a posting would never age out.
            if previous and previous.get("listed_at"):
                entry["listed_at"] = previous["listed_at"]
            else:
                entry["listed_at"] = now.isoformat()
                added += 1
            merged[entry["id"]] = entry

        # Age out old entries so the board does not accumulate dead links.
        cutoff = now.timestamp() - retain_days * 86400
        kept = []
        for job in merged.values():
            try:
                listed = datetime.fromisoformat(job.get("listed_at", "")).timestamp()
            except ValueError:
                listed = now.timestamp()
            if listed >= cutoff:
                kept.append(job)

        kept.sort(key=lambda j: (j.get("listed_at") or "", j.get("score", 0)), reverse=True)
        payload = {
            "version": 1,
            "generated_at": now.isoformat(),
            "count": len(kept),
            "jobs": kept,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")
        refreshed = len(postings) - added
        return (
            f"jsonfeed: +{added} new, {refreshed} refreshed, "
            f"{len(kept)} live -> {path}"
        )


class RSSPublisher(Publisher):
    """Write an RSS 2.0 feed of the live board.

    Squarespace can consume an external RSS feed in a Summary Block, and it
    also gives the audience something to subscribe to.

    An RSS feed has to describe the *whole* current board, not just this run's
    new arrivals -- a run with no new jobs would otherwise blank the feed. So
    this renders ``source_feed`` (the JSON board) when it exists and falls back
    to the passed postings only when it does not. Configure the ``jsonfeed``
    publisher before this one so the board is current when this reads it.
    """

    kind = "rss"

    def publish(self, postings: Sequence[JobPosting]) -> str:
        path = Path(self.options.get("path", "output/jobs.xml"))
        source_feed = Path(self.options.get("source_feed", "output/jobs.json"))
        limit = int(self.options.get("limit", 50))
        title = self.options.get("title", "MOPs & MOEs -- Tactical Human Performance Jobs")
        link = self.options.get("link", "https://www.mopsnmoes.com/jobs")
        description = self.options.get(
            "description",
            "Open roles in tactical strength and conditioning, sports medicine, "
            "performance nutrition, and cognitive performance.",
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        board = load_board(source_feed)
        entries = board or [p.to_public_dict() for p in postings]

        items = []
        for entry in entries[:limit]:
            location = entry.get("location") or "Location not listed"
            body = _excerpt(entry.get("description") or "")
            pub_date = _as_datetime(entry.get("posted_at") or entry.get("listed_at"))
            categories = "".join(
                f"<category>{escape(t)}</category>" for t in entry.get("tags", [])
            )
            items.append(
                "<item>"
                f"<title>{escape(entry.get('title', ''))} — {escape(entry.get('employer', ''))}</title>"
                f"<link>{escape(entry.get('url', ''))}</link>"
                f"<guid isPermaLink=\"false\">{escape(entry.get('id', ''))}</guid>"
                f"<pubDate>{format_datetime(pub_date)}</pubDate>"
                f"<description>{escape(f'{location}. {body}')}</description>"
                f"{categories}"
                "</item>"
            )

        feed = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0"><channel>'
            f"<title>{escape(title)}</title>"
            f"<link>{escape(link)}</link>"
            f"<description>{escape(description)}</description>"
            f"<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>"
            f"{''.join(items)}"
            "</channel></rss>\n"
        )
        path.write_text(feed)
        return f"rss: {len(items)} items -> {path}"


class ReviewQueuePublisher(Publisher):
    """Write borderline postings to a Markdown file for a human to triage.

    This is where anything scoring between ``review`` and ``publish`` lands,
    and -- when ``auto_publish`` is off -- where approved postings land too.
    """

    kind = "review"

    def publish(self, postings: Sequence[JobPosting]) -> str:
        path = Path(self.options.get("path", "output/review-queue.md"))
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = [f"## Run {stamp} — {len(postings)} posting(s)", ""]
        if not postings:
            lines.append("_No new postings._")
        for posting in sorted(postings, key=lambda p: p.score, reverse=True):
            location = posting.location or "location not listed"
            lines.extend(
                [
                    f"### [{posting.title}]({posting.url})",
                    f"- **Employer:** {posting.employer}",
                    f"- **Location:** {location}{' (remote)' if posting.remote else ''}",
                    f"- **Score:** {posting.score:.1f} | **Tags:** {', '.join(posting.tags) or 'none'}",
                    f"- **Source:** `{posting.source}`",
                ]
            )
            if posting.compensation:
                lines.append(f"- **Compensation:** {posting.compensation}")
            lines.extend(
                [
                    f"- **Matched:** domain={', '.join(sorted(set(posting.domain_hits))[:6]) or '-'}"
                    f" | discipline={', '.join(sorted(set(posting.discipline_hits))[:6]) or '-'}",
                    "",
                    f"> {_excerpt(posting.description, 300)}",
                    "",
                    "- [ ] Approve  - [ ] Reject",
                    "",
                ]
            )

        # Prepend so the newest run is at the top of the file.
        previous = path.read_text() if path.exists() else ""
        path.write_text("\n".join(lines) + "\n\n" + previous)
        return f"review: {len(postings)} queued -> {path}"


FILE_PUBLISHERS: tuple[type[Publisher], ...] = (
    JSONFeedPublisher,
    RSSPublisher,
    ReviewQueuePublisher,
)
