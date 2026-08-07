"""Guards on the live Baraffe registry check in tests/test_data_live.py.

Pins which upstream conditions skip the live check and which still fail it. A
zenodo.org that stays unreachable, rate-limits, or returns a server error skips
once the retries are spent; a successful fetch that disagrees with the committed
registry, a short response, a record that is gone, and a deposit that lists no
files all fail. The fetch itself is replaced by a stub, so nothing here reaches
the network.
"""

from __future__ import annotations

import pytest
import requests
import test_data_live as live

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

# Any DOI does, since the fetch is stubbed out; this is the pinned Baraffe one.
BARAFFE_DOI = '10.5281/zenodo.15729114'


class _UnexpectedSkip(Exception):
    """Raised when the live check skips a condition it is required to fail on."""


def _without_skipping(call):
    """Run ``call``, turning a skip into an error no ``pytest.raises`` block absorbs.

    ``Skipped`` derives from ``BaseException``, so a ``pytest.raises`` block lets
    it through and the surrounding test reports as skipped rather than failed. A
    guard blinded that way would read green in CI, which is what this converts.
    """
    try:
        return call()
    except pytest.skip.Exception as exc:
        raise _UnexpectedSkip(f'the live check skipped instead of failing: {exc}') from exc


class _StubFetch:
    """Stand-in for the fwl-io registry fetch that counts calls and replays outcomes.

    The last outcome repeats once the list is exhausted, so a single entry
    describes an upstream condition that persists across every attempt.
    """

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self, doi, **kwargs):
        self.calls += 1
        outcome = self.outcomes[min(self.calls - 1, len(self.outcomes) - 1)]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _http_error(status: int, kind: str) -> requests.exceptions.HTTPError:
    """Build the error ``raise_for_status`` raises for a given status code."""
    response = requests.Response()
    response.status_code = status
    response.url = f'https://zenodo.org/api/records/{BARAFFE_DOI.rsplit(".", 1)[-1]}'
    return requests.exceptions.HTTPError(
        f'{status} {kind} for url: {response.url}', response=response
    )


def _install(monkeypatch, stub: _StubFetch) -> None:
    """Route the live check through ``stub`` and drop the backoff to zero."""
    monkeypatch.setattr('fwl_io.sync.fetch_zenodo_registry', stub)
    monkeypatch.setattr(live, 'RETRY_BACKOFF_S', 0.0)


def _committed() -> dict[str, str]:
    """Return the committed Baraffe registry, read from the shipped file."""
    import mors.data as data

    return data._baraffe_dataset().registry()


def test_sustained_gateway_error_skips_the_live_check(monkeypatch):
    """A Zenodo gateway that answers 504 on every attempt skips, not fails."""
    stub = _StubFetch(_http_error(504, 'Server Error'))
    _install(monkeypatch, stub)
    with pytest.raises(pytest.skip.Exception, match='HTTP 504'):
        live.test_committed_baraffe_registry_matches_live_zenodo()
    # Every attempt is spent before giving up, so a stall shorter than the
    # backoff window still completes the check.
    assert stub.calls == live.FETCH_ATTEMPTS
    assert live.FETCH_ATTEMPTS > 1


def test_sustained_read_timeout_skips_the_live_check(monkeypatch):
    """A Zenodo API that never answers within the client timeout skips, not fails.

    The same outage reaches the check as a timeout or as a 5xx depending on
    which clock expires first, so both shapes are pinned.
    """
    stalled = requests.exceptions.ReadTimeout(
        "HTTPSConnectionPool(host='zenodo.org', port=443): Read timed out. (read timeout=30)"
    )
    stub = _StubFetch(stalled)
    _install(monkeypatch, stub)
    with pytest.raises(pytest.skip.Exception, match='timed out'):
        live.test_committed_baraffe_registry_matches_live_zenodo()
    assert stub.calls == live.FETCH_ATTEMPTS
    assert live.FETCH_ATTEMPTS > 1


def test_unreachable_host_skips_the_live_check(monkeypatch):
    """A zenodo.org that cannot be reached at all skips, not fails."""
    stub = _StubFetch(requests.exceptions.ConnectionError('Name or service not known'))
    _install(monkeypatch, stub)
    with pytest.raises(pytest.skip.Exception, match='could not be reached'):
        live.test_committed_baraffe_registry_matches_live_zenodo()
    assert stub.calls == live.FETCH_ATTEMPTS
    assert live.FETCH_ATTEMPTS > 1


def test_a_single_stall_is_absorbed_by_the_retry(monkeypatch):
    """One stalled attempt followed by an answer completes the check."""
    stub = _StubFetch(requests.exceptions.ReadTimeout('Read timed out.'), _committed())
    _install(monkeypatch, stub)
    _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # The second attempt is what answered, so the retry did the work rather
    # than the first call having quietly succeeded.
    assert stub.calls == 2
    assert live.FETCH_ATTEMPTS > 1


def test_missing_record_fails_the_live_check(monkeypatch):
    """A pinned record that is gone from Zenodo fails, and is not retried."""
    stub = _StubFetch(_http_error(404, 'Client Error'))
    _install(monkeypatch, stub)
    with pytest.raises(requests.exceptions.HTTPError, match='404 Client Error'):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # A record that is gone stays gone, so retrying it would only add delay.
    assert stub.calls == 1


def test_deposit_without_files_fails_the_live_check(monkeypatch):
    """A record whose deposit lists no files fails, and is not retried."""
    stub = _StubFetch(ValueError('Zenodo record 15729114 lists no files'))
    _install(monkeypatch, stub)
    with pytest.raises(ValueError, match='lists no files'):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    assert stub.calls == 1


def test_drifted_checksum_fails_the_live_check(monkeypatch):
    """A republished deposit with one changed checksum fails on the comparison."""
    drifted = dict(_committed())
    first = sorted(drifted)[0]
    # A checksum that cannot collide with a real md5 digest, so the failure is
    # unambiguously the drift and not a coincidence.
    drifted[first] = 'md5:' + '0' * 32
    stub = _StubFetch(drifted)
    _install(monkeypatch, stub)
    with pytest.raises(AssertionError, match='drifted from Zenodo record'):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    assert stub.calls == 1


def test_partial_response_fails_the_live_check(monkeypatch):
    """A response listing fewer files than the record holds fails on the count."""
    partial = dict(_committed())
    partial.pop(sorted(partial)[0])
    stub = _StubFetch(partial)
    _install(monkeypatch, stub)
    with pytest.raises(AssertionError, match='listed 30 files') as excinfo:
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # The count guard is what fires: a short response never reaches the
    # checksum comparison, so it cannot be reported as drift.
    assert 'drifted' not in str(excinfo.value)
    assert stub.calls == 1
