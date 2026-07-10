"""Tests for src/mors/star.py.

Exercises the coupled rotation + activity ``Star`` model. ``Star.Value`` returns
stellar structure in cgs units (bolometric and high-energy luminosities in
erg/s, radius in solar radii) for a given age. The reference anchor is the solar
calibration: a 1 Msun star at the solar age reproduces the nominal solar
luminosity, which validates both the Spada et al. (2013) track calibration and
the Lsun-to-erg/s unit conversion inside the ``Star`` class. Companion tests pin
the model output for both time-integration methods and assert positivity.

Anchor: docs/Validation/star.md.
"""

from __future__ import annotations

import pickle

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors
from mors import star as star_mod
from mors.parameters import paramsDefault

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]

# IAU 2015 Resolution B3 nominal solar luminosity, in cgs (erg/s).
L_SUN_CGS = 3.828e33
# Solar age, 4.57 Gyr, in the Myr unit the tracks are indexed by.
SOLAR_AGE_MYR = 4570.0

# (Mstar [Msun], Omega [Omega_sun], age [Myr]) -> (Rstar [Rsun], Lbol [erg/s],
# Leuv [erg/s]) from Star.Value, pinned per time-integration method. The
# structure (Rstar, Lbol) agrees across methods; the activity (Leuv) differs
# because it depends on the rotation history the integrator produces.
SPADA_DEFAULT = (
    ((0.128, 45.2, 8.5e1), (0.21264087, 1.68629162e31, 1.74475018e28)),
    ((1.113, 17.7, 3.2e3), (1.16581971, 6.81767904e33, 7.94621466e28)),
    ((0.995, 1.005, 1.0e4), (1.48910765e00, 7.80659378e33, 3.16581356e28)),
    ((1.000, 1.00, 1.0e4), (1.52588718e00, 8.13197065e33, 3.29155751e28)),
)
SPADA_FORWARD_EULER = (
    ((0.128, 45.2, 8.5e1), (0.21263373, 1.68612614e31, 1.73275380e28)),
    ((1.113, 17.7, 3.2e3), (1.16581827, 6.81769926e33, 7.94292986e28)),
    ((0.995, 1.005, 1.0e4), (1.48904952e00, 7.80667546e33, 3.22933432e28)),
    ((1.000, 1.00, 1.0e4), (1.52583342e00, 8.13191736e33, 3.38245392e28)),
)


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_star_reproduces_solar_luminosity_at_solar_age():
    """A 1 Msun star at the solar age reproduces the nominal solar luminosity.

    Reference: Spada et al. (2013) solar-calibrated tracks with the IAU 2015 B3
    nominal solar luminosity, L_sun = 3.828e33 erg/s. Star.Value returns the
    bolometric luminosity in erg/s; the solar-mass track at 4.57 Gyr lands
    within 15% of L_sun, which pins both the track calibration and the internal
    Lsun-to-erg/s conversion. The 0.3 Msun discrimination guard, more than a
    factor of ten fainter, rules out a wrong-mass track slipping through.
    """
    mors.DownloadEvolutionTracks('Spada')
    lbol = mors.Star(Mstar=1.0, Omega=1.0).Value(SOLAR_AGE_MYR, 'Lbol')
    assert lbol > 0.0
    # rtol=0.15: the Spada solar-mass track reproduces L_sun to within 15%.
    assert_allclose(lbol, L_SUN_CGS, rtol=0.15)
    # Discrimination: a 0.3 Msun main-sequence star is more than 10x fainter.
    faint = mors.Star(Mstar=0.3, Omega=1.0).Value(SOLAR_AGE_MYR, 'Lbol')
    assert faint < 0.1 * lbol


