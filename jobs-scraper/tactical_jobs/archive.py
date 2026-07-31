"""Full-fidelity corpus of every posting this scraper has ever seen.

The published board is deliberately lossy: it carries only jobs that are
currently open, at excerpt length, scored against today's thresholds. That is
the right shape for a reader and the wrong shape for analysis. Questions worth
answering -- how often does a THOR3 contract re-post, is TS/SCI showing up in
more Fort Liberty listings this year than last, what do CSCS-plus-TSAC-F roles
actually pay -- all need text that a live board throws away, from postings that
were taken down months ago.

So the archive keeps **everything, forever, at full length**. It is the only
place in the system that never deletes and never truncates. ``store.py`` is the
opposite: a small, prunable index of what has been *seen*, sized to be committed
to git. The two are not redundant; the store answers "publish this?" in memory
and the archive answers "what did this job say in March?" off disk.

Why JSONL rather than one JSON array
------------------------------------
A run appends O(new records) instead of rewriting the whole corpus, which
matters once the file is hundreds of megabytes of description text. It also
degrades well: a process killed mid-write costs the one line it was writing,
not the entire archive, because there is no enclosing bracket to leave
unbalanced. Every reader here treats an unparseable line as a skippable hole
rather than a fatal error. There is no schema header for the same reason --
a header is a single point of failure, and each line is self-describing.

The revision rule
-----------------
``append`` is idempotent per *content*, not per identity:

* Same job identity, byte-identical content -> **no line written.** Nightly runs
  re-fetch the same open postings for weeks; recording that would bury the
  corpus in noise.
* Same job identity, changed content -> **a new line is written.** An employer
  who rewrites a description, adds a salary band, or quietly drops the clearance
  requirement is a signal worth having, and the only way to see it is to keep
  both versions. The corpus is a history, not a snapshot.

The comparison is against the identity's *most recent* archived content, not
against every version ever seen. A posting that changes A -> B -> A therefore
records three lines. That is intentional: collapsing the revert would leave the
history claiming the job still reads B, which is false.

For that rule to hold across process restarts, the hash a writer computes from
a live ``JobPosting`` has to equal the hash a later run computes from the line
it wrote. Everything here is therefore hashed in its *on-disk* form -- see
:func:`_normalize` -- because the trip through JSON is lossy in ways that are
easy to miss and expensive to get wrong: an unchanged posting that hashes
differently after a reload gets re-archived on every run, forever.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from .models import JobPosting

ARCHIVED_AT = "archived_at"
"""Record key holding the UTC ISO timestamp of when the line was written.

