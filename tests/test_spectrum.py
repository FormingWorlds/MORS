"""Tests for src/mors/spectrum.py.

Exercises the band classification, surface / 1 AU flux scaling, Planck surface
flux, spectrum sanitisation, band integration, spectral extensions, and TSV
round-trip of ``mors.spectrum``. The physics invariants asserted here are the
symmetry of the flux-scaling pair, the monotonicity of the Planck surface flux
with temperature, the strictly ascending sanitised wavelength grid with its
positive flux floor, and the analytical-limit band integral of a constant
spectrum (integral of a unit integrand equals the band width).

Anchor: docs/Validation/spectrum.md.
"""

from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors.spectrum as specmod

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


# WhichBand

WHICHBAND_DATA = (
    (0.517, ['xr']),
    (10.5, ['xr', 'e1']),
    (12.5, ['e1']),
    (32.0, ['e2']),
    (92.0, ['uv']),
    (399.999, ['uv']),
    (400.0, ['pl']),
    (1.0e9, None),
    (1e-6, None),
)


@pytest.mark.parametrize('wl,expected', WHICHBAND_DATA)
def test_WhichBand_classifies_wavelengths(wl, expected):
    """WhichBand maps a wavelength (nm) to the emission band(s) covering it.

    Overlap regions (e.g. 10.5 nm) return more than one band, and wavelengths
    outside the full modelled range return None. The second assertion checks
    the classification is self-consistent with the band-limit table, so a
    regression that renamed a band or shifted a boundary fails even where the
    pinned expectation happens to still match.
    """
    result = specmod.WhichBand(wl)
    assert result == expected
    lo = min(limits[0] for limits in specmod.bands_limits.values())
    hi = max(limits[1] for limits in specmod.bands_limits.values())
    if result is None:
        # None is returned only outside the union of all band limits; the
        # upper edge is exclusive, so the top of the pl band maps to None too.
        assert wl < lo or wl >= hi
    else:
        # Every returned band names a real key and actually brackets wl.
        assert all(band in specmod.bands_limits for band in result)
        assert all(
            specmod.bands_limits[band][0] <= wl <= specmod.bands_limits[band][1]
            for band in result
        )


# Scaling + Planck helpers

SCALE_DATA = (
    (np.array([1.0, 2.0, 3.0]), 6.96e8),
    (np.array([1e-10, 3e-10, 9e-10]), 1.5e9),
)


@pytest.mark.physics_invariant
@pytest.mark.parametrize('fl,R_star', SCALE_DATA)
def test_scale_surface_to_1au_roundtrip(fl, R_star):
    """Scaling a flux to the stellar surface and back recovers the input.

    ``ScaleToSurf`` multiplies by ``(AU / R_star)**2`` and ``ScaleTo1AU`` divides
    by it, so the pair is an exact inverse (symmetry invariant). The surface
    flux must also exceed the 1 AU flux because the stellar radius is far
    smaller than an AU; that guard catches a swapped or dropped scaling factor
    that a pure round-trip would hide.
    """
    fl_surf = specmod.ScaleToSurf(fl, R_star)
    fl_back = specmod.ScaleTo1AU(fl_surf, R_star)
    assert_allclose(fl_back, fl, rtol=1e-12, atol=0.0)
    # R_star << AU, so concentrating the flux onto the surface raises it.
    assert np.all(fl_surf > fl)


PLANCK_DATA = (
    (np.array([500.0]), 3000.0, 6000.0),
    (np.array([200.0, 500.0, 1000.0]), 4000.0, 8000.0),
)


@pytest.mark.physics_invariant
@pytest.mark.parametrize('wl,T1,T2', PLANCK_DATA)
def test_planck_surface_flux_increases_with_temperature(wl, T1, T2):
    """The Planck surface flux rises with effective temperature at fixed wavelength.

    T1 and T2 are chosen a full factor of two apart so the steep temperature
    dependence of the black-body function is resolved far above numerical
    noise. The positivity guard rejects a sign flip; the monotonicity guard
    rejects a temperature-independent lookup.
    """
    f1 = specmod.PlanckFunction_surf(wl, Teff=T1)
    f2 = specmod.PlanckFunction_surf(wl, Teff=T2)
    assert np.all(f1 > 0.0)
    assert np.all(f2 > f1)