@pytest.mark.physics_invariant
@pytest.mark.parametrize('inp,expected', SPADA_DEFAULT)
def test_star_value_default_integrator(inp, expected):
    """Pin Star.Value (default integrator) against the Spada track model.

    The pinned numbers are a regression guard on the interpolation of the Spada
    et al. (2013) fs255 grid: they lock the coupled rotation + structure model
    to its own tabulated radius, bolometric luminosity, and EUV luminosity, and
    check that all three are strictly positive. The four masses span brown-dwarf
    to solar-type stars.
    """
    mors.DownloadEvolutionTracks('Spada')
    star = mors.Star(Mstar=inp[0], Omega=inp[1])
    ret = (
        star.Value(inp[2], 'Rstar'),
        star.Value(inp[2], 'Lbol'),
        star.Value(inp[2], 'Leuv'),
    )
    # Radius, bolometric, and EUV luminosity are all strictly positive.
    assert all(x > 0.0 for x in ret)
    # rtol=1e-6 tracks the precision of the pinned reference values.
    assert_allclose(ret, expected, rtol=1e-6, atol=0)


@pytest.mark.physics_invariant
@pytest.mark.parametrize('inp,expected', SPADA_FORWARD_EULER)
def test_star_value_forward_euler_integrator(inp, expected):
    """Pin Star.Value (forward-Euler integrator) against the Spada track model.

    The pinned numbers are a regression guard on the interpolation of the Spada
    et al. (2013) fs255 grid under forward-Euler rotation integration. That
    history yields the same structure but a slightly different activity than the
    default integrator, so the EUV luminosity is pinned to its own tabulated
    value. Positivity of every returned quantity is asserted alongside the pin.
    """
    mors.DownloadEvolutionTracks('Spada')
    params = mors.NewParams()
    params['TimeIntegrationMethod'] = 'ForwardEuler'
    star = mors.Star(Mstar=inp[0], Omega=inp[1], params=params)
    ret = (
        star.Value(inp[2], 'Rstar'),
        star.Value(inp[2], 'Lbol'),
        star.Value(inp[2], 'Leuv'),
    )
    assert all(x > 0.0 for x in ret)
    assert_allclose(ret, expected, rtol=1e-6, atol=0)


# Every quantity that has an evolutionary track, in the order the class installs
# the getter methods. Two of them ('Mstar', 'nAge') are stored as scalars rather
# than time series, so their getter raises when the 1D interpolator indexes them.
SCALAR_TRACK_GETTERS = ('Mstar', 'nAge')
ARRAY_TRACK_GETTERS = (
    'Age', 'dAge', 'OmegaEnv', 'OmegaCore', 'Prot', 'Rstar', 'tauConv', 'Ro',
    'Itotal', 'Ienv', 'Icore', 'dItotaldt', 'dIenvdt', 'dIcoredt', 'Rcore',
    'dMcoredt', 'Mdot', 'Bdip', 'vEsc', 'torqueEnvMom', 'torqueCoreMom',
    'torqueEnvCG', 'torqueCoreCG', 'torqueEnvWind', 'torqueEnvCE', 'torqueCoreCE',
    'torqueEnvDL', 'torqueEnv', 'dOmegaEnvdt', 'torqueCore', 'dOmegaCoredt',
    'Lbol', 'Teff', 'Lx', 'Fx', 'Rx', 'Tcor', 'Leuv1', 'Feuv1', 'Reuv1',
    'Leuv2', 'Feuv2', 'Reuv2', 'Leuv', 'Feuv', 'Reuv', 'Lly', 'Fly', 'Rly',
    'FxHZ', 'Feuv1HZ', 'Feuv2HZ', 'FeuvHZ', 'FlyHZ',
)
# Quantities that are strictly positive by physical construction at every age: a
# whole-star radius, temperature, rotation rate, or an emitted power can never be
# zero or negative for an active star.
STRICTLY_POSITIVE_GETTERS = (
    'Age', 'OmegaEnv', 'OmegaCore', 'Prot', 'Rstar', 'tauConv', 'Ro', 'Itotal',
    'Ienv', 'vEsc', 'Bdip', 'Lbol', 'Teff', 'Lx', 'Fx', 'Rx',
    'Leuv1', 'Feuv1', 'Leuv2', 'Feuv2', 'Leuv', 'Feuv', 'Lly', 'Fly',
)
# The radiative core has not formed at 1 Myr (the star is fully convective), so
# its moment of inertia and radius start at zero and grow positive as the star
# settles onto the main sequence.
CORE_GROWTH_GETTERS = ('Icore', 'Rcore')


