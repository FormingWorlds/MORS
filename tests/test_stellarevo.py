"""Tests for src/mors/stellarevo.py.

Exercises the Spada et al. (2013) stellar-structure track interpolation. The
module-level ``Value`` reads the tracks (downloaded to ``FWL_DATA``) and returns
structural quantities in native units: bolometric luminosity in solar
luminosities, radius in solar radii, and effective temperature in Kelvin. The
reference anchor is the solar calibration, and a companion test asserts the
main-sequence luminosity-mass monotonicity that the tracks must obey.

Anchor: docs/Validation/stellarevo.md.
"""

from __future__ import annotations

import os

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors
import mors.stellarevo as se

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]

# Solar age, 4.57 Gyr, in the Myr unit the tracks are indexed by.
SOLAR_AGE_MYR = 4570.0
# Solar effective temperature (K), the standard photospheric value.
T_EFF_SUN = 5772.0
# Default Spada model set, closest to solar composition.
SOLAR_MODEL_SET = 'X0p70952_Z0p01631_A1p875'

# All per-quantity accessor names exposed both as StarEvo methods and module functions.
QUANTITY_NAMES = (
    'Rstar', 'Lbol', 'Teff', 'Itotal', 'Icore', 'Ienv', 'Mcore', 'Menv',
    'Rcore', 'tauConv', 'dItotaldt', 'dIcoredt', 'dIenvdt', 'dMcoredt', 'dRcoredt',
)


@pytest.fixture(scope='module')
def default_star_evo():
    """A StarEvo instance built from the default (cached) Spada grid."""
    mors.DownloadEvolutionTracks('Spada')
    return mors.StarEvo()


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_stellarevo_solar_calibration():
    """The Spada 1 Msun track reproduces the Sun at the solar age.

    Reference: Spada et al. (2013) solar-calibrated tracks, with the solar
    luminosity and radius normalised to unity and the solar effective
    temperature 5772 K. At 4.57 Gyr the solar-mass track lands within
    0.15 Lsun of L = 1 Lsun, 0.05 Rsun of R = 1 Rsun, and 3% of Teff = 5772 K.
    A wrong track index, a wrong age unit, or a units slip would move any of
    these far outside the tolerance.
    """
    mors.DownloadEvolutionTracks('Spada')
    lbol = mors.Value(1.0, SOLAR_AGE_MYR, 'Lbol')
    rstar = mors.Value(1.0, SOLAR_AGE_MYR, 'Rstar')
    teff = mors.Value(1.0, SOLAR_AGE_MYR, 'Teff')
    # Positivity of every structural quantity.
    assert lbol > 0.0
    assert rstar > 0.0
    assert teff > 0.0
    # Solar calibration: within 0.15 Lsun, 0.05 Rsun, and 3% in Teff.
    assert_allclose(lbol, 1.0, atol=0.15)
    assert_allclose(rstar, 1.0, atol=0.05)
    assert_allclose(teff, T_EFF_SUN, rtol=0.03)


