"""Guards on the live Baraffe registry check in tests/test_data_live.py.

Pins which upstream conditions skip the live check and which still fail it. A
zenodo.org that stays unreachable, rate-limits, returns a server error, or breaks
off the response body skips once the retries are spent; a successful fetch that
disagrees with the committed registry, a short response, a body that is not JSON,
a record that is gone, and a deposit that lists no files all fail. The fetch
itself is replaced by a stub, so nothing here reaches the network.
"""

from __future__ import annotations

import pytest
import requests

# tests/ carries no __init__.py, so pytest's default import mode puts it on
# sys.path and the sibling module resolves by bare name.
import test_data_live as live

import mors.data as data

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

# The statuses the live check is required to read as weather. Pinned here rather
# than read from the source, so narrowing the source set fails a test instead of
# quietly collecting fewer cases.
EXPECTED_TRANSIENT = (429, 500, 502, 503, 504)


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


def _record_url() -> str:
    """Return the pinned record's API URL, read from the shipped manifest."""
    record_id = data._baraffe_dataset().zenodo.rsplit('.', 1)[-1]
    return f'https://zenodo.org/api/records/{record_id}'


def _http_error(status: int) -> requests.exceptions.HTTPError:
    """Build the error ``raise_for_status`` raises for a given status code."""
    response = requests.Response()
    response.status_code = status
    response.url = _record_url()
    kind = 'Client Error' if status < 500 else 'Server Error'
    return requests.exceptions.HTTPError(
        f'{status} {kind} for url: {response.url}', response=response
    )


def _install(monkeypatch, stub: _StubFetch) -> None:
    """Route the live check through ``stub`` and drop the backoff to zero."""
    # The stub only lands because the fetch is imported inside the function
    # under test, so the name is looked up on fwl_io.sync at call time.
    assert not hasattr(live, 'fetch_zenodo_registry')
    monkeypatch.setattr('fwl_io.sync.fetch_zenodo_registry', stub)
    monkeypatch.setattr(live, 'RETRY_BACKOFF_S', 0.0)


def _committed() -> dict[str, str]:
    """Return the committed Baraffe registry, read from the shipped file."""
    return data._baraffe_dataset().registry()


def test_the_transient_status_set_is_the_pinned_one():
    """The statuses read as weather are the rate-limit and server-error codes."""
    assert live.TRANSIENT_STATUSES == frozenset(EXPECTED_TRANSIENT)
    # A record that is gone is a defect, so its status must never be in the set.
    assert 404 not in live.TRANSIENT_STATUSES


def test_the_fetch_is_retried_with_a_growing_wait():
    """The check makes more than one attempt, and waits between them."""
    assert live.FETCH_ATTEMPTS > 1
    assert live.RETRY_BACKOFF_S > 0


@pytest.mark.parametrize('status', EXPECTED_TRANSIENT)
def test_every_transient_status_skips_the_live_check(monkeypatch, status):
    """Each status MORS reads as an unwell zenodo.org skips rather than fails."""
    stub = _StubFetch(_http_error(status))
    _install(monkeypatch, stub)
    with pytest.raises(pytest.skip.Exception, match=f'HTTP {status}'):
        live.test_committed_baraffe_registry_matches_live_zenodo()
    # Every attempt is spent before giving up, and there is more than one, so a
    # status that clears partway through still completes the check.
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


@pytest.mark.parametrize(
    'error',
    [
        requests.exceptions.ChunkedEncodingError('Connection broken: IncompleteRead'),
        requests.exceptions.ContentDecodingError(
            'Received response with content-encoding: gzip'
        ),
    ],
    ids=['truncated_body', 'undecodable_body'],
)
def test_incomplete_response_body_skips_the_live_check(monkeypatch, error):
    """A response body that does not arrive intact skips, not fails.

    Neither class carries a status code, so the classifier has to recognise
    them by type rather than through the status branch.
    """
    stub = _StubFetch(error)
    _install(monkeypatch, stub)
    with pytest.raises(pytest.skip.Exception, match='incomplete response body'):
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


def test_the_retry_waits_longer_after_each_attempt(monkeypatch):
    """The gap between attempts grows, so a struggling Zenodo is not hammered."""
    waits: list[float] = []
    monkeypatch.setattr(live.time, 'sleep', waits.append)
    stub = _StubFetch(_http_error(503))
    monkeypatch.setattr('fwl_io.sync.fetch_zenodo_registry', stub)
    with pytest.raises(pytest.skip.Exception, match='HTTP 503'):
        live.test_committed_baraffe_registry_matches_live_zenodo()
    # One wait fewer than attempts: the last failure skips instead of sleeping.
    assert len(waits) == live.FETCH_ATTEMPTS - 1
    assert waits[0] > 0
    assert all(later > earlier for earlier, later in zip(waits, waits[1:]))


def test_missing_record_fails_the_live_check(monkeypatch):
    """A pinned record that is gone from Zenodo fails, and is not retried."""
    stub = _StubFetch(_http_error(404))
    _install(monkeypatch, stub)
    with pytest.raises(requests.exceptions.HTTPError, match='404 Client Error'):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # A record that is gone stays gone, so retrying it would only add delay.
    assert stub.calls == 1


def test_missing_record_after_a_stall_fails_the_live_check(monkeypatch):
    """A 404 arriving on a retry fails there, rather than being absorbed."""
    stub = _StubFetch(_http_error(503), _http_error(404))
    _install(monkeypatch, stub)
    with pytest.raises(requests.exceptions.HTTPError, match='404 Client Error'):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # The earlier stall must not carry the run to a skip and bury the 404.
    assert stub.calls == 2


def test_non_json_body_fails_the_live_check(monkeypatch):
    """A response carrying something other than JSON fails, and is not retried."""
    stub = _StubFetch(requests.exceptions.JSONDecodeError('Expecting value', '<html>', 0))
    _install(monkeypatch, stub)
    with pytest.raises(requests.exceptions.JSONDecodeError):
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # A body that is not JSON says nothing about the deposit, so reading it as
    # weather would hide a change in what the API returns.
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
    expected = rf'listed {live.BARAFFE_FILE_COUNT - 1} files'
    with pytest.raises(AssertionError, match=expected) as excinfo:
        _without_skipping(live.test_committed_baraffe_registry_matches_live_zenodo)
    # The count guard is what fires: a short response never reaches the
    # checksum comparison, so it cannot be reported as drift.
    assert 'drifted' not in str(excinfo.value)
    assert stub.calls == 1
