"""Tests for src/mors/baraffe.py.

Exercises the Baraffe evolutionary-track interpolation (luminosity, stellar
radius, and insolation at an orbital distance) against the published Baraffe
et al. (2015) tracks. The file asserts the invariants a wrong track index or a
dropped unit conversion would break: positivity of every returned quantity and
a monotone increase of luminosity with stellar mass at fixed age.

Anchor: docs/Validation/baraffe.md.
"""

from __future__ import annotations

import pytest
from numpy.testing import assert_allclose

import mors

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]

# (Mstar [Msun], age [yr], aOrb [AU]) -> (Luminosity [Lsun], Rstar [Rsun],
# insolation [W/m^2]) pinned against the Baraffe et al. (2015) tracks. The two
# masses span a factor ~24 so a wrong track index moves the luminosity by
# orders of magnitude, well outside the 1e-5 tolerance.
TEST_DATA = (
    ((0.047, 8.5e7, 0.75), (0.74306071e-3, 0.14300000, 1.79809587)),
    ((1.113, 3.2e9, 1.05), (1.65441005, 1.18216231, 2.04256380e3)),
)


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
@pytest.mark.parametrize('inp,expected', TEST_DATA)
def test_baraffe_track_matches_published_values(inp, expected):
    """Pin Baraffe luminosity, radius, and insolation against the tracks.

    Reference: Baraffe et al. (2015), A&A 577, A42. A regression that shifts
    the interpolation onto the wrong track or drops a unit conversion moves the
    result far outside the tolerance. The positivity guard catches a sign flip
    or a zeroed lookup that a pure numeric pin could miss.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    baraffe = mors.BaraffeTrack(inp[0])
    ret = (
        baraffe.BaraffeLuminosity(inp[1]),
        baraffe.BaraffeStellarRadius(inp[1]),
        baraffe.BaraffeSolarConstant(inp[1], inp[2]),
    )
    # Positivity: luminosity, radius, and insolation are strictly positive for
    # any main-sequence star; a sign flip or a zero signals a broken lookup.
    assert all(x > 0.0 for x in ret)
    # rtol=1e-5 tracks the precision of the pinned reference values.
    assert_allclose(ret, expected, rtol=1e-5, atol=0)


@pytest.mark.physics_invariant
def test_baraffe_luminosity_increases_with_mass():
    """A more massive main-sequence star is more luminous at fixed age.

    Compares the 0.047 and 1.113 Msun Baraffe tracks at a common 3.2 Gyr age:
    the luminosity must rise steeply with mass, so a swapped track index or a
    mass-independent lookup fails loudly rather than passing on a plausible
    single-mass value.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    age = 3.2e9  # yr, on the main sequence for both masses
    low = mors.BaraffeTrack(0.047).BaraffeLuminosity(age)
    high = mors.BaraffeTrack(1.113).BaraffeLuminosity(age)
    assert low > 0.0
    assert high > 0.0
    # A 1.113 Msun star outshines a 0.047 Msun star by well over two orders of
    # magnitude; the factor-100 floor is far above interpolation noise.
    assert high > 100.0 * low