# Spectrum: LoadDirectly / CalcBandFluxes

@pytest.mark.physics_invariant
@pytest.mark.parametrize(
    'wl,fl',
    (
        # descending wl + bad flux values (nan, 0, negative)
        (
            np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.8, 0.6, 0.55, 0.53, 0.52, 0.518]),
            np.array([1.0, np.nan, 0.0, -1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
        ),
    ),
)
def test_Spectrum_LoadDirectly_sanitizes_and_orders(wl, fl):
    """Loading a raw spectrum sorts wavelengths and floors the flux positive.

    The input is intentionally adversarial: wavelengths in descending order and
    a flux array containing nan, zero, and a negative value. After loading, the
    wavelength grid must be strictly ascending (monotonicity) and every flux
    finite and at or above the 1e-20 floor (positivity / boundedness), so the
    downstream band integrals never see a non-physical value.
    """
    s = specmod.Spectrum().LoadDirectly(wl, fl)

    assert s.loaded is True
    assert s.nbins == len(wl)

    # Wavelength grid must be strictly ascending after sanitisation.
    assert np.all(np.diff(s.wl) > 0)

    # Flux must be finite and floored above zero; no nan / zero / negative.
    assert np.all(np.isfinite(s.fl))
    assert np.min(s.fl) >= 1e-20

    # binwidth has one fewer entry than the grid.
    assert len(s.binwidth) == s.nbins - 1


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
@pytest.mark.parametrize(
    'wl,fl,expected',
    (
        # Constant flux=1, segments chosen to avoid overlap regions so band integrals are clean.
        (
            np.concatenate(
                [
                    np.linspace(0.6, 9.9, 50),        # xr (avoid 10..12.5 overlap)
                    np.linspace(12.6, 31.9, 50),      # e1
                    np.linspace(32.1, 91.9, 50),      # e2
                    np.linspace(92.1, 399.9, 100),    # uv
                    np.linspace(400.1, 900.0, 100),   # pl
                ]
            ),
            None,  # filled below
            {
                'xr': 9.9 - 0.6,
                'e1': 31.9 - 12.6,
                'e2': 91.9 - 32.1,
                'uv': 399.9 - 92.1,
                'pl': 900.0 - 400.1,
                'bo': 900.0 - 0.6,
            },
        ),
    ),
)
def test_Spectrum_CalcBandFluxes_constant_integrand(wl, fl, expected):
    """A unit-flux spectrum integrates to the band width in every band.

    Analytical limit: the integral of a constant integrand of value 1 over a
    band is exactly the band width. Feeding a flat spectrum therefore pins each
    band integral to a hand-computed width, and the bolometric integral to the
    full wavelength span. A wrong integration weight (trapezoid vs rectangle),
    a dropped bin width, or a units slip fails against the 1e-12 tolerance.
    """
    if fl is None:
        fl = np.ones_like(wl)

    s = specmod.Spectrum().LoadDirectly(wl, fl)
    integ = s.CalcBandFluxes()

    ret = (integ['xr'], integ['e1'], integ['e2'], integ['uv'], integ['pl'], integ['bo'])
    exp = (expected['xr'], expected['e1'], expected['e2'], expected['uv'],
           expected['pl'], expected['bo'])

    # Every band integral is positive for a positive integrand.
    assert all(x > 0.0 for x in ret)
    assert_allclose(ret, exp, rtol=1e-12, atol=0.0)


# Spectrum: extensions

EXT_SHORT_DATA = (
    (0.1, np.linspace(1.0, 10.0, 200), np.linspace(2.0, 3.0, 200)),
    (0.01, np.linspace(5.0, 50.0, 300), np.ones(300) * 7.0),
)


