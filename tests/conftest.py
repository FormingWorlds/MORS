"""Shared fixtures for the MORS test suite.

Provides process-wide state isolation so tests stay order-independent regardless
of which files run before them.
"""

from __future__ import annotations

import copy

import pytest

from mors import parameters


@pytest.fixture(autouse=True)
def _restore_params_default():
    """Snapshot and restore the shared default-parameter dictionary around each test.

    ``mors.parameters.paramsDefault`` is a module-level dictionary that several
    entry points use as a default argument. A test that constructs a real
    ``Star`` or ``Cluster`` (or otherwise writes into a parameter dictionary that
    aliases the default) could leave the default altered for later tests that
    derive their parameters from it. Restoring the snapshot after every test
    keeps the suite deterministic no matter the collection order.
    """
    snapshot = copy.deepcopy(parameters.paramsDefault)
    yield
    parameters.paramsDefault.clear()
    parameters.paramsDefault.update(snapshot)
