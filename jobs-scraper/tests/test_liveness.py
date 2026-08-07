"""Liveness tests.

These pin the one-way bias: ``gone`` requires proof, everything else keeps
the job on the board. No test here touches the network.
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from tactical_jobs import liveness


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200, final_url: str | None = None):
        self._body = body
        self.status = status
        self._final_url = final_url

    def read(self, _n: int | None = None) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._final_url or "https://example.invalid/job/123"

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


@pytest.fixture
def fake_urlopen(monkeypatch):
    """Install a canned response (or exception) for the next check."""

    def install(result):
        def _open(_request, timeout=None):  # noqa: ARG001
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(urllib.request, "urlopen", _open)

    return install


def test_404_retires_the_posting(fake_urlopen):
    fake_urlopen(
        urllib.error.HTTPError("https://x.invalid/job/1", 404, "Not Found", {}, None)
    )
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.GONE
    assert verdict.http_status == 404


def test_410_retires_the_posting(fake_urlopen):
    fake_urlopen(urllib.error.HTTPError("https://x.invalid/job/1", 410, "Gone", {}, None))
    assert liveness.check_url("https://x.invalid/job/1").state == liveness.GONE


def test_403_keeps_the_posting(fake_urlopen):
    # KBR's public job HTML 403s every non-browser fetcher while the
    # requisition is live. Treating 403 as removal would empty the board of
    # exactly the employers that matter most.
    fake_urlopen(
        urllib.error.HTTPError("https://x.invalid/job/1", 403, "Forbidden", {}, None)
    )
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.UNKNOWN
    assert verdict.http_status == 403


@pytest.mark.parametrize("code", [401, 429, 500, 502, 503])
def test_no_other_status_retires_a_posting(fake_urlopen, code):
    fake_urlopen(urllib.error.HTTPError("https://x.invalid/job/1", code, "", {}, None))
    assert liveness.check_url("https://x.invalid/job/1").state == liveness.UNKNOWN


def test_network_failure_keeps_the_posting(fake_urlopen):
    fake_urlopen(urllib.error.URLError("connection reset"))
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.UNKNOWN
    assert "unreachable" in verdict.reason


def test_timeout_keeps_the_posting(fake_urlopen):
    fake_urlopen(TimeoutError("timed out"))
    assert liveness.check_url("https://x.invalid/job/1").state == liveness.UNKNOWN


def test_expired_marker_in_page_text_retires_the_posting(fake_urlopen):
    body = b"<html><body><h1>Careers</h1><p>This job is no longer available.</p></body></html>"
    fake_urlopen(_FakeResponse(body))
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.GONE
    assert "no longer available" in verdict.reason


def test_marker_with_typographic_apostrophe_is_still_caught(fake_urlopen):
    body = "<p>Sorry, this job is not available.</p>".encode()
    fake_urlopen(_FakeResponse(body))
    assert liveness.check_url("https://x.invalid/job/1").state == liveness.GONE


def test_marker_hidden_in_a_script_block_does_not_retire_a_live_job(fake_urlopen):
    # An ATS ships its "no longer available" string in a JS template on every
    # page, live or not. Reading raw HTML would retire the entire board.
    body = (
        b"<html><script>var msgs={expired:'this job is no longer available'};</script>"
        b"<body><h1>Strength and Conditioning Coach</h1><p>Apply now.</p></body></html>"
    )
    fake_urlopen(_FakeResponse(body))
    assert liveness.check_url("https://x.invalid/job/1").state == liveness.LIVE


def test_healthy_page_is_live(fake_urlopen):
    fake_urlopen(_FakeResponse(b"<h1>Athletic Trainer</h1><p>Fort Campbell, KY</p>"))
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.LIVE
    assert verdict.checked_at


def test_redirect_off_the_posting_is_reported_but_not_fatal(fake_urlopen):
    fake_urlopen(
        _FakeResponse(b"<h1>Search jobs</h1>", final_url="https://x.invalid/careers")
    )
    verdict = liveness.check_url("https://x.invalid/job/1")
    assert verdict.state == liveness.LIVE
    assert "redirected" in verdict.reason


def test_non_http_url_is_unknown_not_gone():
    assert liveness.check_url("").state == liveness.UNKNOWN
    assert liveness.check_url("mailto:jobs@example.invalid").state == liveness.UNKNOWN


def test_check_all_deduplicates_and_keys_by_url(monkeypatch):
    seen: list[str] = []

    def _check(url, timeout=None):  # noqa: ARG001
        seen.append(url)
        return liveness.Liveness(url, liveness.LIVE, "reachable")

    monkeypatch.setattr(liveness, "check_url", _check)
    results = liveness.check_all(
        ["https://a.invalid/job/1", "https://a.invalid/job/1", "https://b.invalid/job/2", ""]
    )
    assert sorted(seen) == ["https://a.invalid/job/1", "https://b.invalid/job/2"]
    assert set(results) == {"https://a.invalid/job/1", "https://b.invalid/job/2"}


def test_check_all_with_no_urls_does_no_work(monkeypatch):
    monkeypatch.setattr(
        liveness, "check_url", lambda *a, **k: pytest.fail("should not be called")
    )
    assert liveness.check_all([]) == {}


# --------------------------------------------------------------------------
# Pipeline integration: the sweep has to write down what it found
# --------------------------------------------------------------------------


def _feed(tmp_path, jobs):
    import json
    path = tmp_path / "jobs.json"
    path.write_text(json.dumps({"version": 1, "count": len(jobs), "jobs": jobs}))
    return path


def _config(path):
    from tactical_jobs.config import Config, PublisherConfig
    return Config(
        publishers=[PublisherConfig(kind="jsonfeed", options={"path": str(path)})],
        liveness_check=True,
    )


def test_sweep_stamps_a_healthy_board_so_verified_means_something(tmp_path, monkeypatch):
    # Regression: the rewrite used to be gated on "something changed", so a
    # board where every posting was still live recorded nothing -- and with no
    # stamp, no row could ever be badged verified.
    import json
    from tactical_jobs import pipeline

    path = _feed(tmp_path, [{"id": "a", "url": "https://x.invalid/job/alpha", "title": "A"}])
    monkeypatch.setattr(
        pipeline, "check_all",
        lambda urls, **kw: {
            u: liveness.Liveness(u, liveness.LIVE, "reachable", 200, checked_at="2026-08-07T00:00:00+00:00")
            for u in urls if u
        },
    )
    report = pipeline.RunReport()
    pipeline._retire_dead(_config(path), report)

    written = json.loads(path.read_text())
    assert report.retired == 0
    assert written["jobs"][0]["liveness"]["state"] == "live"
    assert written["jobs"][0]["liveness"]["checked_at"] == "2026-08-07T00:00:00+00:00"


def test_sweep_drops_only_the_dead_row(tmp_path, monkeypatch):
    import json
    from tactical_jobs import pipeline

    path = _feed(tmp_path, [
        {"id": "a", "url": "https://x.invalid/job/alpha", "title": "A"},
        {"id": "b", "url": "https://x.invalid/job/bravo", "title": "B"},
        {"id": "c", "url": "https://x.invalid/job/charlie", "title": "C"},
    ])

    def _check(urls, **kw):
        out = {}
        for u in urls:
            if u.endswith("bravo"):
                out[u] = liveness.Liveness(u, liveness.GONE, "HTTP 404", 404)
            elif u.endswith("charlie"):
                out[u] = liveness.Liveness(u, liveness.UNKNOWN, "HTTP 403", 403)
            else:
                out[u] = liveness.Liveness(u, liveness.LIVE, "reachable", 200)
        return out

    monkeypatch.setattr(pipeline, "check_all", _check)
    report = pipeline.RunReport()
    pipeline._retire_dead(_config(path), report)

    written = json.loads(path.read_text())
    ids = [j["id"] for j in written["jobs"]]
    assert ids == ["a", "c"], "only the confirmed-dead row may be removed"
    assert written["count"] == 2
    assert report.retired == 1
    assert report.unverifiable == 1


def test_sweep_is_skipped_when_disabled(tmp_path, monkeypatch):
    from tactical_jobs import pipeline

    path = _feed(tmp_path, [{"id": "a", "url": "https://x.invalid/job/alpha", "title": "A"}])
    config = _config(path)
    config.liveness_check = False
    monkeypatch.setattr(
        pipeline, "check_all", lambda *a, **k: pytest.fail("should not run")
    )
    pipeline._retire_dead(config, pipeline.RunReport())