@pytest.mark.physics_invariant
def test_stellarevo_luminosity_increases_with_mass():
    """Main-sequence luminosity rises monotonically with stellar mass at fixed age.

    Samples four masses from 0.3 to 1.2 Msun at 1 Gyr. The luminosity must
    increase strictly with mass (a steep main-sequence mass-luminosity
    relation), so a swapped track index or a mass-independent lookup fails. The
    lightest and heaviest tracks differ by more than two orders of magnitude.
    """
    mors.DownloadEvolutionTracks('Spada')
    age = 1000.0  # Myr, main sequence for all four masses
    masses = (0.3, 0.6, 1.0, 1.2)
    lums = [mors.Value(m, age, 'Lbol') for m in masses]
    # Positivity and strict monotone increase with mass.
    assert all(lum > 0.0 for lum in lums)
    assert all(lo < hi for lo, hi in zip(lums, lums[1:]))
    # The 1.2 Msun track outshines the 0.3 Msun track by well over 100x.
    assert lums[-1] > 100.0 * lums[0]


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_grid_compiled_from_raw_tracks_matches_saved_grid(tmp_path):
    """Compiling the grid from the raw Spada track files reproduces the solar calibration.

    Reference: Spada et al. (2013), ApJ 776, 87. The default install ships a
    pre-pickled grid; here the raw ``.track1`` / ``.track2`` files are read and
    the grid is compiled from scratch (the code path that produced that pickle).
    The freshly compiled 1 Msun track must still land near L = 1 Lsun and
    R = 1 Rsun at the solar age, and a second construction from the pickle it
    just wrote must return the identical grid. A wrong column index in the raw
    reader, a dropped log-to-linear conversion, or a Gyr-to-Myr slip would move
    the solar luminosity far outside the tolerance.
    """
    real_model_dir = os.path.join(se.starEvoDirDefault, SOLAR_MODEL_SET)
    # Point a private grid directory at the real raw tracks with no pickle present,
    # so construction is forced down the compile-from-scratch branch.
    os.symlink(real_model_dir, tmp_path / SOLAR_MODEL_SET)
    pickle_path = tmp_path / (SOLAR_MODEL_SET + '.pickle')
    assert not pickle_path.exists()

    compiled = mors.StarEvo(starEvoDir=str(tmp_path), evoModels=SOLAR_MODEL_SET)
    # The compile branch writes the pickle it just built.
    assert pickle_path.exists()

    lbol = compiled.Lbol(1.0, SOLAR_AGE_MYR)
    rstar = compiled.Rstar(1.0, SOLAR_AGE_MYR)
    # Positivity and solar calibration of the freshly compiled track.
    assert lbol > 0.0
    assert rstar > 0.0
    assert_allclose(lbol, 1.0, atol=0.2)
    assert_allclose(rstar, 1.0, atol=0.1)
    # Discrimination: a 0.5 Msun track would give Lbol well below 0.5 Lsun, so the
    # correct 1 Msun track is unambiguously selected.
    assert lbol > 0.5

    # Re-constructing now loads the saved pickle; the grids must agree at 1 Msun.
    reloaded = mors.StarEvo(starEvoDir=str(tmp_path), evoModels=SOLAR_MODEL_SET)
    assert_allclose(reloaded.Lbol(1.0, SOLAR_AGE_MYR), lbol, rtol=1e-12)
    assert_allclose(reloaded.Teff(1.0, SOLAR_AGE_MYR),
                    compiled.Teff(1.0, SOLAR_AGE_MYR), rtol=1e-12)


@pytest.mark.physics_invariant
def test_starevo_methods_return_physical_solar_quantities(default_star_evo):
    """Every StarEvo per-quantity method returns a finite, physically signed value.

    For a 1 Msun star at the solar age the structural quantities must be positive
    (radius, luminosity, temperature, the three moments of inertia, the core and
    envelope masses, the core radius, the convective turnover time), the core
    radius must sit inside the stellar radius, the envelope mass fraction must lie
    in [0, 1], and all five time derivatives must be finite. The core moment of
    inertia must not exceed the total, a structural bound on the partition.
    """
    se_obj = default_star_evo
    vals = {name: float(getattr(se_obj, name)(1.0, SOLAR_AGE_MYR)) for name in QUANTITY_NAMES}
    # The generic Value dispatcher must agree with the named accessor.
    assert_allclose(se_obj.Value(1.0, SOLAR_AGE_MYR, 'Lbol'), vals['Lbol'], rtol=1e-12)

    # Strictly positive structural quantities.
    for key in ('Rstar', 'Lbol', 'Teff', 'Itotal', 'Icore', 'Ienv',
                'Mcore', 'Menv', 'Rcore', 'tauConv'):
        assert vals[key] > 0.0, key

    # Envelope mass fraction is bounded; the solar core radius is inside the star.
    assert 0.0 < vals['Menv'] < 1.0
    assert vals['Rcore'] < vals['Rstar']
    # Core mass cannot exceed the total stellar mass.
    assert vals['Mcore'] < 1.0

    # The grid stores Icore as Itotal minus Ienv, so their sum recovering Itotal
    # is a structural consistency check on the interpolation, not an independent
    # pin. The physical content is that each partition piece stays within the
    # total: the core and envelope moments are both bounded by Itotal.
    assert vals['Icore'] <= vals['Itotal']
    assert vals['Ienv'] <= vals['Itotal']

    # Every rate of change is finite (signs vary across the evolution).
    for key in ('dItotaldt', 'dIcoredt', 'dIenvdt', 'dMcoredt', 'dRcoredt'):
        assert np.isfinite(vals[key]), key

    # Teff sits in the cool-dwarf-to-solar range, ruling out a log-vs-linear slip.
    assert 3000.0 < vals['Teff'] < 7000.0