Excluded from the content hash on purpose -- it changes every run, so including
it would make every posting look edited and defeat the idempotency rule.
"""

TOP_EMPLOYERS = 10
"""How many employers :meth:`Archive.stats` names before it stops counting."""

# Sorts before any real timestamp, so a record with a missing or unparseable
# archived_at loses to a dated one instead of poisoning the comparison.
_UNDATED = datetime(1, 1, 1, tzinfo=timezone.utc)


def _json_text(payload: Any, *, sort_keys: bool = False) -> str:
    """Serialize ``payload`` exactly the way a line of this file is written.

    Three deliberate safety valves, all there because ``enrichment`` is a
    free-form dict owned by another module and one odd value in it must not
    take down a nightly run:

    * ``default=str`` stringifies a value type JSON has no room for (a
      ``datetime``, say) instead of raising.
    * ``skipkeys=True`` drops a key type JSON has no room for -- a tuple key --
      instead of raising. Losing one exotic key beats losing the whole run,
      and because the same call produces both the hash and the line, the writer
      and every later reader agree on what is missing.
    * The re-encode through ``errors="replace"`` scrubs lone surrogates.
      ``json.dumps`` will happily emit a raw ``\\ud800`` that scraped HTML
      smuggled in, and writing that to a UTF-8 file raises
      ``UnicodeEncodeError`` -- so the substitution has to happen here, on the
      text that gets both hashed and written, rather than at the file handle
      where only the write would be protected and the two would disagree.
    """
    text = json.dumps(payload, ensure_ascii=False, sort_keys=sort_keys, default=str, skipkeys=True)
    return text.encode("utf-8", "replace").decode("utf-8")


def _normalize(record: Mapping[str, Any]) -> dict[str, Any]:
    """Round-trip a record through JSON so it matches what a reader will see.

    Whatever ``enrichment`` was carrying in memory -- datetimes, tuples,
    integer dict keys -- comes back as the plain strings, lists and
    string-keyed dicts that JSON has room for. Hashing the normalized form is
    what makes idempotency survive a restart, and the failure it prevents is
    silent: an enrichment dict keyed by integers sorts numerically in memory
    (``9`` before ``10``) and lexically once reloaded (``"10"`` before ``"9"``),
    so an unchanged posting would hash differently on every run and the corpus
    would grow a bogus revision nightly.

    It also makes :func:`_content_hash` safe to sort: after the round trip every
    key is a string, so ``sort_keys`` can no longer trip over a dict that mixed
    integer and string keys.
    """
    return json.loads(_json_text(record))


def _content_hash(record: Mapping[str, Any]) -> str:
    """Fingerprint a JSON-native record's *content*, ignoring when it was archived.

    Callers must pass a record that has already been through JSON -- either
    parsed from a line of the file or run through :func:`_normalize` -- or the
    hash will not match the one a later run computes for the same posting.
    """
    payload = {key: value for key, value in record.items() if key != ARCHIVED_AT}
    return hashlib.sha256(_json_text(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _archived_at(record: Mapping[str, Any]) -> datetime:
    """Parse ``archived_at`` into a UTC datetime, tolerating anything."""
    raw = record.get(ARCHIVED_AT)
    if not isinstance(raw, str):
        return _UNDATED
    try:
        stamp = datetime.fromisoformat(raw)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        # OverflowError, not ValueError, is what a near-``datetime.min`` stamp
        # with an eastern offset raises when it is shifted back to UTC. A single
        # weird line in the corpus must not take down the read.
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return _UNDATED


def _span(values: list[str]) -> tuple[str | None, str | None]:
    """Earliest and latest of a list of ISO strings, or ``(None, None)``.

    Lexical order is chronological order here because every timestamp this
    module writes is UTC-normalized to a fixed-width ``+00:00`` form, by
    ``JobPosting.posted_at_iso`` for postings and by :meth:`Archive.append` for
    archive stamps.
    """
    if not values:
        return None, None
    ordered = sorted(values)
    return ordered[0], ordered[-1]


@dataclass(slots=True)
class Archive:
    """Append-only JSONL corpus at ``path``."""

    path: Path

    _latest_hash: dict[str, str] = field(default_factory=dict, repr=False)
    """identity -> content hash of that job's most recently archived line.

    Only the hashes are held in memory, never the records. The whole point of
    this file is that it grows without bound, so loading it into RAM to decide
    what to append would put a ceiling on the corpus. Callers that genuinely
    need the text re-read it through :meth:`records`.
    """

    @classmethod
    def load(cls, path: str | Path) -> "Archive":
        """Open the archive at ``path``, building the dedupe index.

        A missing file is not an error -- it is simply an empty corpus, which is
        exactly what the first run of a fresh checkout sees.
        """
        path = Path(path)
        archive = cls(path=path)
        # Streamed, not ``records()``: materializing the corpus here to build a
        # dict of 20-byte hashes would put the whole point of the file -- that
        # it grows without bound -- at the mercy of available RAM.
        for record in archive._iter_records():
            identity = record.get("id")
            if isinstance(identity, str) and identity:
                # File order is archive order, so the last line for an identity
                # wins and _latest_hash ends up holding the current content.
                archive._latest_hash[identity] = _content_hash(record)
        return archive

    def append(self, postings: Sequence[JobPosting]) -> int:
        """Archive ``postings``, skipping unchanged ones. Returns lines written.

        See the module docstring for the revision rule. Deduping happens against
        the in-memory index as it is updated, so a batch containing the same
        posting twice writes it once.
        """
        stamp = datetime.now(timezone.utc).isoformat()
        lines: list[str] = []
        pending: dict[str, str] = {}
        for posting in postings:
            # Normalized first so the hash is taken on the bytes that will
            # actually land in the file, not on the richer in-memory shape.
            record = _normalize(posting.to_archive_dict())
            digest = _content_hash(record)
            identity = posting.identity
            if pending.get(identity, self._latest_hash.get(identity)) == digest:
                continue
            record[ARCHIVED_AT] = stamp
            lines.append(_json_text(record))
            pending[identity] = digest

        if not lines:
            return 0

        self.path.parent.mkdir(parents=True, exist_ok=True)
        # A previous process killed mid-write can leave a line with no trailing
        # newline. Appending straight onto it would glue our first record to the
        # tail of the broken one and corrupt a good record along with the bad
        # one, so close the wound off first. The truncated line stays garbage
        # and gets skipped on read; that is the cost of one interrupted run.
        prefix = "\n" if self._dangling_line() else ""
        with self.path.open("a", encoding="utf-8") as handle:
            # One write of complete, newline-terminated lines: a reader either
            # sees a whole record or does not see it at all.
            handle.write(prefix + "".join(f"{line}\n" for line in lines))
            handle.flush()
            os.fsync(handle.fileno())

        self._latest_hash.update(pending)
        return len(lines)

    def records(self) -> list[dict[str, Any]]:
        """Every archived record, oldest line first.

        Never raises. A missing file yields ``[]``, and a line that does not
        parse as a JSON object is dropped rather than aborting the read -- one
        interrupted run must not make the corpus permanently unreadable.

        This is the one method that deliberately holds the whole corpus in
        memory, because that is what its signature promises. Anything inside
        this module that only needs to sweep the file uses
        :meth:`_iter_records` instead.
        """
        return list(self._iter_records())

    def _iter_records(self) -> Iterator[dict[str, Any]]:
        """Stream archived records off disk, oldest line first.

        Never raises, for the same reasons :meth:`records` does not. Keeping
        this lazy is what lets :meth:`load` and :meth:`stats` sweep a corpus
        larger than RAM.
        """
        try:
            # errors="replace" so a half-written multi-byte character at the
            # truncation point degrades into a line that fails to parse (and is
            # skipped below) instead of raising out of the whole read.
            with self.path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except ValueError:
                        # The broad base class rather than JSONDecodeError (a
                        # subclass of it) on purpose: the guarantee this method
                        # makes is that no line can abort the read, and that is
                        # worth more than naming one exception type precisely.
                        continue
                    if isinstance(record, dict):
                        yield record
        except OSError:
            return

    def latest_by_identity(self) -> dict[str, dict[str, Any]]:
        """The current version of every job the archive has ever held.

        Keyed by ``id`` (the posting's identity). Where an identity has several
        revisions, the one with the newest ``archived_at`` wins; ties go to the
        later line, since append order is the tiebreaker the file itself
        records. This is the entry point for "what does the corpus know about
        every job", as opposed to :meth:`records` which is the edit history.
        """
        latest: dict[str, dict[str, Any]] = {}
        newest: dict[str, datetime] = {}
        # Streamed: the result holds one record per job, not one per revision,
        # so there is no reason to have the whole edit history resident too.
        for record in self._iter_records():
            identity = record.get("id")
            if not isinstance(identity, str) or not identity:
                continue
            when = _archived_at(record)
            if identity in newest and when < newest[identity]:
                continue
            latest[identity] = record
            newest[identity] = when
        return latest

    def stats(self) -> dict[str, Any]:
        """Corpus summary: counts, date spans, employers, size on disk.

        Cheap enough to print in a run report and JSON-serializable throughout,
        so the same shape can be dropped into a status page. Streams the file
        rather than materializing it: this is the method most likely to be
        called on a corpus nobody has pruned in two years.
        """
        total = 0
        identified = 0
        identities: set[str] = set()
        sources: set[str] = set()
        employer_counts: dict[str, int] = {}
        archived: list[str] = []
        posted: list[str] = []
        description_chars = 0

        for record in self._iter_records():
            total += 1
            identity = record.get("id")
            if isinstance(identity, str) and identity:
                identities.add(identity)
                identified += 1
            source = record.get("source")
            if isinstance(source, str) and source:
                sources.add(source)
            employer = record.get("employer")
            if isinstance(employer, str) and employer:
                employer_counts[employer] = employer_counts.get(employer, 0) + 1
            stamp = record.get(ARCHIVED_AT)
            if isinstance(stamp, str) and stamp:
                archived.append(stamp)
            stamp = record.get("posted_at")
            if isinstance(stamp, str) and stamp:
                posted.append(stamp)
            chars = record.get("description_chars")
            # ``bool`` is an ``int`` in Python, and a hand-edited or
            # half-corrupt line carrying ``true`` here would otherwise add 1.
            if isinstance(chars, int) and not isinstance(chars, bool) and chars > 0:
                description_chars += chars

        first_archived, last_archived = _span(archived)
        first_posted, last_posted = _span(posted)

        try:
            size = self.path.stat().st_size
        except OSError:
            size = 0

        # Sort by count descending, then name, so the list is stable across runs
        # and does not churn a committed status file over tied employers.
        top = sorted(employer_counts.items(), key=lambda item: (-item[1], item[0]))

        return {
            "path": str(self.path),
            "exists": self.path.exists(),
            "bytes": size,
            "records": total,
            "identities": len(identities),
            # Every line beyond the first for an identity is an observed edit.
            # A high number here means employers are actively revising, which is
            # itself the signal the archive exists to capture. Counted off the
            # lines that actually carry an id, so a stray id-less record cannot
            # inflate the edit count with a revision that never happened.
            "revisions": identified - len(identities),
            "sources": len(sources),
            "employers": len(employer_counts),
            "top_employers": [
                {"employer": name, "records": count} for name, count in top[:TOP_EMPLOYERS]
            ],
            "description_chars": description_chars,
            "first_archived_at": first_archived,
            "last_archived_at": last_archived,
            "first_posted_at": first_posted,
            "last_posted_at": last_posted,
        }

    def _dangling_line(self) -> bool:
        """True if the file ends mid-line (no trailing newline)."""
        try:
            size = self.path.stat().st_size
        except OSError:
            return False
        if size == 0:
            return False
        try:
            with self.path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                return handle.read(1) != b"\n"
        except OSError:
            return False
