"""The CATS portal reader, against the markup Reef Systems' portal serves."""

from tactical_jobs.sources.catsone import CATSOneSource, _list_jobs, _parse_detail

LIST = """
<div class="jobs-table">
<div class="table-row"><div class="data-cell" data-label="Title"><a href="/careers/5332/jobs/16473510-Doctor-of-Physical-Therapy-DPT-HPO-Fort-Riley-KS">Doctor of Physical Therapy (DPT) &ndash; HPO &ndash; Fort Riley, KS</a></div>
<div class="data-cell" data-label="Category">Government/Military</div><div class="data-cell" data-label="Location">Fort Riley, Kansas</div></div>
<div class="table-row"><div class="data-cell" data-label="Title"><a href="/careers/5332/jobs/16849027-Cognitive-Performance-Coach-CPC-Travis-AFB-CA-94535">Cognitive Performance Coach (CPC) &ndash; Travis AFB, CA 94535</a></div>
<div class="data-cell" data-label="Category">Government/Military</div><div class="data-cell" data-label="Location">Travis AFB, CA</div></div>
<div class="table-row"><div class="data-cell" data-label="Title"><a href="/careers/5332/jobs/16473510-Doctor-of-Physical-Therapy-DPT-HPO-Fort-Riley-KS">duplicate row</a></div></div>
</div>
"""

DETAIL = """
<main id="job"><div class="container"><div class="job-description-container"><a class="view-all-jobs" href="/careers/5332">View all jobs</a>
<div><div class="job-header"><h1>Doctor of Physical Therapy (DPT) &ndash; HPO &ndash; Fort Riley, KS</h1><ul class="job-tags"><li>Fort Riley, Kansas</li><li>Government/Military</li></ul></div><hr/>
<div class="job-description"><p>Reef Systems is seeking a fully qualified Doctor of Physical Therapy to support the 10 ASOS at Fort Riley, KS.</p>
<ul><li>Return to duty</li><li>Injury prevention</li></ul></div></div></div></main>
"""


def test_list_rows_are_read_once_each_with_their_location():
    jobs = _list_jobs(LIST, "5332")
    assert [j["id"] for j in jobs] == ["16473510", "16849027"]
    assert jobs[0]["title"] == "Doctor of Physical Therapy (DPT) – HPO – Fort Riley, KS"
    assert jobs[0]["location"] == "Fort Riley, Kansas"
    assert jobs[1]["location"] == "Travis AFB, CA"
    assert jobs[0]["path"].startswith("/careers/5332/jobs/16473510-")


def test_detail_reads_header_tags_and_body():
    d = _parse_detail(DETAIL)
    assert d["title"] == "Doctor of Physical Therapy (DPT) – HPO – Fort Riley, KS"
    assert d["tags"] == ["Fort Riley, Kansas", "Government/Military"]
    assert "10 ASOS at Fort Riley" in d["description"]
    assert "Return to duty" in d["description"] and "Injury prevention" in d["description"]
    assert "View all jobs" not in d["description"]


def test_source_yields_postings_with_no_date_and_the_tagged_station(monkeypatch):
    pages = {
        "https://reefsys.catsone.com/careers/5332": LIST,
        "https://reefsys.catsone.com/careers/5332/jobs/16473510-Doctor-of-Physical-Therapy-DPT-HPO-Fort-Riley-KS": DETAIL,
    }
    calls = []

    def fake_fetch(url, **kw):
        calls.append(url)
        return pages.get(url, "<main><h1>Other</h1></main>").encode()

    monkeypatch.setattr("tactical_jobs.sources.catsone.fetch", fake_fetch)
    postings = list(CATSOneSource("reef", {"subdomain": "reefsys", "portal": 5332, "employer": "Reef Systems", "detail_limit": 1}).fetch())
    assert len(postings) == 2
    first, second = postings
    assert first.source == "catsone:reef" and first.source_id == "16473510"
    assert first.url == "https://reefsys.catsone.com/careers/5332/jobs/16473510-Doctor-of-Physical-Therapy-DPT-HPO-Fort-Riley-KS"
    assert first.employer == "Reef Systems"
    assert first.location == "Fort Riley, KS"  # the title's place, not the tag
    assert first.posted_at is None
    assert "10 ASOS" in first.description and "Category: Government/Military." in first.description
    # past detail_limit: list-level fields only
    assert second.location == "Travis AFB, CA" and second.description == second.title  # zip code in the title: the list cell
    assert len(calls) == 2


def test_tag_is_used_when_the_title_names_no_place(monkeypatch):
    detail = DETAIL.replace("Doctor of Physical Therapy (DPT) &ndash; HPO &ndash; Fort Riley, KS", "Physical Therapist")
    listing = LIST.replace("Doctor of Physical Therapy (DPT) &ndash; HPO &ndash; Fort Riley, KS", "Physical Therapist")
    pages = {"https://reefsys.catsone.com/careers/5332": listing,
             "https://reefsys.catsone.com/careers/5332/jobs/16473510-Doctor-of-Physical-Therapy-DPT-HPO-Fort-Riley-KS": detail}
    monkeypatch.setattr("tactical_jobs.sources.catsone.fetch", lambda url, **kw: pages.get(url, "<main></main>").encode())
    first = next(iter(CATSOneSource("reef", {"subdomain": "reefsys", "portal": 5332, "detail_limit": 1}).fetch()))
    assert first.location == "Fort Riley, Kansas"
