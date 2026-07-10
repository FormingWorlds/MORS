"""Tests for src/mors/baraffe.py.

Exercises the Baraffe evolutionary-track interpolation (luminosity, stellar
radius, and insolation at an orbital distance) against the published Baraffe
et al. (2015) tracks. The file asserts the invariants a wrong track index or a
dropped unit conversion would break: positivity of every returned quantity and
a monotone increase of luminosity with stellar mass at fixed age.

Anchor: docs/Validation/baraffe.md.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors
from mors import baraffe

pytestmark = [pytest.mark.integration, pytest.mark.timeout(300)]

# (Mstar [Msun], age [yr], aOrb [AU]) -> (Luminosity [Lsun], Rstar [Rsun],
# insolation [W/m^2]) pinned against the interpolation of the Baraffe et al.
# (2015) tracks. The two cases sit at different ages, so the pins are regression
# checks of the track interpolation; the same-age mass discrimination lives in
# the companion monotonicity test below.
TEST_DATA = (
    ((0.047, 8.5e7, 0.75), (0.74306071e-3, 0.14300000, 1.79809587)),
    ((1.113, 3.2e9, 1.05), (1.65441005, 1.18216231, 2.04256380e3)),
)


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
@pytest.mark.parametrize('inp,expected', TEST_DATA)
def test_baraffe_track_matches_published_values(inp, expected):
    """Pin Baraffe luminosity, radius, and insolation against the tracks.

    Reference: the Baraffe et al. (2015), A&A 577, A42 evolutionary tracks. The
    pinned values are the interpolation of the published tracks; a regression
    that shifts the interpolation onto the wrong track or drops a unit
    conversion moves the result far outside the tolerance. The positivity guard
    catches a sign flip or a zeroed lookup that a pure numeric pin could miss.
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
    """Luminosity rises steeply with mass at a fixed age across the Baraffe grid.

    Compares the 0.047 Msun (substellar, below the hydrogen-burning limit) and
    1.113 Msun tracks at a common 3.2 Gyr age: the luminosity must rise steeply
    with mass, so a swapped track index or a mass-independent lookup fails
    loudly rather than passing on a plausible single-mass value.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    age = 3.2e9  # yr, an age both tracks cover
    low = mors.BaraffeTrack(0.047).BaraffeLuminosity(age)
    high = mors.BaraffeTrack(1.113).BaraffeLuminosity(age)
    assert low > 0.0
    assert high > 0.0
    # A 1.113 Msun star outshines a 0.047 Msun object by well over two orders of
    # magnitude; the factor-100 floor is far above interpolation noise.
    assert high > 100.0 * low


def test_baraffe_track_rejects_off_grid_masses():
    """Construction refuses stellar masses outside the tabulated Baraffe grid.

    The lowest grid node is 0.010 Msun and the highest is 1.400 Msun; a request
    below or above that range has no track to interpolate onto, so the
    constructor must raise rather than silently extrapolate. Both boundary
    directions are exercised, and the guard must fire before any track is stored.
    """
    with pytest.raises(Exception, match='too low'):
        mors.BaraffeTrack(0.005)
    with pytest.raises(Exception, match='too high'):
        mors.BaraffeTrack(1.5)


@pytest.mark.physics_invariant
def test_baraffe_exact_grid_mass_loads_positive_track():
    """A mass on a grid node loads its track directly without mass interpolation.

    1.000 Msun is a tabulated node, so the exact-match branch runs and no
    neighbour blending happens. The stored track must span a positive,
    ascending time axis and hold strictly positive luminosity, radius, and
    effective temperature at every sample; a broken loader would leave a zero or
    negative entry.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    track = mors.BaraffeTrack(1.000)
    assert track.tmin > 0.0
    assert track.tmax > track.tmin
    assert np.all(track.track['Lstar'] > 0.0)
    assert np.all(track.track['Rstar'] > 0.0)
    assert np.all(track.track['Teff'] > 0.0)