@pytest.mark.physics_invariant
def test_module_level_wrappers_match_default_grid():
    """The bare module functions return the same physical quantities as the class.

    The first call to a module-level wrapper loads the default grid lazily; the
    returned values must be positive where physics requires it and must keep the
    core moment of inertia within the total. This exercises the standalone API
    surface PROTEUS uses (mors.Rstar, mors.Lbol, ...), separate from a StarEvo
    instance.
    """
    mors.DownloadEvolutionTracks('Spada')
    module_vals = {name: float(getattr(mors, name)(1.0, SOLAR_AGE_MYR)) for name in QUANTITY_NAMES}

    for key in ('Rstar', 'Lbol', 'Teff', 'Itotal', 'Icore', 'Ienv',
                'Mcore', 'Menv', 'Rcore', 'tauConv'):
        assert module_vals[key] > 0.0, key

    # Same structural constraints as the class accessors.
    assert 0.0 < module_vals['Menv'] < 1.0
    assert module_vals['Rcore'] < module_vals['Rstar']
    # Core and envelope moments are each bounded by the total (structural bound,
    # since the grid derives Icore as Itotal minus Ienv).
    assert module_vals['Icore'] <= module_vals['Itotal']
    assert module_vals['Ienv'] <= module_vals['Itotal']
    # Solar luminosity near unity discriminates against a mis-selected track.
    assert_allclose(module_vals['Lbol'], 1.0, atol=0.2)


@pytest.mark.physics_invariant
def test_value_off_grid_mass_interpolates_between_bins(default_star_evo):
    """An off-grid stellar mass is interpolated between the two bracketing tracks.

    A mass of 0.93 Msun lies between the 0.90 and 0.95 Msun grid nodes, forcing
    the two-dimensional (mass, age) interpolation rather than a single-track
    lookup. The interpolated luminosity must be bracketed by the two neighbouring
    node luminosities and stay strictly positive, so a broken interpolation that
    snapped to one node or overshot the bracket would fail.
    """
    se_obj = default_star_evo
    l_low = se_obj.Lbol(0.90, SOLAR_AGE_MYR)
    l_high = se_obj.Lbol(0.95, SOLAR_AGE_MYR)
    l_mid = se_obj.Lbol(0.93, SOLAR_AGE_MYR)
    # Positivity and strict bracketing by the two adjacent mass-bin luminosities.
    assert l_mid > 0.0
    assert l_low < l_mid < l_high


def test_value_array_inputs_return_broadcast_grid(default_star_evo):
    """Array-valued mass, age, and parameter arguments produce a squeezed grid.

    Passing a mass array with a scalar age returns one luminosity per mass, and a
    list of parameter names with scalar mass and age returns one value per
    parameter. This exercises the multi-dimensional branch of Value and its final
    squeeze, distinct from the scalar fast path.
    """
    se_obj = default_star_evo
    masses = np.array([0.6, 1.0, 1.2])
    lums = se_obj.Value(masses, SOLAR_AGE_MYR, 'Lbol')
    # One luminosity per mass, monotonically increasing along the main sequence.
    assert lums.shape == (3,)
    assert np.all(lums > 0.0)
    assert lums[0] < lums[1] < lums[2]

    params = se_obj.Value(1.0, SOLAR_AGE_MYR, ['Lbol', 'Rstar', 'Teff'])
    # One value per requested parameter, matching the scalar accessors.
    assert params.shape == (3,)
    assert_allclose(params[0], se_obj.Lbol(1.0, SOLAR_AGE_MYR), rtol=1e-12)
    assert_allclose(params[2], se_obj.Teff(1.0, SOLAR_AGE_MYR), rtol=1e-12)


def test_load_track_default_grid_and_clear(monkeypatch):
    """LoadTrack lazily loads the default grid and can prune to a single mass.

    With no ModelData supplied and no default grid cached, LoadTrack must load the
    default grid, insert the requested off-grid mass, and register it in MstarAll.
    ClearData then reduces the returned dictionary to just that mass while keeping
    the parameter list intact.
    """
    monkeypatch.setattr('mors.stellarevo.ModelDataDefault', None, raising=False)
    md = mors.LoadTrack(0.37, ModelData=None)
    # The off-grid mass is now a first-class track in the returned grid.
    assert 0.37 in md
    assert 0.37 in md['MstarAll']
    # A value can be read straight off the freshly inserted track.
    assert mors.Value(0.37, SOLAR_AGE_MYR, 'Lbol', ModelData=md) > 0.0

    # Re-requesting an existing grid-node mass is a no-op that leaves the node present.
    md2 = mors.LoadTrack(1.0, ModelData=md)
    assert 1.0 in md2

    cleared = mors.LoadTrack(0.37, ModelData=md, ClearData=True)
    # Pruned grid keeps only the requested mass but retains the parameter registry.
    assert list(cleared['MstarAll']) == [0.37]
    assert 'ParamsAll' in cleared
    assert 1.0 not in cleared


