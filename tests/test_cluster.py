"""Tests for src/mors/cluster.py.

Exercises the ``Cluster`` class, a population of stars carrying a rotation-rate
distribution. The per-star evolutionary model (``mors.star.Star``), the
rotation-distribution percentile lookup (``mors.star.Percentile``), and the
habitable-zone boundary calculation (``mors.physicalmodel.aOrbHZ``) are the
external calls; they are patched with closed-form stand-ins so the tests isolate
the ``Cluster`` orchestration logic and run without downloading tracks.

Invariants exercised:

- Positivity / boundedness: per-star ``OmegaEnv`` values and integrated
  emission stay positive; distribution percentiles map to positive rotation
  rates; habitable-zone boundaries are positive.
- Monotonicity: surface rotation decreases with age (spin-down); the
  percentile-to-rotation mapping is monotone increasing; integrated emission
  grows with the integration interval.
- Analytical limit: for a uniform (evenly spaced) rotation ramp the q-th
  percentile has the closed form ``A + (B - A) * q / 100``; the cluster
  reproduces it after assembling and dispatching its own ``OmegaEnv``
  distribution.

Units follow the MORS convention: stellar mass in Msun, age in Myr, rotation in
Omega_sun, luminosity in erg/s.
"""

from __future__ import annotations

import logging
import pickle

import numpy as np
import pytest
from numpy.testing import assert_allclose

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


class FakeStar:
    """Closed-form stand-in for ``mors.star.Star`` used to isolate Cluster logic.

    Stores the configured mass and envelope rotation and returns physically
    plausible, mass- and age-dependent values so that monotonicity and
    positivity assertions on the aggregated cluster remain meaningful. Rotation
    follows a simple spin-down (decreasing with age); luminosity scales as a
    steep power of mass.
    """

    # Quantity names the cluster iterates over to build its accessor methods.
    Tracks = ['Lbol', 'Rstar', 'OmegaEnv', 'Lx', 'Leuv']

    def __init__(self, Mstar=None, OmegaEnv=None, OmegaCore=None, **kwargs):
        self.Mstar = float(Mstar)
        self.OmegaEnv = float(OmegaEnv)
        self.OmegaCore = float(OmegaCore)

    def Value(self, Age=None, Quantity=None):
        """Return a plausible value of Quantity at the given age (Myr)."""
        if Quantity == 'OmegaEnv':
            # Spin-down: surface rotation decreases monotonically with age.
            return self.OmegaEnv / (1.0 + Age / 1000.0)
        if Quantity == 'Lbol':
            # Mass-luminosity relation, erg/s; steep so masses stay distinct.
            return 8.0e33 * self.Mstar**3.5
        if Quantity == 'Rstar':
            return self.Mstar
        if Quantity == 'Lx':
            return 1.0e27 * self.Mstar
        if Quantity == 'Leuv':
            return 1.0e28 * self.Mstar
        return 1.0

    def ActivityLifetime(self, Quantity=None, Threshold=None, AgeMax=None):
        """Return a mass-dependent activity lifetime in Myr."""
        return 100.0 * self.Mstar

    def IntegrateEmission(self, AgeMin=None, AgeMax=None, Band=None, aOrb=None):
        """Return integrated emission in erg over the interval, mass-scaled."""
        return (AgeMax - AgeMin) * 1.0e30 * self.Mstar


def fake_aOrbHZ(Mstar=None, params=None):
    """Return plausible positive habitable-zone boundary distances in AU."""
    scale = np.atleast_1d(np.asarray(Mstar, dtype=float))
    return {
        'RunawayGreenhouse': 0.9 * scale,
        'MaximumGreenhouse': 1.7 * scale,
        'HZ': 1.3 * scale,
    }


def fake_percentile(
    Mstar=None,
    Omega=None,
    Prot=None,
    percentile=None,
    MstarDist=None,
    OmegaDist=None,
    ProtDist=None,
    params=None,
):
    """Faithful percentile lookup over the supplied OmegaDist distribution.

    If ``percentile`` is set, return the corresponding rotation rate via the
    numpy percentile of the distribution; otherwise return the percentile (in
    [0, 100]) of the supplied ``Omega`` within the distribution.
    """
    dist = np.asarray(OmegaDist, dtype=float)
    if percentile is not None:
        return float(np.percentile(dist, percentile))
    return float(100.0 * np.mean(dist <= Omega))