@pytest.fixture(scope='module')
def solar_star():
    """A single solar-calibrated star (1 Msun, Omega = 1 Omega_sun) shared across
    the method-surface tests so the real Spada evolution runs only once."""
    mors.DownloadEvolutionTracks('Spada')
    return mors.Star(Mstar=1.0, Omega=1.0)


@pytest.mark.physics_invariant
def test_all_quantity_getters_return_finite_positive_values(solar_star):
    """Every installed quantity getter returns a finite value at two ages, and the
    structural / emission quantities stay strictly positive.

    The ``Star`` class installs one accessor per tracked quantity that forwards to
    ``Value``. This exercises the whole dispatch surface at the youngest track node
    (1 Myr, a boundary age) and at an intermediate main-sequence age, checking
    that none of the ~55 quantities returns a NaN or infinity and that radii,
    moments of inertia, temperature, rotation, and emitted powers remain positive.
    """
    # 1.0 Myr is the youngest node on the track (boundary); 1000 Myr is interior.
    for age in (solar_star.AgeMin, 1000.0):
        values = {}
        for name in ARRAY_TRACK_GETTERS:
            getter = getattr(type(solar_star), name)
            values[name] = getter(solar_star, age)
        assert all(np.isfinite(v) for v in values.values())
        # Structural and emission quantities cannot be zero or negative.
        assert all(values[name] > 0.0 for name in STRICTLY_POSITIVE_GETTERS)
        # The radiative core is non-negative at every age.
        assert all(values[name] >= 0.0 for name in CORE_GROWTH_GETTERS)
        # A discriminating scale guard: a solar Lbol is ~4-7e33 erg/s (cgs),
        # never the ~1e27 W it would be if the SI-vs-cgs conversion were dropped.
        assert 1.0e33 < values['Lbol'] < 1.0e34
        # Effective temperature of a Sun-like star sits near 4500-6000 K over
        # this age range (cooler and inflated at 1 Myr, hotter on the MS).
        assert 4000.0 < values['Teff'] < 7000.0
    # The core has formed and grown strictly positive by the main-sequence age,
    # having started at zero for the fully-convective 1 Myr star.
    icore_young = getattr(type(solar_star), 'Icore')(solar_star, solar_star.AgeMin)
    icore_ms = getattr(type(solar_star), 'Icore')(solar_star, 1000.0)
    assert icore_young == pytest.approx(0.0, abs=1e40)
    assert icore_ms > 1.0e50


def test_scalar_track_getters_raise_on_interpolation(solar_star):
    """The getters for the scalar-valued tracks refuse to interpolate.

    ``Mstar`` and ``nAge`` are stored as single scalars, not time series, so the
    1D interpolator inside ``Value`` cannot index them; the accessor surfaces a
    ``TypeError`` rather than fabricating a number. This pins that contract for
    both scalar quantities.
    """
    for name in SCALAR_TRACK_GETTERS:
        # The stored track is a single scalar, which is why interpolation fails.
        assert np.ndim(solar_star.Tracks[name]) == 0
        getter = getattr(type(solar_star), name)
        with pytest.raises(TypeError):
            getter(solar_star, 100.0)