@pytest.mark.parametrize('wl_min,wl,fl', EXT_SHORT_DATA)
def test_Spectrum_ExtendShortwave(wl_min, wl, fl):
    """Extending a spectrum to shorter wavelengths prepends a flat continuation.

    The extension grows the grid, reaches the requested lower wavelength, meets
    the original grid at the seam, and holds the first flux value across the new
    short-wavelength bins. Checking the seam and the held value rejects an
    off-by-one in the insertion index.
    """
    s = specmod.Spectrum().LoadDirectly(wl, fl)
    old_n = s.nbins
    old_min = s.wl[0]
    old_first_flux = s.fl[0]

    s.ExtendShortwave(wl_min=wl_min)

    assert s.nbins > old_n
    assert s.ext_short > 0
    assert_allclose(s.wl[0], wl_min, rtol=1e-10, atol=0.0)
    assert_allclose(s.wl[s.ext_short], old_min, rtol=1e-10, atol=0.0)
    assert_allclose(s.fl[: s.ext_short], old_first_flux, rtol=0.0, atol=0.0)


EXT_PLANCK_DATA = (
    # (Teff, R_star, wl_max)
    (5800.0, 6.96e8, 1.0e5),
    (4500.0, 1.0e9, 5.0e4),
)


@pytest.mark.physics_invariant
@pytest.mark.parametrize('Teff,R_star,wl_max', EXT_PLANCK_DATA)
def test_Spectrum_ExtendPlanck(Teff, R_star, wl_max):
    """Extending a spectrum with a Planck tail grows a strictly positive long-wave grid.

    The Planck continuation appends bins up to the requested maximum wavelength,
    meets the original grid at the seam, and stays strictly positive (a black-body
    flux never reaches zero at finite temperature). The positivity and seam
    checks reject a tail that clips to zero or overwrites the original grid.
    """
    wl = np.linspace(100.0, 1000.0, 300)  # nm
    fl = np.ones_like(wl) * 1e-5

    s = specmod.Spectrum().LoadDirectly(wl, fl)
    old_n = s.nbins
    old_max = s.wl[-1]

    s.ExtendPlanck(Teff=Teff, R_star=R_star, wl_max=wl_max)

    assert s.nbins > old_n
    assert s.ext_long == old_n
    assert_allclose(s.wl[s.ext_long - 1], old_max, rtol=1e-12, atol=0.0)
    assert_allclose(s.wl[-1], wl_max, rtol=1e-10, atol=0.0)
    assert np.all(s.fl[s.ext_long:] > 0.0)


# TSV I/O

@pytest.mark.parametrize(
    'wl,fl',
    (
        (np.linspace(1.0, 100.0, 200), np.linspace(1e-10, 2e-10, 200)),
    ),
)
def test_Spectrum_tsv_roundtrip(tmp_path, wl, fl):
    """Writing a spectrum to TSV and reading it back preserves the grid and flux.

    The file format writes four significant figures (`fmt='%1.4e'`), so the
    round-trip is checked at `rtol=1e-4` rather than exactly. Both the wavelength
    grid and the flux must survive; asserting on the bin count as well catches a
    truncated or duplicated write.
    """
    s1 = specmod.Spectrum().LoadDirectly(wl, fl)

    fp = tmp_path / 'spec.tsv'
    out_fp = s1.WriteTSV(str(fp))
    assert fp.exists()
    assert str(fp) == out_fp

    s2 = specmod.Spectrum().LoadTSV(str(fp))

    assert s2.loaded is True
    assert s2.nbins == s1.nbins

    # WriteTSV uses fmt='%1.4e' so allow four-significant-figure error.
    assert_allclose(s2.wl, s1.wl, rtol=1e-4, atol=0.0)
    assert_allclose(s2.fl, s1.fl, rtol=1e-4, atol=0.0)