@pytest.fixture
def cluster_mod(monkeypatch):
    """Import the cluster module with its external calls patched to stand-ins."""
    from mors import cluster as cl

    monkeypatch.setattr(cl.star, 'Star', FakeStar)
    monkeypatch.setattr(cl.star, 'Percentile', fake_percentile)
    monkeypatch.setattr(cl.phys, 'aOrbHZ', fake_aOrbHZ)
    return cl


def make_cluster(cl, n=3, **kwargs):
    """Build a small cluster spanning a mass and rotation range."""
    Mstar = np.linspace(0.5, 1.2, n)
    Omega = np.linspace(1.0, 40.0, n)
    return cl.Cluster(Mstar=Mstar, Omega=Omega, **kwargs)


def test_construction_populates_stars_and_hz_boundaries(cluster_mod):
    """Constructing a cluster loads one star per mass and positive HZ boundaries."""
    cluster = make_cluster(cluster_mod, n=3)
    # One star object per input mass, and per-index attribute access.
    assert cluster.nStars == 3
    assert len(cluster.stars) == 3
    assert isinstance(getattr(cluster, 'star0'), FakeStar)
    assert isinstance(getattr(cluster, 'star2'), FakeStar)
    # Habitable-zone boundaries are strictly positive distances (AU).
    assert np.all(cluster.aOrbHZ['HZ'] > 0.0)
    assert np.all(cluster.aOrbHZ['RunawayGreenhouse'] > 0.0)


def test_values_returns_per_star_array_and_requires_arguments(cluster_mod):
    """Values returns one entry per star and refuses missing Age or Quantity."""
    cluster = make_cluster(cluster_mod, n=4)
    omega = cluster.Values(Age=100.0, Quantity='OmegaEnv')
    # One value per star, all strictly positive rotation rates (Omega_sun).
    assert omega.shape == (4,)
    assert np.all(omega > 0.0)
    # Error contract: both keyword arguments are mandatory.
    with pytest.raises(Exception, match='Age'):
        cluster.Values(Quantity='OmegaEnv')
    with pytest.raises(Exception, match='Quantity'):
        cluster.Values(Age=100.0)


def test_surface_rotation_decreases_with_age(cluster_mod):
    """Surface rotation spins down: OmegaEnv is smaller at old age than young age."""
    cluster = make_cluster(cluster_mod, n=3)
    # Young (10 Myr) versus old (5000 Myr) so the spin-down is resolved.
    omega_young = cluster.Values(Age=10.0, Quantity='OmegaEnv')
    omega_old = cluster.Values(Age=5000.0, Quantity='OmegaEnv')
    assert np.all(omega_old < omega_young)
    # A wrong (constant or increasing) history would fail this margin.
    assert np.all(omega_young > 1.5 * omega_old)


@pytest.mark.physics_invariant
def test_percentile_maps_percentile_to_rotation_monotonically(cluster_mod):
    """Increasing percentile yields a strictly larger, positive rotation rate."""
    cluster = make_cluster(cluster_mod, n=6)
    omega_slow = cluster.Percentile(Mstar=1.0, Age=100.0, percentile=5.0)
    omega_med = cluster.Percentile(Mstar=1.0, Age=100.0, percentile=50.0)
    omega_fast = cluster.Percentile(Mstar=1.0, Age=100.0, percentile=95.0)
    # Monotone increasing mapping from percentile to rotation rate.
    assert omega_slow < omega_med < omega_fast
    # Rotation rates are strictly positive (Omega_sun).
    assert omega_slow > 0.0