def test_track_returns_series_and_rejects_bad_quantities(solar_star):
    """``Track`` returns the raw time series for a valid quantity and validates input.

    A valid key yields the full evolutionary array (same length as the age track,
    strictly positive for a luminosity). Missing, non-string, and unknown keys
    each raise, so a caller cannot silently receive a wrong or absent track.
    """
    lbol = solar_star.Track('Lbol')
    assert len(lbol) == len(solar_star.AgeTrack)
    assert np.all(lbol > 0.0)
    with pytest.raises(Exception, match='not set'):
        solar_star.Track(None)
    with pytest.raises(Exception, match='must be string'):
        solar_star.Track(123)
    with pytest.raises(Exception, match='no available track'):
        solar_star.Track('NotAQuantity')


def test_print_available_tracks_lists_quantities(solar_star, caplog):
    """``PrintAvailableTracks`` logs the header and the tracked quantities with units.

    The listing is the human-facing inventory of what a star exposes; it must name
    at least the bolometric luminosity and carry the section header.
    """
    import logging

    with caplog.at_level(logging.INFO, logger='fwl.mors.star'):
        solar_star.PrintAvailableTracks()
    text = caplog.text
    assert 'EVOLUTIONARY TRACKS AVAILABLE FOR' in text
    assert 'Lbol' in text
    # A quantity carrying a unit is annotated with it in parentheses; the radius
    # is listed in solar radii, so its parenthesised unit appears verbatim.
    assert 'Rstar (Rsun)' in text


def test_save_and_reload_roundtrip(solar_star, tmp_path):
    """Both ``Save`` and its ``save`` alias pickle a star that reloads faithfully.

    A persisted star must reproduce its mass and its interpolated luminosity after
    a round trip through disk, so cached runs stay bit-consistent.
    """
    path_upper = tmp_path / 'star_upper.pickle'
    path_lower = tmp_path / 'star_lower.pickle'
    solar_star.Save(filename=str(path_upper))
    solar_star.save(filename=str(path_lower))
    assert path_upper.exists() and path_lower.exists()
    with open(str(path_upper), 'rb') as f:
        reloaded = pickle.load(f)
    assert reloaded.Mstar == pytest.approx(solar_star.Mstar, rel=1e-12)
    assert_allclose(
        reloaded.Value(2000.0, 'Lbol'),
        solar_star.Value(2000.0, 'Lbol'),
        rtol=1e-12,
    )


@pytest.mark.physics_invariant
def test_activity_lifetime_decreases_with_threshold(solar_star):
    """Activity lifetime shortens as the emission threshold rises.

    ``ActivityLifetime`` reports the last age at which a band drops below a level.
    A higher X-ray threshold is crossed earlier, so the returned lifetime must be
    monotonically non-increasing in the threshold; the saturation-normalised call
    exercises the ``'sat'`` branch and must return a positive age.
    """
    life_low = solar_star.ActivityLifetime(Quantity='Lx', Threshold=1.0e27)
    life_high = solar_star.ActivityLifetime(Quantity='Lx', Threshold=1.0e29)
    assert life_low > 0.0 and life_high > 0.0
    # A brighter cutoff is reached sooner: the star stays above 1e27 longer.
    assert life_low >= life_high
    life_sat = solar_star.ActivityLifetime(Quantity='Lx', Threshold='sat')
    assert life_sat > 0.0
    # AgeMax caps the search window; the answer cannot exceed the cap.
    life_capped = solar_star.ActivityLifetime(
        Quantity='Lx', Threshold=1.0e27, AgeMax=500.0
    )
    assert life_capped <= 500.0 + 1.0e-6


def test_activity_lifetime_validates_quantity(solar_star):
    """``ActivityLifetime`` rejects a missing, non-string, or unlisted quantity.

    Only the enumerated activity bands are integrable; anything else raises before
    a spurious lifetime is computed.
    """
    with pytest.raises(Exception, match='not set'):
        solar_star.ActivityLifetime(Quantity=None, Threshold=1.0e28)
    with pytest.raises(Exception, match='must be string'):
        solar_star.ActivityLifetime(Quantity=42, Threshold=1.0e28)
    with pytest.raises(Exception, match='invalid quantity'):
        solar_star.ActivityLifetime(Quantity='Lbol', Threshold=1.0e28)


