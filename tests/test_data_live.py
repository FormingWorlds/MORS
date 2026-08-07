"""Live check that the committed Baraffe registry matches its Zenodo record.

Nightly/slow tier only; needs network. A republished or edited Zenodo deposit is
caught here instead of by a user's failing fetch.

The fetch is retried a few times, and the check is skipped when zenodo.org stays
unreachable, rate-limits, or answers with a server error, so an outage upstream
does not read as registry drift. Every other outcome fails: a checksum that
disagrees with the committed registry, a partial API response, a record that is
gone, and a deposit that lists no files.
"""

from __future__ import annotations

import time

import pytest
import requests

pytestmark = [pytest.mark.slow, pytest.mark.timeout(3600)]

# Number of track files the committed Baraffe registry pins.
BARAFFE_FILE_COUNT = 31

# Statuses that mean zenodo.org is busy or unwell rather than the pinned record
# being wrong: 429 is rate limiting, the 5xx entries are gateway and backend
# failures.
TRANSIENT_STATUSES = frozenset({429, 500, 502, 503, 504})

# Attempts per check, spaced by RETRY_BACKOFF_S * 2**attempt seconds.
FETCH_ATTEMPTS = 3
RETRY_BACKOFF_S = 5.0


def _upstream_failure(exc: Exception) -> str | None:
    """Report zenodo.org being unavailable, or None for anything else.

    A stalled Zenodo API surfaces as a timeout when the client's own clock
    expires first and as an HTTP 5xx when the gateway answers first, so both
    shapes describe the same condition.
    """
    if isinstance(exc, requests.exceptions.HTTPError):
        status = getattr(exc.response, 'status_code', None)
        if status in TRANSIENT_STATUSES:
            return f'zenodo.org returned HTTP {status}'
        return None
    if isinstance(exc, requests.exceptions.Timeout):
        return 'zenodo.org did not answer before the request timed out'
    if isinstance(exc, requests.exceptions.ConnectionError):
        return 'zenodo.org could not be reached'
    return None


def _fetch_live_registry(doi: str) -> dict[str, str]:
    """Return a Zenodo record's registry, retrying while the API is stalled.

    Skips the calling test once the attempts are spent on an unavailable
    zenodo.org. Every other failure propagates: a missing record, a concept DOI,
    and a deposit that lists no files are defects rather than weather.
    """
    from fwl_io.sync import fetch_zenodo_registry

    failure = ''
    for attempt in range(FETCH_ATTEMPTS):
        try:
            return fetch_zenodo_registry(doi)
        except requests.exceptions.RequestException as exc:
            reason = _upstream_failure(exc)
            if reason is None:
                raise
            failure = reason
            if attempt < FETCH_ATTEMPTS - 1:
                time.sleep(RETRY_BACKOFF_S * 2**attempt)
    pytest.skip(f'{failure} on all {FETCH_ATTEMPTS} attempts; the live registry is unreadable')


def test_committed_baraffe_registry_matches_live_zenodo():
    """The 31 committed Baraffe checksums equal the live Zenodo record's."""
    import mors.data as data

    ds = data._baraffe_dataset()
    committed = ds.registry()
    live = _fetch_live_registry(ds.zenodo)
    # Guard against a vacuous match on an empty/partial API response.
    assert len(live) == len(committed) == BARAFFE_FILE_COUNT, (
        f'Zenodo record {ds.zenodo} listed {len(live)} files against '
        f'{len(committed)} committed, expected {BARAFFE_FILE_COUNT} of each'
    )
    # Every committed checksum matches the live deposit; any drift fails here.
    assert live == committed, f'Baraffe registry has drifted from Zenodo record {ds.zenodo}'
