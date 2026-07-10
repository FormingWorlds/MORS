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

import pytest
from numpy.testing import assert_allclose

import mors

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
    # rtol=0.15: the Spada solar-mass track reproduces L_sun to about 10%.
    assert_allclose(lbol, L_SUN_CGS, rtol=0.15)
    # Discrimination: a 0.3 Msun main-sequence star is more than 10x fainter.
    faint = mors.Star(Mstar=0.3, Omega=1.0).Value(SOLAR_AGE_MYR, 'Lbol')
    assert faint < 0.1 * lbol


@pytest.mark.physics_invariant
@pytest.mark.parametrize('inp,expected', SPADA_DEFAULT)
def test_star_value_default_integrator(inp, expected):
    """Pin Star.Value (default integrator) against the Spada track model.

    Verifies the coupled rotation + structure model reproduces its tabulated
    radius, bolometric luminosity, and EUV luminosity, and that all three are
    strictly positive. The four masses span brown-dwarf to solar-type stars.
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

    The forward-Euler rotation history yields the same structure but a slightly
    different activity than the default integrator, so the EUV luminosity is
    pinned to its own tabulated value. Positivity of every returned quantity is
    asserted alongside the numeric pin.
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
