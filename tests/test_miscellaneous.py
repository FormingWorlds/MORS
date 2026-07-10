"""Tests for src/mors/miscellaneous.py.

Exercises the shared array and index helpers used across MORS: float / array
coercion (`_convertFloatArray`), pickle round-trip loading (`Load`), the three
index-lookup helpers (`_getIndexLT`, `_getIndexGT`, `_getIndexLTordered`), and
the two emission-track routines (`ActivityLifetime`, `IntegrateEmission`).

This is a utility source, so the tests check the helper contracts directly:
an activity lifetime stays within the age-array bounds, and an emission
integral of a constant luminosity reduces to the closed-form rectangle
`L * (AgeMax - AgeMin)` in seconds.
"""

from __future__ import annotations

import pickle

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors.constants as const
from mors import miscellaneous as misc

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


class _PickleStar:
    """Minimal stand-in for a saved Star / Cluster that exposes the reload hook."""

    def __init__(self, tag):
        self.tag = tag
        self.reloaded = False

    def _setupQuantityFunctions(self):
        # Load() calls this after unpickling; record that it ran so the test can
        # assert the reload hook fired rather than being silently skipped.
        self.reloaded = True


def test_convert_float_array_scalar_and_list():
    """A scalar returns a plain float; a list of numeric strings returns a float array."""
    scalar = misc._convertFloatArray(3)
    assert isinstance(scalar, float)
    # Discriminate against an int passthrough: the return type must be float.
    assert scalar == pytest.approx(3.0)

    out = misc._convertFloatArray(['1.5', '2', 4])
    assert isinstance(out, np.ndarray)
    assert out.dtype == np.float64
    # Values are element-wise floats of the mixed str/int input.
    assert_allclose(out, np.array([1.5, 2.0, 4.0]), rtol=1e-12)


def test_convert_float_array_numpy_single_and_multi():
    """A zero-dimensional numpy array collapses to a float; a multi-element array stays an array."""
    single = misc._convertFloatArray(np.array(7.25))
    assert isinstance(single, float)
    # A wrong branch that returned the 0-d array would not be a plain float.
    assert single == pytest.approx(7.25)

    multi = misc._convertFloatArray(np.array([1.0, 2.0, 3.0]))
    assert isinstance(multi, np.ndarray)
    assert len(multi) == 3
    assert_allclose(multi, np.array([1.0, 2.0, 3.0]), rtol=1e-12)


def test_convert_float_array_unsupported_returns_none():
    """An unsupported type (string) falls through every branch and returns None."""
    result = misc._convertFloatArray('not-a-number')
    assert result is None
    # A dict is likewise unsupported and must not raise, just return None.
    assert misc._convertFloatArray({'a': 1}) is None


def test_load_roundtrip_calls_setup_hook(tmp_path):
    """Load unpickles a saved object and re-runs its quantity-function setup hook."""
    obj = _PickleStar('alpha-cen')
    path = tmp_path / 'star.pkl'
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

    loaded = misc.Load(str(path))
    # The payload survives the round-trip.
    assert loaded.tag == 'alpha-cen'
    # The reload hook that pickling drops must have been re-invoked by Load.
    assert loaded.reloaded is True


def test_model_cluster_reads_distribution():
    """ModelCluster loads the packaged Johnstone (2020) mass / rotation distribution."""
    Mstar, Omega = misc.ModelCluster()
    # The two arrays describe the same set of stars, so their lengths must match.
    assert len(Mstar) == len(Omega)
    assert len(Mstar) > 0
    # Stellar masses and rotation rates are physical positive quantities.
    assert np.all(Mstar > 0.0)
    assert np.all(Omega > 0.0)


def test_get_index_lt_ordered_descending_search_path():
    """_getIndexLTordered narrows from the upper end when the midpoint overshoots the query."""
    arr = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    # 5 lies in the first bin; the search must move the upper bound down to reach it.
    assert misc._getIndexLTordered(arr, 5.0) == 0
    # 35 lies in the last interior bin [30, 40).
    assert misc._getIndexLTordered(arr, 35.0) == 3


def test_get_index_lt_interior_and_boundary():
    """_getIndexLT returns the closest element below the query on an unordered array."""
    arr = np.array([0.0, 10.0, 5.0, 30.0, 20.0])
    # 12 sits just above the element 10.0 at index 1; the nearest smaller is 10.0.
    assert misc._getIndexLT(arr, 12.0) == 1
    # Exact hit on an array value returns that element's own index (delta 0).
    assert misc._getIndexLT(arr, 20.0) == 4