@pytest.mark.physics_invariant
def test_integrated_emission_bands_are_additive(solar_star):
    """Integrated XUV energy equals the sum of its X-ray and EUV sub-bands.

    The bolometric bands partition the emitted energy: XUV is X-ray plus EUV, and
    EUV is the sum of its two sub-bands. Integrating each band between the same two
    ages must respect that additive budget, which pins the band-dispatch mapping.
    """
    kw = dict(AgeMin=100.0, AgeMax=1000.0)
    e_xuv = solar_star.IntegrateEmission(Band='XUV', **kw)
    e_xray = solar_star.IntegrateEmission(Band='Xray', **kw)
    e_euv = solar_star.IntegrateEmission(Band='EUV', **kw)
    e_euv1 = solar_star.IntegrateEmission(Band='EUV1', **kw)
    e_euv2 = solar_star.IntegrateEmission(Band='EUV2', **kw)
    e_bol = solar_star.IntegrateEmission(Band='bol', **kw)
    e_lyman = solar_star.IntegrateEmission(Band='Lyman', **kw)
    assert e_xray > 0.0 and e_euv > 0.0 and e_lyman > 0.0
    # Conservation: XUV is exactly X-ray plus EUV (the tracks add before the
    # integral), so the closure holds to interpolation precision.
    assert_allclose(e_xuv, e_xray + e_euv, rtol=1e-9)
    # And EUV is the sum of its two sub-bands.
    assert_allclose(e_euv, e_euv1 + e_euv2, rtol=1e-9)
    # The bolometric energy dwarfs the high-energy tail by orders of magnitude.
    assert e_bol > 100.0 * e_xuv


@pytest.mark.physics_invariant
def test_integrated_emission_orbital_distance(solar_star):
    """A fluence at an orbital distance is the luminosity budget spread over 4 pi r^2.

    Supplying ``aOrb`` as a number or as a habitable-zone label converts the
    integrated luminosity (erg) into a fluence (erg/cm^2); both are positive and
    the closer 1 AU point receives a larger fluence than the more distant HZ edge.
    """
    kw = dict(AgeMin=100.0, AgeMax=1000.0, Band='XUV')
    energy = solar_star.IntegrateEmission(**kw)
    fluence_1au = solar_star.IntegrateEmission(aOrb=1.0, **kw)
    fluence_hz = solar_star.IntegrateEmission(aOrb='HZ', **kw)
    assert fluence_1au > 0.0 and fluence_hz > 0.0
    # A fluence (erg/cm^2) is the luminosity budget divided by 4 pi r^2, so it is
    # far below the raw integrated energy (erg) for any astronomical distance.
    assert fluence_1au < energy
    # The runaway-greenhouse HZ of the Sun lies beyond 1 AU, so its edge receives
    # less XUV than the 1 AU point.
    assert fluence_hz < fluence_1au


def test_integrated_emission_validates_band_and_orbit(solar_star):
    """``IntegrateEmission`` rejects a missing, non-string, or unknown band and orbit.

    The band and the habitable-zone label are both validated against fixed option
    lists before any integral runs, so a typo cannot silently return the wrong
    band's energy.
    """
    with pytest.raises(Exception, match='not set'):
        solar_star.IntegrateEmission(AgeMin=100.0, AgeMax=1000.0, Band=None)
    with pytest.raises(Exception, match='must be string'):
        solar_star.IntegrateEmission(AgeMin=100.0, AgeMax=1000.0, Band=7)
    with pytest.raises(Exception, match='invalid Band'):
        solar_star.IntegrateEmission(AgeMin=100.0, AgeMax=1000.0, Band='Gamma')
    with pytest.raises(Exception, match='invalid aOrb'):
        solar_star.IntegrateEmission(
            AgeMin=100.0, AgeMax=1000.0, Band='XUV', aOrb='NoSuchZone'
        )


