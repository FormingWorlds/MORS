import pytest
import numpy as np
from numpy.testing import assert_allclose

import mors.spectrum as specmod


# WhichBand

WHICHBAND_DATA = (
    (0.517, ["xr"]),
    (10.5, ["xr", "e1"]),
    (12.5, ["e1"]),
    (32.0, ["e2"]),
    (92.0, ["uv"]),
    (399.999, ["uv"]),
    (400.0, ["pl"]),
    (1.0e9, None),
    (1e-6, None),
)

@pytest.mark.parametrize("wl,expected", WHICHBAND_DATA)
def test_WhichBand(wl, expected):
    assert specmod.WhichBand(wl) == expected

# Scaling + Planck helpers

SCALE_DATA = (
    (np.array([1.0, 2.0, 3.0]), 6.96e8),
    (np.array([1e-10, 3e-10, 9e-10]), 1.5e9),
)

@pytest.mark.parametrize("fl,R_star", SCALE_DATA)
def test_scale_roundtrip(fl, R_star):
    # 1AU -> surface -> 1AU should recover original
    fl_surf = specmod.ScaleToSurf(fl, R_star)
    fl_back = specmod.ScaleTo1AU(fl_surf, R_star)
    assert_allclose(fl_back, fl, rtol=1e-12, atol=0.0)


PLANCK_DATA = (
    (np.array([500.0]), 3000.0, 6000.0),
    (np.array([200.0, 500.0, 1000.0]), 4000.0, 8000.0),
)

@pytest.mark.parametrize("wl,T1,T2", PLANCK_DATA)
def test_planck_increases_with_temperature(wl, T1, T2):
    f1 = specmod.PlanckFunction_surf(wl, Teff=T1)
    f2 = specmod.PlanckFunction_surf(wl, Teff=T2)
    assert np.all(f2 > f1)
    assert np.all(f1 > 0.0)


# Spectrum: LoadDirectly / CalcBandFluxes

@pytest.mark.parametrize(
    "wl,fl",
    (
        # descending wl + bad flux values (nan, 0, negative)
        (
            np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.8, 0.6, 0.55, 0.53, 0.52, 0.518]),
            np.array([1.0, np.nan, 0.0, -1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
        ),
    ),
)
def test_Spectrum_LoadDirectly_sanitizes_and_orders(wl, fl):
    s = specmod.Spectrum().LoadDirectly(wl, fl)

    assert s.loaded is True
    assert s.nbins == len(wl)

    # should be wl ascending
    assert np.all(np.diff(s.wl) > 0)

    # flux should be finite and floored at 1e-20
    assert np.all(np.isfinite(s.fl))
    assert np.min(s.fl) >= 1e-20

    # binwidth length nbins-1
    assert len(s.binwidth) == s.nbins - 1


@pytest.mark.parametrize(
    "wl,fl,expected",
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
                "xr": 9.9 - 0.6,
                "e1": 31.9 - 12.6,
                "e2": 91.9 - 32.1,
                "uv": 399.9 - 92.1,
                "pl": 900.0 - 400.1,
                "bo": 900.0 - 0.6,
            },
        ),
    ),
)
def test_Spectrum_CalcBandFluxes_constant(wl, fl, expected):
    if fl is None:
        fl = np.ones_like(wl)

    s = specmod.Spectrum().LoadDirectly(wl, fl)
    integ = s.CalcBandFluxes()

    ret = (integ["xr"], integ["e1"], integ["e2"], integ["uv"], integ["pl"], integ["bo"])
    exp = (expected["xr"], expected["e1"], expected["e2"], expected["uv"], expected["pl"], expected["bo"])

    assert_allclose(ret, exp, rtol=1e-12, atol=0.0)


# Spectrum: extensions

EXT_SHORT_DATA = (
    (0.1, np.linspace(1.0, 10.0, 200), np.linspace(2.0, 3.0, 200)),
    (0.01, np.linspace(5.0, 50.0, 300), np.ones(300) * 7.0),
)

@pytest.mark.parametrize("wl_min,wl,fl", EXT_SHORT_DATA)
def test_Spectrum_ExtendShortwave(wl_min, wl, fl):
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

@pytest.mark.parametrize("Teff,R_star,wl_max", EXT_PLANCK_DATA)
def test_Spectrum_ExtendPlanck(Teff, R_star, wl_max):
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
    assert np.all(s.fl[s.ext_long :] > 0.0)


# TSV I/O

@pytest.mark.parametrize(
    "wl,fl",
    (
        (np.linspace(1.0, 100.0, 200), np.linspace(1e-10, 2e-10, 200)),
    ),
)
def test_Spectrum_tsv_roundtrip(tmp_path, wl, fl):
    s1 = specmod.Spectrum().LoadDirectly(wl, fl)

    fp = tmp_path / "spec.tsv"
    out_fp = s1.WriteTSV(str(fp))
    assert fp.exists()
    assert str(fp) == out_fp

    s2 = specmod.Spectrum().LoadTSV(str(fp))

    assert s2.loaded is True
    assert s2.nbins == s1.nbins

    # WriteTSV uses fmt='%1.4e' so allow small error
    assert_allclose(s2.wl, s1.wl, rtol=1e-4, atol=0.0)
    assert_allclose(s2.fl, s1.fl, rtol=1e-4, atol=0.0)