def test_get_index_lt_below_minimum_raises():
    """_getIndexLT rejects a query strictly below the array minimum."""
    arr = np.array([1.0, 2.0, 3.0])
    with pytest.raises(Exception, match='less than minimum'):
        misc._getIndexLT(arr, 0.5)
    # A query at the minimum itself is in range and returns that index.
    assert misc._getIndexLT(arr, 1.0) == 0


def test_get_index_gt_interior_and_boundary():
    """_getIndexGT returns the closest element above the query on an unordered array."""
    arr = np.array([0.0, 10.0, 5.0, 30.0, 20.0])
    # 12 sits just below 20.0 (index 4), the nearest larger element.
    assert misc._getIndexGT(arr, 12.0) == 4
    # Exact hit returns that element's index.
    assert misc._getIndexGT(arr, 10.0) == 1


def test_get_index_gt_above_maximum_raises():
    """_getIndexGT rejects a query strictly above the array maximum."""
    arr = np.array([1.0, 2.0, 3.0])
    with pytest.raises(Exception, match='more than maximum'):
        misc._getIndexGT(arr, 5.0)
    # A query at the maximum is in range and returns the last index.
    assert misc._getIndexGT(arr, 3.0) == 2


def test_get_index_lt_ordered_interior_and_endpoints():
    """_getIndexLTordered binary-searches an ascending array for the bracketing index."""
    arr = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    # 25 lies in the bin [20, 30): the lower bracket index is 2.
    assert misc._getIndexLTordered(arr, 25.0) == 2
    # Endpoint short-circuits: an exact match on the first element returns 0.
    assert misc._getIndexLTordered(arr, 0.0) == 0
    # An exact match on the last element returns the final index.
    assert misc._getIndexLTordered(arr, 40.0) == 4


def test_activity_lifetime_crossing_within_bounds():
    """A track that decays past a threshold yields a crossing age inside the age span."""
    Age = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    Track = np.array([10.0, 8.0, 6.0, 4.0, 2.0])
    life = misc.ActivityLifetime(Age=Age, Track=Track, Threshold=5.0)
    # Linear interpolation between (3 Myr, 6) and (4 Myr, 4) crosses 5 at 3.5 Myr.
    assert life == pytest.approx(3.5, rel=1e-9)
    # A wrong-direction interpolation would land outside [3, 4]; guard the bound.
    assert Age[0] <= life <= Age[-1]


def test_activity_lifetime_never_below_threshold_returns_final_age():
    """If the final value is still above the threshold, the full track age is returned."""
    Age = np.array([1.0, 2.0, 3.0])
    Track = np.array([100.0, 90.0, 80.0])
    life = misc.ActivityLifetime(Age=Age, Track=Track, Threshold=10.0)
    assert life == pytest.approx(3.0, rel=1e-12)
    # The star is active over the whole track, so the lifetime is the last age.
    assert life >= Age[-1]


def test_activity_lifetime_always_below_threshold_returns_zero():
    """A track sitting below the threshold at every node yields a zero lifetime."""
    Age = np.array([1.0, 2.0, 3.0])
    Track = np.array([1.0, 0.5, 0.25])
    life = misc.ActivityLifetime(Age=Age, Track=Track, Threshold=10.0)
    assert life == pytest.approx(0.0, abs=1e-12)
    # A nonzero return here would signal a spurious crossing detection.
    assert life < Age[0]


def test_activity_lifetime_exact_threshold_node():
    """A node equal to the threshold just before a below-threshold node is reported directly."""
    Age = np.array([1.0, 2.0, 3.0, 4.0])
    Track = np.array([9.0, 5.0, 3.0, 1.0])
    # Track[-1]=1 < threshold, and node index 1 equals the threshold exactly.
    life = misc.ActivityLifetime(Age=Age, Track=Track, Threshold=5.0)
    assert life == pytest.approx(2.0, rel=1e-12)
    assert Age[0] <= life <= Age[-1]


def test_activity_lifetime_agemax_truncates_track():
    """AgeMax restricts the search window; a late crossing beyond it is ignored."""
    Age = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    Track = np.array([10.0, 8.0, 6.0, 4.0, 2.0])
    # Truncated at 2.5 Myr the retained track ends at 8.0, still above 5.0.
    life = misc.ActivityLifetime(Age=Age, Track=Track, Threshold=5.0, AgeMax=2.5)
    assert life == pytest.approx(2.0, rel=1e-12)
    assert life <= 2.5


