"""The run loop: fetch -> classify -> dedupe -> publish."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .classify import Verdict, classify
from .config import Config
from .models import JobPosting, SourceError
from .publishers import build_publisher
from .sources import build_source
from .store import Store

log = logging.getLogger(__name__)


@dataclass(slots=True)
class RunReport:
    fetched: int = 0
    rejected: int = 0
    stale: int = 0
    duplicates: int = 0
    approved: list[JobPosting] = field(default_factory=list)
    review: list[JobPosting] = field(default_factory=list)
    errors: list[SourceError] = field(default_factory=list)
    published: list[str] = field(default_factory=list)
    pruned: int = 0

    def summary(self) -> str:
        lines = [
            f"fetched     {self.fetched}",
            f"rejected    {self.rejected} (off-topic)",
            f"stale       {self.stale} (older than max_age_days)",
            f"duplicates  {self.duplicates} (already seen)",
            f"approved    {len(self.approved)}",
            f"review      {len(self.review)}",
        ]
        if self.pruned:
            lines.append(f"pruned      {self.pruned} state record(s)")
        for entry in self.published:
            lines.append(f"published   {entry}")
        for error in self.errors:
            lines.append(f"ERROR       {error}")
        return "\n".join(lines)


def collect(config: Config, report: RunReport) -> list[JobPosting]:
    """Fetch from every configured source, tolerating individual failures."""
    postings: list[JobPosting] = []
    for source_config in config.sources:
        try:
            source = build_source(
                source_config.kind, source_config.name, source_config.options
            )
        except KeyError as exc:
            report.errors.append(SourceError(source_config.name, str(exc)))
            continue
        try:
            found = list(source.fetch())
            log.info("%s: fetched %d posting(s)", source_config.name, len(found))
            postings.extend(found)
        except Exception as exc:
            # One broken source must never abort the whole run.
            log.warning("%s failed: %s", source_config.name, exc)
            report.errors.append(SourceError(source_config.name, str(exc)))
    report.fetched = len(postings)
    return postings


def _is_stale(posting: JobPosting, max_age_days: int) -> bool:
    if max_age_days <= 0 or posting.posted_at is None:
        return False
    stamp = posting.posted_at
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp < datetime.now(timezone.utc) - timedelta(days=max_age_days)


def run(config: Config, *, dry_run: bool = False) -> RunReport:
    """Execute one full pass and return what happened."""
    report = RunReport()
    store = Store.load(config.state_path)

    postings = collect(config, report)

    verdicts: dict[str, str] = {}
    scored: list[JobPosting] = []
    for posting in postings:
        if not posting.url or not posting.title:
            report.rejected += 1
            continue
        if _is_stale(posting, config.max_age_days):
            report.stale += 1
            continue
        verdict = classify(posting, config.thresholds)
        if verdict == Verdict.REJECT:
            report.rejected += 1
            continue
        verdicts[posting.identity] = verdict
        scored.append(posting)

    before = len(scored)
    fresh = store.filter_new(scored)
    report.duplicates = before - len(fresh)

    # Auto-publish is opt-in. With it off, even a high scorer goes to review --
    # a public brand site is not the place to discover a classifier regression.
    for posting in fresh:
        if config.auto_publish and verdicts[posting.identity] == Verdict.PUBLISH:
            report.approved.append(posting)
        else:
            report.review.append(posting)

    if dry_run:
        log.info("dry run: skipping publishers and state write")
        return report

    _publish(config, report)

    for posting in report.approved:
        store.mark(posting, "published")
    for posting in report.review:
        store.mark(posting, "review")
    report.pruned = store.prune(config.max_age_days * 3)
    store.save()
    return report


def _publish(config: Config, report: RunReport) -> None:
    """Fan out to configured publishers.

    Review-queue publishers get everything that needs eyes; every other
    publisher gets only approved postings. A publisher that raises is logged
    and skipped so one bad webhook cannot lose the rest of the run.
    """
    for publisher_config in config.publishers:
        try:
            publisher = build_publisher(publisher_config.kind, publisher_config.options)
        except KeyError as exc:
            report.errors.append(SourceError(publisher_config.kind, str(exc)))
            continue

        batch = report.review if publisher_config.kind == "review" else report.approved

        try:
            report.published.append(publisher.publish(batch))
        except Exception as exc:
            log.warning("publisher %s failed: %s", publisher_config.kind, exc)
            report.errors.append(SourceError(publisher_config.kind, str(exc)))
        finally:
            publisher.close()