@pytest.mark.physics_invariant
def test_star_from_age_fits_initial_rotation():
    """Seeding a star by (Age, OmegaEnv) recovers that rotation rate at that age.

    When ``Age`` is given, the constructor fits the initial rotation so the track
    passes through the specified envelope rate. Reading the envelope rotation back
    at the seed age must reproduce the input to close tolerance, and the resulting
    luminosity stays physical.
    """
    mors.DownloadEvolutionTracks('Spada')
    star = mors.Star(Mstar=1.0, Age=100.0, OmegaEnv=1.0)
    omega_at_seed = star.Value(100.0, 'OmegaEnv')
    # The fitted track passes through OmegaEnv = 1 at Age = 100 Myr.
    assert_allclose(omega_at_seed, 1.0, rtol=1e-3)
    assert star.Value(4570.0, 'Lbol') > 0.0


def test_star_from_age_rejects_unreachable_rotation():
    """A seed rotation outside the reachable range for the mass and age raises.

    The initial-rotation fitter distinguishes a request that is below every
    attainable track from one above every track, and reports each with its own
    message rather than returning a nonsensical spin history.
    """
    mors.DownloadEvolutionTracks('Spada')
    with pytest.raises(Exception, match='too low'):
        mors.Star(Mstar=1.0, Age=1000.0, OmegaEnv=1.0e-6)
    with pytest.raises(Exception, match='too high'):
        mors.Star(Mstar=1.0, Age=1000.0, OmegaEnv=1.0e6)


@pytest.mark.physics_invariant
@pytest.mark.parametrize(
    'kwargs',
    [
        {'Prot': 10.0},
        {'percentile': 'medium'},
        {'OmegaEnv': 1.0, 'OmegaCore': 1.0},
    ],
    ids=['from-rotation-period', 'from-percentile-string', 'from-env-and-core'],
)
def test_star_alternative_rotation_specifications(kwargs):
    """A star can be seeded by period, by distribution percentile, or by env+core.

    Each entry point resolves to a valid initial rotation and yields a positive
    bolometric luminosity and radius at the solar age; the percentile of the
    resulting track is a well-defined fraction in [0, 100].
    """
    mors.DownloadEvolutionTracks('Spada')
    star = mors.Star(Mstar=1.0, **kwargs)
    assert star.Value(4570.0, 'Lbol') > 0.0
    assert star.Value(4570.0, 'Rstar') > 0.0
    assert 0.0 <= star.percentile <= 100.0


def test_check_input_mstar_enforces_grid_bounds():
    """``_CheckInputMstar`` accepts an on-grid mass and rejects the out-of-range ones.

    The evolutionary grid is only defined between the low- and high-mass limits, so
    a missing, too-small, or too-large mass must each raise a distinct message
    before any track is loaded; a valid mass returns without error.
    """
    assert star_mod._CheckInputMstar(1.0) is None
    with pytest.raises(Exception, match='not given'):
        star_mod._CheckInputMstar(None)
    with pytest.raises(Exception, match='less than lower limit'):
        star_mod._CheckInputMstar(0.05)
    with pytest.raises(Exception, match='greater than upper limit'):
        star_mod._CheckInputMstar(2.0)


def _input_rotation(**overrides):
    """Call ``_InputRotation`` with all-None defaults, overriding named arguments."""
    base = dict(
        Mstar=1.0, Age=None, Omega=None, OmegaEnv=None, OmegaCore=None,
        Prot=None, percentile=None, params=dict(paramsDefault),
    )
    base.update(overrides)
    return star_mod._InputRotation(**base)