def test_activity_lifetime_missing_arguments_raise():
    """Each required argument left unset raises, and length mismatch is rejected."""
    Age = np.array([1.0, 2.0, 3.0])
    Track = np.array([3.0, 2.0, 1.0])
    with pytest.raises(Exception, match='Age not set'):
        misc.ActivityLifetime(Track=Track, Threshold=1.0)
    with pytest.raises(Exception, match='Track not set'):
        misc.ActivityLifetime(Age=Age, Threshold=1.0)
    with pytest.raises(Exception, match='Threshold not set'):
        misc.ActivityLifetime(Age=Age, Track=Track)
    with pytest.raises(Exception, match='different lengths'):
        misc.ActivityLifetime(Age=Age, Track=np.array([1.0, 2.0]), Threshold=1.0)


def test_integrate_emission_constant_luminosity_matches_rectangle():
    """A constant luminosity integrates to L * (AgeMax - AgeMin), converted Myr to s.

    Analytical anchor: the trapezoidal integral of a constant integrand over an
    interval equals the exact rectangle area. This pins the Myr->s unit factor
    and discriminates a dropped conversion (which would be ~10^13 times smaller).
    """
    Age = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    L0 = 1.0e28
    Luminosity = np.full_like(Age, L0)
    energy = misc.IntegrateEmission(AgeMin=0.5, AgeMax=3.5, Age=Age, Luminosity=Luminosity)
    expected = L0 * (3.5 - 0.5) * const.Myr
    assert energy == pytest.approx(expected, rel=1e-9)
    # Positivity guard: an integrated emission is strictly positive.
    assert energy > 0.0
    # Unit guard: without the Myr->s factor the result would be smaller by const.Myr.
    assert energy > 1.0e6 * L0 * (3.5 - 0.5)


def test_integrate_emission_fluence_scales_with_orbit():
    """Supplying aOrb converts the energy to a fluence that falls as 1/aOrb^2."""
    Age = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    L0 = 2.0e27
    Luminosity = np.full_like(Age, L0)
    aOrb = 0.5
    fluence = misc.IntegrateEmission(
        AgeMin=0.0, AgeMax=4.0, Age=Age, Luminosity=Luminosity, aOrb=aOrb
    )
    energy = misc.IntegrateEmission(AgeMin=0.0, AgeMax=4.0, Age=Age, Luminosity=Luminosity)
    geom = 4.0 * const.Pi * (aOrb * const.AU) ** 2.0
    assert fluence == pytest.approx(energy / geom, rel=1e-9)
    # A fluence at a finite orbit is far smaller than the total energy budget.
    assert 0.0 < fluence < energy


def test_integrate_emission_zero_width_interval_is_zero():
    """Integrating over a degenerate interval pinned to a single node yields zero energy."""
    Age = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    Luminosity = np.full_like(Age, 5.0e27)
    energy = misc.IntegrateEmission(
        AgeMin=2.0, AgeMax=2.0, Age=Age, Luminosity=Luminosity
    )
    assert energy == pytest.approx(0.0, abs=1e-6)
    # A zero-width window cannot accumulate a positive energy.
    assert energy < 1.0
    # A finite window over the same track does accumulate energy, confirming the
    # zero result is the interval, not a broken integrand.
    finite = misc.IntegrateEmission(
        AgeMin=1.0, AgeMax=3.0, Age=Age, Luminosity=Luminosity
    )
    assert finite > 0.0


def test_integrate_emission_missing_and_out_of_range_raise():
    """Missing arguments, length mismatch, and out-of-range ages all raise."""
    Age = np.array([0.0, 1.0, 2.0])
    Lum = np.array([1.0, 1.0, 1.0])
    with pytest.raises(Exception, match='AgeMin not set'):
        misc.IntegrateEmission(AgeMax=2.0, Age=Age, Luminosity=Lum)
    with pytest.raises(Exception, match='AgeMax not set'):
        misc.IntegrateEmission(AgeMin=0.0, Age=Age, Luminosity=Lum)
    with pytest.raises(Exception, match='Age not set'):
        misc.IntegrateEmission(AgeMin=0.0, AgeMax=2.0, Luminosity=Lum)
    with pytest.raises(Exception, match='Luminosity not set'):
        misc.IntegrateEmission(AgeMin=0.0, AgeMax=2.0, Age=Age)
    with pytest.raises(Exception, match='different lengths'):
        misc.IntegrateEmission(
            AgeMin=0.0, AgeMax=2.0, Age=Age, Luminosity=np.array([1.0, 1.0])
        )
    with pytest.raises(Exception, match='AgeMin not in range'):
        misc.IntegrateEmission(AgeMin=-1.0, AgeMax=2.0, Age=Age, Luminosity=Lum)
    with pytest.raises(Exception, match='AgeMax not in range'):
        misc.IntegrateEmission(AgeMin=0.0, AgeMax=5.0, Age=Age, Luminosity=Lum)
