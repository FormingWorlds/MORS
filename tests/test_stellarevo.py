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

import pytest
from numpy.testing import assert_allclose

import mors

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]

# Solar age, 4.57 Gyr, in the Myr unit the tracks are indexed by.
SOLAR_AGE_MYR = 4570.0
# Solar effective temperature (K), the standard photospheric value.
T_EFF_SUN = 5772.0


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_stellarevo_solar_calibration():
    """The Spada 1 Msun track reproduces the Sun at the solar age.

    Reference: Spada et al. (2013) solar-calibrated tracks, with the solar
    luminosity and radius normalised to unity and the solar effective
    temperature 5772 K. At 4.57 Gyr the solar-mass track lands within roughly
    10% of L = 1 Lsun, R = 1 Rsun, and 3% of Teff = 5772 K. A wrong track
    index, a wrong age unit, or a units slip would move any of these far outside
    the tolerance.
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