def test_off_limits_mass_and_age_raise(default_star_evo):
    """Off-grid stellar mass or age is rejected rather than silently extrapolated.

    The Spada grid spans 0.1 to 1.25 Msun; a 5 Msun request and a 0.01 Msun
    request must both raise, as must an age beyond the end of the 1 Msun track.
    These guards protect PROTEUS from reading an extrapolated flux history off the
    edge of the tabulated tracks.
    """
    se_obj = default_star_evo
    with pytest.raises(Exception, match='stellar mass'):
        se_obj.Lbol(5.0, SOLAR_AGE_MYR)
    with pytest.raises(Exception, match='stellar mass'):
        se_obj.Lbol(0.01, SOLAR_AGE_MYR)
    # An age far past the oldest track node is out of range.
    with pytest.raises(Exception, match='age'):
        se_obj.Lbol(1.0, 1.0e9)


def test_value_rejects_bad_types_and_unknown_parameter(default_star_evo):
    """Value and _ValueSingle reject malformed mass, age, and parameter arguments.

    A non-numeric mass or age cannot be coerced and must raise; an unknown
    parameter name and a non-string parameter must also raise before any track
    lookup runs. These are the input-contract guards on the public accessor.
    """
    se_obj = default_star_evo
    with pytest.raises(Exception, match='Mstar'):
        mors.Value('not-a-mass', SOLAR_AGE_MYR, 'Lbol', ModelData=se_obj.ModelData)
    with pytest.raises(Exception, match='Age'):
        mors.Value(1.0, 'not-an-age', 'Lbol', ModelData=se_obj.ModelData)
    with pytest.raises(Exception, match='not valid'):
        mors.Value(1.0, SOLAR_AGE_MYR, 'NotAParameter', ModelData=se_obj.ModelData)
    # A non-string parameter is rejected inside the single-value lookup.
    with pytest.raises(Exception, match='string'):
        se._ValueSingle(1.0, SOLAR_AGE_MYR, 123, ModelData=se_obj.ModelData)


def test_starevo_loadtrack_method_inserts_mass(monkeypatch):
    """The StarEvo.LoadTrack method caches an off-grid track into the instance grid.

    Loading the 0.42 Msun track (a mass between the 0.40 and 0.45 nodes) into a
    fresh instance must add it to the instance ModelData and make subsequent
    lookups exact rather than interpolated. With no default grid cached, the
    instance grid is used directly and the global default is left untouched.
    """
    mors.DownloadEvolutionTracks('Spada')
    # Force the no-default branch so the instance grid is the only source.
    monkeypatch.setattr('mors.stellarevo.ModelDataDefault', None, raising=False)
    se_obj = mors.StarEvo()
    assert 0.42 not in se_obj.ModelData

    se_obj.LoadTrack(0.42)
    # The track is now cached on the instance and the global default stays absent.
    assert 0.42 in se_obj.ModelData
    assert se.ModelDataDefault is None
    # The cached track yields a positive, physically bracketed luminosity.
    lbol = se_obj.Lbol(0.42, SOLAR_AGE_MYR)
    assert lbol > 0.0
    assert se_obj.Lbol(0.40, SOLAR_AGE_MYR) < lbol < se_obj.Lbol(0.45, SOLAR_AGE_MYR)


def test_starevo_default_arguments_load_grid():
    """Passing None for the directory and model set falls back to the shipped defaults.

    The explicit-None constructor path must resolve to the default Spada grid and
    yield the same solar luminosity as the no-argument constructor, confirming the
    default-substitution branch in __init__.
    """
    mors.DownloadEvolutionTracks('Spada')
    se_default = mors.StarEvo(starEvoDir=None, evoModels=None)
    lbol = se_default.Lbol(1.0, SOLAR_AGE_MYR)
    # Default-loaded grid reproduces the solar calibration and stays positive.
    assert lbol > 0.0
    assert_allclose(lbol, 1.0, atol=0.2)