@pytest.mark.parametrize(
    'overrides,match',
    [
        ({'percentile': 50.0, 'Omega': 1.0}, 'percentile and Omega'),
        ({'percentile': 50.0, 'OmegaEnv': 1.0}, 'percentile and OmegaEnv'),
        ({'percentile': 50.0, 'OmegaCore': 1.0}, 'percentile and OmegaCore'),
        ({'percentile': 50.0, 'Prot': 10.0}, 'percentile and Prot'),
        ({'percentile': 'unknown'}, 'invalid percentile string'),
        ({'Age': 100.0, 'OmegaCore': 1.0}, 'both Age and OmegaCore'),
        ({'Omega': 1.0, 'Prot': 10.0}, 'both Omega and Prot'),
        ({'Age': 100.0}, 'if Age is set'),
        ({}, 'must set either Omega'),
        ({'Omega': 1.0, 'OmegaEnv': 1.0}, 'cannot set OmegaEnv and OmegaCore'),
    ],
    ids=[
        'pct-and-omega', 'pct-and-omegaenv', 'pct-and-omegacore', 'pct-and-prot',
        'bad-percentile-string', 'age-and-omegacore', 'omega-and-prot',
        'age-without-omegaenv', 'nothing-set', 'omega-with-envcore',
    ],
)
def test_input_rotation_rejects_conflicting_arguments(overrides, match):
    """``_InputRotation`` rejects every mutually-exclusive rotation specification.

    The constructor forbids setting a percentile together with an explicit rotation,
    an age together with a core rate, two rotation units at once, and an
    under-specified rotation; each conflict raises before the star is built.
    """
    with pytest.raises(Exception, match=match):
        _input_rotation(**overrides)


def test_input_rotation_resolves_valid_specifications():
    """``_InputRotation`` maps each valid input to a consistent (Omega, env, core).

    A named percentile string, a rotation period, and an explicit Omega each resolve
    to a positive rotation rate with the envelope and core seeded to the same value.
    """
    omega_slow, env_slow, core_slow = _input_rotation(percentile='slow')
    omega_fast, env_fast, core_fast = _input_rotation(percentile='fast')
    # A slower percentile means a lower rotation rate than a faster one.
    assert 0.0 < omega_slow < omega_fast
    assert env_slow == pytest.approx(omega_slow) and core_slow == pytest.approx(omega_slow)
    omega_prot, env_prot, core_prot = _input_rotation(Prot=10.0)
    assert omega_prot > 0.0 and env_prot == pytest.approx(core_prot)
    omega_e, env_e, core_e = _input_rotation(Omega=1.5)
    assert env_e == pytest.approx(1.5) and core_e == pytest.approx(1.5)


@pytest.mark.parametrize(
    'kwargs,match',
    [
        ({'Omega': 1.0, 'Mstar': None}, 'Mstar must be set'),
        ({'Omega': 1.0, 'Prot': 10.0}, 'Omega and Prot cannot both'),
        ({}, 'must set either Omega, Prot, or percentile'),
    ],
    ids=['no-mass', 'omega-and-prot', 'no-rotation-or-percentile'],
)
def test_percentile_validates_arguments(kwargs, match):
    """``Percentile`` rejects a missing mass and an ambiguous or absent rotation.

    Determining a percentile needs a mass and exactly one rotation specification;
    a missing mass, both Omega and Prot, or neither each raise.
    """
    base = dict(Mstar=1.0)
    base.update(kwargs)
    with pytest.raises(Exception, match=match):
        mors.Percentile(**base)


def test_percentile_validates_supplied_distribution():
    """A user-supplied distribution must carry exactly one rate array of matching length.

    When ``MstarDist`` is given, the code needs one of ``OmegaDist`` / ``ProtDist``,
    forbids supplying both, and requires the rate array to match the mass array in
    length; each violation raises.
    """
    md = np.array([1.0, 1.0])
    with pytest.raises(Exception, match='OmegaDist and ProtDist must'):
        mors.Percentile(Mstar=1.0, Omega=1.0, MstarDist=md)
    with pytest.raises(Exception, match='cannot both be set'):
        mors.Percentile(
            Mstar=1.0, Omega=1.0, MstarDist=md,
            OmegaDist=np.array([1.0, 2.0]), ProtDist=np.array([10.0, 20.0]),
        )
    with pytest.raises(Exception, match='same length'):
        mors.Percentile(
            Mstar=1.0, Omega=1.0,
            MstarDist=np.array([1.0, 1.0, 1.0]), OmegaDist=np.array([1.0, 2.0]),
        )


