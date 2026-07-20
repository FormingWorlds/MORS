"""Live check that the committed Baraffe registry matches its Zenodo record.

Nightly/slow tier only; needs network. This re-homes the registry-drift guard
that previously lived in fwl-io's shared-manifest live test, now that MORS owns
the Baraffe dataset. A republished or edited Zenodo deposit is caught here
instead of by a user's failing fetch.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.timeout(3600)]


def test_committed_baraffe_registry_matches_live_zenodo():
    """The 31 committed Baraffe checksums equal the live Zenodo record's."""
    from fwl_io.sync import fetch_zenodo_registry

    import mors.data as data

    ds = data._baraffe_dataset()
    committed = ds.registry()
    live = fetch_zenodo_registry(ds.zenodo)
    # Guard against a vacuous match on an empty/partial API response.
    assert len(live) == len(committed) == 31
    # Every committed checksum matches the live deposit; any drift fails here.
    assert live == committed, f'Baraffe registry has drifted from Zenodo record {ds.zenodo}'