@pytest.mark.physics_invariant
def test_baraffe_getters_clip_below_track_start(caplog):
    """Ages younger than the track start clip to the youngest sampled value.

    An age below tmin is out of range for every getter; the documented contract
    clamps it to tmin and warns rather than extrapolating. The nearest-node
    lookup (argmin over |t - tstar|) would already land on the first sample for
    any age below the grid, so the returned value alone cannot prove the clamp
    branch ran. The captured "too low" warning is the direct evidence that the
    clamp fired; the endpoint equality then confirms it clamped to tmin (the
    youngest node) and each clamped quantity stays strictly positive.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    track = mors.BaraffeTrack(1.000)
    young = track.tmin * 0.1  # well below the first tabulated age
    with caplog.at_level(logging.WARNING, logger='fwl.mors.baraffe'):
        lum = track.BaraffeLuminosity(young)
        rad = track.BaraffeStellarRadius(young)
        teff = track.BaraffeStellarTeff(young)
    # One "too low" warning per getter is emitted only inside the clamp branch.
    assert caplog.text.count('too low') == 3
    assert lum > 0.0 and rad > 0.0 and teff > 0.0
    assert_allclose(lum, track.BaraffeLuminosity(track.tmin), rtol=1e-12)
    assert_allclose(rad, track.BaraffeStellarRadius(track.tmin), rtol=1e-12)
    assert_allclose(teff, track.BaraffeStellarTeff(track.tmin), rtol=1e-12)


@pytest.mark.physics_invariant
def test_baraffe_getters_clip_above_track_end(caplog):
    """Ages older than the track end clip to the oldest sampled value.

    An age above tmax is out of range; the getters clamp to tmax. As with the
    below-range case, the nearest-node lookup would already select the last
    sample for any age past the grid, so the captured "too high" warning is the
    direct evidence that the clamp branch executed. The endpoint equality then
    confirms the clamp targets tmax, and the tmin comparison shows it selects the
    correct end of the track rather than a fixed constant.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    track = mors.BaraffeTrack(1.000)
    old = track.tmax * 10.0  # well above the last tabulated age
    with caplog.at_level(logging.WARNING, logger='fwl.mors.baraffe'):
        lum = track.BaraffeLuminosity(old)
        rad = track.BaraffeStellarRadius(old)
        teff = track.BaraffeStellarTeff(old)
    # One "too high" warning per getter is emitted only inside the clamp branch.
    assert caplog.text.count('too high') == 3
    assert_allclose(lum, track.BaraffeLuminosity(track.tmax), rtol=1e-12)
    assert_allclose(rad, track.BaraffeStellarRadius(track.tmax), rtol=1e-12)
    assert_allclose(teff, track.BaraffeStellarTeff(track.tmax), rtol=1e-12)
    # The two ends of a Sun-like track differ: the clamp picks tmax, not tmin.
    assert abs(teff - track.BaraffeStellarTeff(track.tmin)) > 1.0