@pytest.mark.physics_invariant
def test_percentile_inverts_rotation_and_percentile():
    """Percentile and its inverse round-trip on a controlled rotation distribution.

    Mapping a percentile to a rotation rate and back must recover the original
    percentile, and every result stays inside [0, 100]. A five-star bin with
    distinct rates makes the inversion well-posed.
    """
    md = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    od = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    omega_mid = mors.Percentile(Mstar=1.0, percentile=50.0, MstarDist=md, OmegaDist=od)
    # The median of 1..5 is 3, discriminating a wrong-quantile selection.
    assert omega_mid == pytest.approx(3.0, rel=1e-6)
    recovered = mors.Percentile(Mstar=1.0, Omega=omega_mid, MstarDist=md, OmegaDist=od)
    assert 0.0 <= recovered <= 100.0
    assert recovered == pytest.approx(50.0, abs=0.1)
    # Passing a rotation period returns the percentile of that rate, not a rate.
    pct_from_prot = mors.Percentile(Mstar=1.0, Prot=15.0, MstarDist=md, OmegaDist=od)
    assert 0.0 <= pct_from_prot <= 100.0


def test_percentile_protdist_conversion_unavailable():
    """Supplying only ``ProtDist`` surfaces the missing period-to-rate helper.

    The period-distribution branch calls ``misc._Omega`` to convert periods to
    rotation rates, but no such helper exists on the miscellaneous module, so the
    call raises rather than returning a silently wrong rotation distribution.
    """
    md = np.array([1.0, 1.0])
    pd = np.array([10.0, 20.0])
    # This pins the present behaviour of the ProtDist branch: it references a
    # helper that is not defined, so it raises instead of building a distribution.
    with pytest.raises(AttributeError):
        mors.Percentile(Mstar=1.0, percentile=50.0, MstarDist=md, ProtDist=pd)
    # The equivalent rate-distribution path is well-defined and returns a value
    # inside the physical rotation range, confirming only the period branch is out.
    omega = mors.Percentile(
        Mstar=1.0, percentile=50.0, MstarDist=md, OmegaDist=np.array([2.0, 4.0])
    )
    assert omega == pytest.approx(3.0, rel=1e-6)


@pytest.mark.physics_invariant
def test_percentile_requires_two_stars_in_mass_bin():
    """Both percentile directions refuse a mass bin with fewer than two stars.

    A single star in the mass window cannot define a distribution, so requesting a
    rotation rate for a percentile or a percentile for a rotation rate both raise.
    """
    params = dict(paramsDefault)
    md = np.array([1.0])
    od = np.array([1.0])
    with pytest.raises(Exception, match='at least two stars'):
        star_mod._OmegaPercentile(1.0, 50.0, md, od, params)
    with pytest.raises(Exception, match='at least two stars'):
        star_mod._PerPercentile(1.0, 1.0, md, od, params)


@pytest.mark.physics_invariant
def test_per_percentile_clamps_out_of_range_rotation():
    """The rotation-to-percentile map clamps below the slowest and above the fastest star.

    A rate at or below the minimum of the bin is the 0th percentile and a rate at
    or above the maximum is the 100th; an interior rate returns a bounded value in
    between. This pins the boundary behaviour and the monotone interior.
    """
    params = dict(paramsDefault)
    md = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    od = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert star_mod._PerPercentile(1.0, 0.5, md, od, params) == pytest.approx(0.0)
    assert star_mod._PerPercentile(1.0, 9.0, md, od, params) == pytest.approx(100.0)
    interior = star_mod._PerPercentile(1.0, 3.0, md, od, params)
    # The median rate (3) sits at the middle of the distribution.
    assert interior == pytest.approx(50.0, abs=0.1)
    assert 0.0 < interior < 100.0