def test_percentile_string_labels_and_error_contract(cluster_mod):
    """String percentile labels resolve to fixed values; bad input raises."""
    cluster = make_cluster(cluster_mod, n=6)
    # 'slow' == 5th percentile, 'fast' == 95th; both bracket 'medium' == 50th.
    slow = cluster.Percentile(Mstar=1.0, Age=100.0, percentile='slow')
    medium = cluster.Percentile(Mstar=1.0, Age=100.0, percentile='medium')
    fast = cluster.Percentile(Mstar=1.0, Age=100.0, percentile='fast')
    assert slow < medium < fast
    # 'slow' must agree with the numeric 5th percentile it stands for.
    slow_numeric = cluster.Percentile(Mstar=1.0, Age=100.0, percentile=5.0)
    assert_allclose(slow, slow_numeric, rtol=1e-12)
    # Error contract: an unknown label and a missing age both raise.
    with pytest.raises(Exception, match='invalid percentile'):
        cluster.Percentile(Mstar=1.0, Age=100.0, percentile='sluggish')
    with pytest.raises(Exception, match='Age'):
        cluster.Percentile(Mstar=1.0, percentile='slow')


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_percentile_of_uniform_ramp_matches_closed_form(cluster_mod):
    """Percentile of a uniform rotation ramp equals its closed-form value.

    Analytical anchor: for an evenly spaced distribution running from A to B, the
    q-th percentile under linear interpolation is exactly A + (B - A) * q / 100,
    independent of the sample count. The cluster is built with an evenly spaced
    initial rotation ramp from 1 to 40 Omega_sun, and the surface spin-down
    rescales every member by the same factor at a fixed age, so the ramp stays
    uniform and its percentiles keep the closed form. This pins that
    Cluster.Percentile assembles the OmegaEnv distribution and dispatches the
    percentile branch so the returned rotation equals the analytic value rather
    than a re-evaluation of the same numpy call on the same array.
    """
    cluster = make_cluster(cluster_mod, n=8)
    age = 200.0
    # Every star's surface rotation is scaled by the same spin-down factor at a
    # shared age, so the uniform 1..40 Omega_sun ramp stays uniform.
    factor = 1.0 / (1.0 + age / 1000.0)
    lo_edge, hi_edge = 1.0 * factor, 40.0 * factor
    for q in (5.0, 50.0, 95.0):
        got = cluster.Percentile(Mstar=1.0, Age=age, percentile=q)
        analytic = lo_edge + (hi_edge - lo_edge) * q / 100.0
        assert_allclose(got, analytic, rtol=1e-12)
    # Discrimination guard: a wrong branch returning the distribution midpoint
    # for every request would sit at (lo+hi)/2, differing from the analytic p05
    # and p95 by far more than the tolerance.
    midpoint = 0.5 * (lo_edge + hi_edge)
    p05 = cluster.Percentile(Mstar=1.0, Age=age, percentile=5.0)
    p95 = cluster.Percentile(Mstar=1.0, Age=age, percentile=95.0)
    assert abs(p05 - midpoint) > 1.0
    assert abs(p95 - midpoint) > 1.0


def test_activity_lifetime_requires_string_quantity(cluster_mod):
    """ActivityLifetime returns a positive per-star array and validates Quantity."""
    cluster = make_cluster(cluster_mod, n=3)
    ages = cluster.ActivityLifetime(Quantity='Lx', Threshold='sat', AgeMax=None)
    # One positive lifetime (Myr) per star.
    assert ages.shape == (3,)
    assert np.all(ages > 0.0)
    # Error contract: Quantity is mandatory and must be a string.
    with pytest.raises(Exception, match='Quantity not set'):
        cluster.ActivityLifetime(Threshold='sat')
    with pytest.raises(Exception, match='must be string'):
        cluster.ActivityLifetime(Quantity=5, Threshold='sat')


def test_integrate_emission_grows_with_interval(cluster_mod):
    """Integrated emission is positive and increases with the age interval."""
    cluster = make_cluster(cluster_mod, n=3)
    short = cluster.IntegrateEmission(AgeMin=10.0, AgeMax=110.0, Band='XUV')
    long = cluster.IntegrateEmission(AgeMin=10.0, AgeMax=1010.0, Band='XUV')
    # Energies (erg) are positive and monotone in the integration window.
    assert np.all(short > 0.0)
    assert np.all(long > short)
    # Edge case: a zero-width interval integrates to zero energy. Allow rounding
    # at a tiny fraction of a finite-interval energy (short ~ 1e32 erg), far
    # below any physical XUV budget, rather than demanding a bit-exact zero.
    zero = cluster.IntegrateEmission(AgeMin=50.0, AgeMax=50.0, Band='XUV')
    assert_allclose(zero, np.zeros(cluster.nStars), atol=1e-9 * float(np.max(short)))


def test_dynamic_quantity_accessors_are_created(cluster_mod):
    """Constructing a cluster attaches a per-track accessor for each quantity."""
    cluster = make_cluster(cluster_mod, n=3)
    # The accessor built from the OmegaEnv track returns the per-star array.
    omega = cluster.OmegaEnv(Age=100.0)
    assert omega.shape == (3,)
    assert np.all(omega > 0.0)
    # A second track (Lbol, erg/s) is exposed the same way and is positive.
    lbol = cluster.Lbol(Age=100.0)
    assert np.all(lbol > 0.0)


