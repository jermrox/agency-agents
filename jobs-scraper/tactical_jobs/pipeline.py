"""The run loop: fetch -> classify -> dedupe -> publish."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .archive import Archive
from .classify import Verdict, classify
from .config import Config
from .enrich import enrich
from .facets import facets_for
from .feed import normalize_file
from .insights import build_insights
from .liveness import check_all
from .models import JobPosting, SourceError
from .publishers import build_publisher
from .publishers.files import load_board
from .report import render_html, render_markdown
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
    refreshed: list[JobPosting] = field(default_factory=list)
    errors: list[SourceError] = field(default_factory=list)
    published: list[str] = field(default_factory=list)
    pruned: int = 0
    archived: int = 0
    retired: int = 0
    unverifiable: int = 0
    insights: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"fetched     {self.fetched}",
            f"rejected    {self.rejected} (off-topic)",
            f"stale       {self.stale} (older than max_age_days)",
            f"duplicates  {self.duplicates} (already seen)",
            f"approved    {len(self.approved)}",
            f"review      {len(self.review)}",
        ]
        if self.retired or self.unverifiable:
            lines.append(
                f"retired     {self.retired} dead listing(s) "
                f"({self.unverifiable} unverifiable, kept)"
            )
        if self.archived:
            lines.append(f"archived    {self.archived} new corpus record(s)")
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

        # Enrich everything that survives classification, including postings
        # that turn out to be duplicates. The archive is a corpus, and a
        # re-post whose salary or clearance changed is signal worth keeping.
        try:
            enrich(posting)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("enrichment failed for %s: %s", posting.url, exc)

        try:
            posting.facets = facets_for(posting)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("facets failed for %s: %s", posting.url, exc)

        verdicts[posting.identity] = verdict
        scored.append(posting)

    before = len(scored)
    fresh = store.filter_new(scored)
    report.duplicates = before - len(fresh)

    # A posting already on the board is re-fetched and re-derived on every run,
    # then dropped here as a duplicate -- so the board kept whatever it was
    # first published with, forever. That made every classifier or extraction
    # fix apply only to jobs the board had never seen: three KBR SOF postings
    # stayed flagged Remote after the fix that corrected them, because they
    # were already listed. Carry the re-derived version through so the entry
    # reflects the posting as it is now, not as it was first read.
    fresh_ids = {p.identity for p in fresh}
    report.refreshed = [
        p
        for p in scored
        if p.identity not in fresh_ids and verdicts[p.identity] == Verdict.PUBLISH
    ]

    # Auto-publish is opt-in. With it off, even a high scorer goes to review --
    # a public brand site is not the place to discover a classifier regression.
    for posting in fresh:
        if config.auto_publish and verdicts[posting.identity] == Verdict.PUBLISH:
            report.approved.append(posting)
        else:
            report.review.append(posting)

    if dry_run:
        log.info("dry run: skipping archive, publishers, and state write")
        return report

    # Archive BEFORE publishing. The corpus is the durable asset -- a publisher
    # failing should never cost us the record of what we saw.
    _archive(config, report, scored)

    _retire_dead(config, report)
    _publish(config, report)
    _finalize_feeds(config, report)

    for posting in report.approved:
        store.mark(posting, "published")
    for posting in report.review:
        store.mark(posting, "review")
    report.pruned = store.prune(config.max_age_days * 3)
    store.save()

    _analyze(config, report)
    return report


def _archive(config: Config, report: RunReport, scored: list[JobPosting]) -> None:
    """Append every relevant posting to the full-fidelity corpus."""
    if not config.archive_path:
        return
    try:
        archive = Archive.load(config.archive_path)
        report.archived = archive.append(scored)
    except Exception as exc:
        log.warning("archive append failed: %s", exc)
        report.errors.append(SourceError("archive", str(exc)))


def _feed_paths(config: Config) -> list[Path]:
    """Every jsonfeed file this config writes."""
    return [
        Path(p.options.get("path", "output/jobs.json"))
        for p in config.publishers
        if p.kind == "jsonfeed"
    ]


def _retire_dead(config: Config, report: RunReport) -> None:
    """Walk the published board and drop postings that no longer exist."""
    if not config.liveness_check:
        return
    for path in _feed_paths(config):
        board = load_board(path)
        if not board:
            continue
        try:
            verdicts = check_all(
                (job.get("url", "") for job in board),
                workers=config.liveness_workers,
                timeout=config.liveness_timeout,
            )
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("liveness sweep failed for %s: %s", path, exc)
            report.errors.append(SourceError("liveness", str(exc)))
            continue

        kept: list[dict] = []
        for job in board:
            verdict = verdicts.get(job.get("url", ""))
            if verdict is None:
                kept.append(job)
                continue
            if verdict.is_gone:
                report.retired += 1
                log.info("retiring %s (%s)", job.get("url"), verdict.reason)
                continue
            if verdict.state != "live":
                report.unverifiable += 1
            job["liveness"] = verdict.as_dict()
            kept.append(job)

        if verdicts:
            try:
                payload = json.loads(path.read_text())
                payload["jobs"] = kept
                payload["count"] = len(kept)
                path.write_text(json.dumps(payload, indent=2) + "\n")
            except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
                log.warning("could not rewrite %s after liveness sweep: %s", path, exc)


def _finalize_feeds(config: Config, report: RunReport) -> None:
    """Normalize every published feed so the board has what it renders."""
    for path in _feed_paths(config):
        if not path.exists():
            continue
        try:
            normalize_file(path, path)
        except Exception as exc:
            log.warning("feed normalize failed for %s: %s", path, exc)
            report.errors.append(SourceError("feed", str(exc)))


def _analyze(config: Config, report: RunReport) -> None:
    """Rebuild the insights digest and dashboard from the whole corpus.

    Runs over the archive rather than this run's postings, because a report
    built from one night's fetch would say almost nothing -- the interesting
    questions (who is hiring, what do they pay, which credentials) are only
    answerable across the accumulated corpus.
    """
    if not config.archive_path or not config.insights_dir:
        return
    try:
        records = Archive.load(config.archive_path).records()
        if not records:
            return
        insights = build_insights(records)
        output = Path(config.insights_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "insights.json").write_text(json.dumps(insights, indent=2) + "\n")
        (output / "digest.md").write_text(render_markdown(insights))
        (output / "dashboard.html").write_text(
            render_html(insights, title=config.insights_title)
        )
        report.insights = insights
        report.published.append(f"insights: {len(records)} records -> {output}")
    except Exception as exc:
        log.warning("insights build failed: %s", exc)
        report.errors.append(SourceError("insights", str(exc)))


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

        # Only the board takes refreshed entries. RSS and webhooks announce, and
        # re-announcing a job because its location string was corrected would
        # be a lie to every subscriber.
        if publisher_config.kind == "review":
            batch = report.review
        elif publisher_config.kind == "jsonfeed":
            batch = report.approved + report.refreshed
        else:
            batch = report.approved

        try:
            report.published.append(publisher.publish(batch))
        except Exception as exc:
            log.warning("publisher %s failed: %s", publisher_config.kind, exc)
            report.errors.append(SourceError(publisher_config.kind, str(exc)))
        finally:
            publisher.close()
