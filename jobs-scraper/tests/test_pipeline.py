

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