@pytest.mark.physics_invariant
def test_baraffe_spectrum_scales_linearly_with_luminosity():
    """Historical spectrum scales the modern flux by the luminosity ratio.

    BaraffeSpectrumCalc multiplies a modern flux array by Lstar(t) / Lstar_modern.
    The discriminating check is behavioural: doubling the reference luminosity
    must halve every scaled flux, which pins the reference as a divisor rather
    than a multiplier, and the proportionality across the input array (a threefold
    larger input entry yields a threefold larger output entry) confirms the flux
    enters as a per-element factor. Every scaled entry stays strictly positive.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    track = mors.BaraffeTrack(1.000)
    modern_flux = [1.0, 2.5, 4.0]
    lstar_modern = 1.0  # Lsun reference
    young_age = 1.0e6  # yr, pre-main-sequence contraction, clips to tmin
    scaled = track.BaraffeSpectrumCalc(young_age, lstar_modern, modern_flux)
    assert np.all(scaled > 0.0)
    # The scaling is a single per-element factor, so output ratios track input
    # ratios: entry 2 (4.0) must be 4.0 / 1.0 times entry 0 (1.0).
    assert_allclose(scaled[2] / scaled[0], modern_flux[2] / modern_flux[0], rtol=1e-12)
    # Doubling the modern reference luminosity halves the scaled flux: the
    # reference enters as a divisor, so an accidental multiply would double it.
    scaled_double_ref = track.BaraffeSpectrumCalc(young_age, 2.0 * lstar_modern, modern_flux)
    assert_allclose(scaled_double_ref, 0.5 * scaled, rtol=1e-12)


@pytest.mark.physics_invariant
def test_baraffe_load_track_uninterpolated_matches_grid_nodes():
    """The uninterpolated loader returns the raw track nodes, not a fine grid.

    With pre_interp=False the loader skips the PchipInterpolator resampling and
    returns the tabulated nodes directly. That raw track holds far fewer samples
    than the 5e4-point interpolated grid, yet every luminosity, radius, and
    effective-temperature node stays strictly positive and the time axis is
    strictly ascending.
    """
    mors.DownloadEvolutionTracks('Baraffe')
    raw = baraffe.BaraffeLoadTrack(1.000, pre_interp=False)
    fine = baraffe.BaraffeLoadTrack(1.000, pre_interp=True)
    assert len(raw['t']) < len(fine['t'])
    assert np.all(raw['Lstar'] > 0.0)
    assert np.all(raw['Rstar'] > 0.0)
    assert np.all(raw['Teff'] > 0.0)
    assert np.all(np.diff(raw['t']) > 0.0)


def test_baraffe_load_track_missing_file_raises(monkeypatch, tmp_path):
    """A missing track file surfaces a clear IO error, not a bare parse failure.

    When FWL_DATA points at a directory with no Baraffe files, the loader must
    raise before attempting to read, so the user is told to fetch the data
    rather than hitting an opaque loadtxt error. The empty directory guarantees
    the file is absent and no track dictionary is returned.
    """
    monkeypatch.setattr(baraffe, 'FWL_DATA_DIR', tmp_path)
    with pytest.raises(IOError) as excinfo:
        baraffe.BaraffeLoadTrack(1.000)
    # The raised message currently emits the literal placeholder '{path}' rather
    # than the resolved path; this pins the present behaviour of the loader's
    # error string and is not an endorsement of the missing interpolation.
    assert 'Cannot find Baraffe track file' in str(excinfo.value)
    # No stray track file was created as a side effect of the failed load.
    assert not any(tmp_path.rglob('*.txt'))


def test_modern_spectrum_load_reads_and_copies(tmp_path):
    """Loading a modern spectrum copies the file byte-for-byte and splits columns.

    ModernSpectrumLoad performs no sanitisation: it copies the input two-header,
    tab-delimited spectrum to the output path and hands back the two columns as
    read. The guarantees it actually provides are that the destination file is a
    faithful copy of the source and that the first column becomes the wavelength
    return and the second the flux return, so no column is transposed. Column
    ordering is exercised with a deliberately non-monotone wavelength column so a
    silent sort or swap would be caught.
    """
    src = tmp_path / 'modern.sflux'
    dst = tmp_path / 'copied.sflux'
    # Wavelengths are intentionally out of order; the loader must return them as
    # given, since it does not sort, so a swap or a sort would change the output.
    wl = np.array([400.0, 100.0, 800.0, 200.0])
    fl = np.array([1.0e-3, 5.0e-3, 2.0e-3, 4.0e-4])
    with open(src, 'w') as fh:
        fh.write('# header line one\n# header line two\n')
        for w, f in zip(wl, fl):
            fh.write(f'{w}\t{f}\n')
    out_wl, out_fl = baraffe.ModernSpectrumLoad(str(src), str(dst))
    # The destination is a faithful byte copy of the source input.
    assert dst.exists()
    assert dst.read_bytes() == src.read_bytes()
    # Column split preserves order and orientation (first column -> wavelength).
    assert_allclose(out_wl, wl, rtol=1e-12)
    assert_allclose(out_fl, fl, rtol=1e-12)


def test_modern_spectrum_load_missing_input_raises(tmp_path):
    """A missing modern-spectrum input raises FileNotFoundError before copying.

    The loader validates that the input path exists; pointing it at an absent
    file must raise FileNotFoundError and leave no output file behind, so a typo
    in the spectrum path fails loudly rather than producing an empty copy.
    """
    missing = tmp_path / 'does_not_exist.sflux'
    dst = tmp_path / 'out.sflux'
    with pytest.raises(FileNotFoundError):
        baraffe.ModernSpectrumLoad(str(missing), str(dst))
    assert not dst.exists()
