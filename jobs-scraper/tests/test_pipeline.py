

def test_a_source_can_opt_out_of_the_age_rule():
    """A BambooHR list is the employer's open requisitions; age is not
    staleness there, so max_age_days = 0 on the source keeps old-but-open
    postings while the global limit still applies to everyone else."""
    from datetime import datetime, timedelta, timezone

    from tactical_jobs.config import Config, SourceConfig
    from tactical_jobs.pipeline import _age_limits, _is_stale

    config = Config.__new__(Config)
    config.sources = [
        SourceConfig(kind="bamboohr", name="lmr", options={"max_age_days": 0}),
        SourceConfig(kind="jsonld", name="serco", options={}),
        SourceConfig(kind="workday", name="kbr", options={"max_age_days": "many"}),
    ]
    limits = _age_limits(config)
    assert limits == {"bamboohr:lmr": 0}

    from tactical_jobs.models import JobPosting

    old = datetime.now(timezone.utc) - timedelta(days=200)
    lmr = JobPosting(source="bamboohr:lmr", source_id="1", url="https://x/1", title="Coach", employer="LMR", location="", description="", posted_at=old)
    serco = JobPosting(source="jsonld:serco", source_id="2", url="https://x/2", title="Coach", employer="Serco", location="", description="", posted_at=old)
    assert not _is_stale(lmr, limits.get(lmr.source, 45))
    assert _is_stale(serco, limits.get(serco.source, 45))


# --- retirement: what a source no longer lists, what the classifier rejects --


def _retire_config(tmp_path, sources, liveness=False):
    from tactical_jobs.config import Config, PublisherConfig

    config = Config.__new__(Config)
    config.sources = sources
    config.publishers = [PublisherConfig(kind="jsonfeed", options={"path": str(tmp_path / "jobs.json")})]
    config.liveness_check = liveness
    config.liveness_workers = 1
    config.liveness_timeout = 1
    config.max_age_days = 45
    return config


def _board(tmp_path, jobs):
    import json

    path = tmp_path / "jobs.json"
    path.write_text(json.dumps({"version": 1, "count": len(jobs), "jobs": jobs}))
    return path


def _row(source, n, title="Coach"):
    return {"id": f"{source}-{n}", "url": f"https://x.invalid/{source}/{n}", "source": source, "title": title}


def _keys(row):
    return {row["id"], row["url"]}


def test_an_open_only_source_retires_what_it_no_longer_lists(tmp_path):
    """USAJOBS, Workday, iCIMS and Oracle list open jobs only and serve closed
    ones with HTTP 200. The source is the authority: twelve closed federal
    announcements sat on the live board as "live" (audit 2026-09-05)."""
    import json

    from tactical_jobs.config import SourceConfig
    from tactical_jobs.pipeline import RunReport, _age_limits, _retire_dead, _retirement_plan

    config = _retire_config(
        tmp_path,
        [
            SourceConfig(kind="usajobs", name="federal", options={"max_age_days": 0}),
            SourceConfig(kind="jsonld", name="nsca", options={}),
        ],
    )
    listed, closed = _row("usajobs:federal", 1), _row("usajobs:federal", 2)
    aged = _row("jsonld:nsca", 3)          # 45-day source: absence says nothing
    manual = _row("usajobs:manual", 4)     # no configured source: left to liveness
    path = _board(tmp_path, [listed, closed, aged, manual])

    report = RunReport()
    returned = {"usajobs:federal": _keys(listed)}
    plans = _retirement_plan(config, report, returned, set(), _age_limits(config))
    assert plans[path] == {closed["url"]: "no longer listed by usajobs:federal"}

    _retire_dead(config, report, plans)
    remaining = [job["id"] for job in json.loads(path.read_text())["jobs"]]
    assert remaining == [listed["id"], aged["id"], manual["id"]]
    assert report.retired == 1
    assert json.loads(path.read_text())["count"] == 3


def test_absence_is_not_trusted_after_a_failed_or_empty_fetch(tmp_path):
    from tactical_jobs.config import SourceConfig
    from tactical_jobs.models import SourceError
    from tactical_jobs.pipeline import RunReport, _age_limits, _retirement_plan

    config = _retire_config(
        tmp_path,
        [
            SourceConfig(kind="workday", name="kbr", options={"max_age_days": 0}),
            SourceConfig(kind="workday", name="gdit", options={"max_age_days": 0}),
        ],
    )
    kbr, gdit = _row("workday:kbr", 1), _row("workday:gdit", 2)
    path = _board(tmp_path, [kbr, gdit])
    limits = _age_limits(config)

    # KBR errored (its one returned row is partial output); GDIT returned nothing.
    report = RunReport()
    report.errors.append(SourceError("kbr", "HTTP 403"))
    plans = _retirement_plan(config, report, {"workday:kbr": {"other"}}, set(), limits)
    assert plans[path] == {}


def test_the_safety_valve_keeps_a_source_that_mostly_vanished(tmp_path):
    """A fetch that lost most of a source at once failed partway; a board
    must not be emptied by one bad night. Small sources may lose everything."""
    from tactical_jobs.config import SourceConfig
    from tactical_jobs.pipeline import RunReport, _age_limits, _retirement_plan

    config = _retire_config(
        tmp_path,
        [
            SourceConfig(kind="workday", name="kbr", options={"max_age_days": 0}),
            SourceConfig(kind="oraclecloud", name="hjf", options={"max_age_days": 0}),
        ],
    )
    kbr = [_row("workday:kbr", n) for n in range(12)]
    hjf = [_row("oraclecloud:hjf", 99)]
    path = _board(tmp_path, kbr + hjf)
    limits = _age_limits(config)

    # KBR returned 2 of its 12 entries: ten absent, over the valve -> kept.
    returned = {"workday:kbr": _keys(kbr[0]) | _keys(kbr[1]), "oraclecloud:hjf": {"something-else"}}
    plans = _retirement_plan(config, RunReport(), returned, set(), limits)
    assert plans[path] == {hjf[0]["url"]: "no longer listed by oraclecloud:hjf"}

    # KBR returned 8 of 12: four absent, within the valve -> retired.
    returned["workday:kbr"] = set().union(*(_keys(r) for r in kbr[:8]))
    plans = _retirement_plan(config, RunReport(), returned, set(), limits)
    assert set(plans[path]) == {r["url"] for r in kbr[8:]} | {hjf[0]["url"]}


def test_a_refetched_posting_the_classifier_rejects_is_retired(tmp_path):
    """The merge only ever adds, so a posting the classifier turned away on
    re-fetch stayed on the board for ever (three did, audit 2026-09-05)."""
    import json

    from tactical_jobs.config import SourceConfig
    from tactical_jobs.pipeline import RunReport, _age_limits, _retire_dead, _retirement_plan

    config = _retire_config(
        tmp_path, [SourceConfig(kind="jsonld", name="nsca", options={})]
    )
    keep, reject = _row("jsonld:nsca", 1), _row("jsonld:nsca", 2, "Marine Investigator")
    path = _board(tmp_path, [keep, reject])
    report = RunReport()
    plans = _retirement_plan(config, report, {"jsonld:nsca": _keys(keep) | _keys(reject)}, _keys(reject), _age_limits(config))
    assert plans[path] == {reject["url"]: "classifier: reject"}
    _retire_dead(config, report, plans)
    assert [job["id"] for job in json.loads(path.read_text())["jobs"]] == [keep["id"]]