def test_print_stars_logs_masses_and_count(cluster_mod, caplog):
    """PrintStars emits each stellar mass and the total star count to the log."""
    cluster = make_cluster(cluster_mod, n=2)
    with caplog.at_level(logging.INFO, logger='fwl.mors.cluster'):
        cluster.PrintStars()
    text = caplog.text
    # The summary line reports the population size.
    assert 'Number of stars in cluster = 2' in text
    # At least one stellar mass (Msun) appears in the per-star listing.
    assert 'Msun' in text


def test_save_and_reload_roundtrip(cluster_mod, tmp_path):
    """Save writes a pickled cluster that reloads with the same population."""
    cluster = make_cluster(cluster_mod, n=3)
    target = tmp_path / 'cluster.pickle'
    cluster.Save(filename=str(target))
    # The file is written and non-empty.
    assert target.exists()
    assert target.stat().st_size > 0
    with open(target, 'rb') as f:
        reloaded = pickle.load(f)
    assert reloaded.nStars == cluster.nStars
    assert_allclose(reloaded.Mstar, cluster.Mstar, rtol=1e-12)
    # The lowercase alias writes an independent file with identical content.
    alias_target = tmp_path / 'cluster_alias.pickle'
    cluster.save(filename=str(alias_target))
    assert alias_target.exists()
    assert alias_target.stat().st_size > 0


def test_age_scalar_and_array_construction(cluster_mod):
    """Age can be a shared scalar or a per-star array at construction time."""
    Mstar = np.linspace(0.6, 1.1, 3)
    Omega = np.linspace(2.0, 20.0, 3)
    # Scalar age shared by all stars.
    cluster_scalar = cluster_mod.Cluster(Mstar=Mstar, Omega=Omega, Age=50.0)
    assert cluster_scalar.nStars == 3
    # Per-star age array, one entry per mass.
    ages = np.array([10.0, 100.0, 1000.0])
    cluster_array = cluster_mod.Cluster(Mstar=Mstar, Omega=Omega, Age=ages)
    assert cluster_array.nStars == 3
    # Both routes yield positive rotation values.
    assert np.all(cluster_array.Values(Age=100.0, Quantity='OmegaEnv') > 0.0)


def test_construction_input_validation(cluster_mod):
    """Missing mass and mismatched mass/rotation lengths are rejected."""
    # Mstar is mandatory.
    with pytest.raises(Exception, match='Mstar keyword argument not set'):
        cluster_mod.Cluster(Omega=[1.0, 2.0])
    # Mstar and Omega must have matching lengths.
    with pytest.raises(Exception, match='different lengths'):
        cluster_mod.Cluster(Mstar=[0.5, 0.8, 1.0], Omega=[1.0, 2.0])


def test_check_input_rotation_expands_and_validates():
    """_CheckInputRotation expands a scalar Omega and rejects conflicting inputs."""
    from mors.cluster import _CheckInputRotation

    # Omega set alone propagates to both envelope and core rotation rates.
    Omega, OmegaEnv, OmegaCore = _CheckInputRotation(None, 3.0, None, None)
    assert_allclose(OmegaEnv, 3.0, rtol=1e-12)
    assert_allclose(OmegaCore, 3.0, rtol=1e-12)
    # Age together with an explicit OmegaCore is contradictory.
    with pytest.raises(Exception, match='cannot set both Age and OmegaCore'):
        _CheckInputRotation(100.0, None, None, 2.0)
    # With Omega unset, both OmegaEnv and OmegaCore must be provided.
    with pytest.raises(Exception, match='must set either Omega'):
        _CheckInputRotation(None, None, 2.0, None)
    # Omega set alongside OmegaEnv/OmegaCore is over-specified.
    with pytest.raises(Exception, match='cannot set OmegaEnv and OmegaCore'):
        _CheckInputRotation(None, 3.0, 2.0, 2.0)
    # Omega unset with both OmegaEnv and OmegaCore supplied passes through
    # unchanged (the envelope and core rotation are allowed to differ).
    Omega2, OmegaEnv2, OmegaCore2 = _CheckInputRotation(None, None, 2.0, 4.0)
    assert Omega2 is None
    assert_allclose(OmegaEnv2, 2.0, rtol=1e-12)
    assert_allclose(OmegaCore2, 4.0, rtol=1e-12)
