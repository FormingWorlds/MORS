import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors.spectrum as spec
import mors.synthesis as synth

# GetProperties

@pytest.mark.parametrize(
    "Mstar,pctle,age,Lxuv_dict,Lbol_val",
    (
        (1.0, 50.0, 1000.0, {"Lx": 1.0e28, "Leuv1": 2.0e28, "Leuv2": 3.0e28}, 1.0),
    ),
)
def test_GetProperties_flux_budget(monkeypatch, Mstar, pctle, age, Lxuv_dict, Lbol_val):
    """
    Relates to synthesis.GetProperties():

    - Uses Value() for Rstar/Teff
    - Uses Percentile() for Omega
    - Uses Lxuv() for Lx/Leuv1/Leuv2
    - Computes F_k = L_k / (4*pi*AU^2)
    - Computes Planckian band integral F_pl via PlanckFunction_surf + ScaleTo1AU + trapezoid
    - Defines UV as remainder:
        F_uv = F_bo - F_xr - F_e1 - F_e2 - F_pl
    """

    def fake_Value(Mstar_in, age_in, key):
        if key == "Rstar":
            return 1.0  # Rsun 
        if key == "Teff":
            return 5000.0
        raise KeyError(key)

    monkeypatch.setattr(synth, "Value", fake_Value)
    monkeypatch.setattr(synth, "Percentile", lambda **kwargs: 1.0)
    monkeypatch.setattr(synth, "Lxuv", lambda **kwargs: dict(Lxuv_dict))
    monkeypatch.setattr(synth, "Lbol", lambda M, a: Lbol_val)

    # Make Planck contribution small: set surface flux = 0 everywhere
    monkeypatch.setattr(spec, "PlanckFunction_surf", lambda wl, Teff: np.zeros_like(wl, dtype=float))
    monkeypatch.setattr(spec, "ScaleTo1AU", lambda fl, R_star: fl)

    out = synth.GetProperties(Mstar=Mstar, pctle=pctle, age=age)

    # Check keys exist
    for k in ["age", "radius", "Teff", "L_bo", "L_xr", "L_e1", "L_e2", "L_pl", "L_uv",
              "F_bo", "F_xr", "F_e1", "F_e2", "F_pl", "F_uv"]:
        assert k in out

    # Recompute expected area and fluxes using same constants as code
    area = 4.0 * synth.const.Pi * synth.const.AU * synth.const.AU

    expected_L_bo = Lbol_val * synth.const.LbolSun
    expected_L_xr = Lxuv_dict["Lx"]
    expected_L_e1 = Lxuv_dict["Leuv1"]
    expected_L_e2 = Lxuv_dict["Leuv2"]

    expected_F_bo = expected_L_bo / area
    expected_F_xr = expected_L_xr / area
    expected_F_e1 = expected_L_e1 / area
    expected_F_e2 = expected_L_e2 / area

    # Planck patched to zero 
    expected_F_pl = 0.0
    expected_L_pl = 0.0

    # UV remainder
    expected_F_uv = expected_F_bo - expected_F_xr - expected_F_e1 - expected_F_e2 - expected_F_pl
    expected_L_uv = expected_F_uv * area

    ret = (out["F_bo"], out["F_xr"], out["F_e1"], out["F_e2"], out["F_pl"], out["F_uv"])
    exp = (expected_F_bo, expected_F_xr, expected_F_e1, expected_F_e2, expected_F_pl, expected_F_uv)
    assert_allclose(ret, exp, rtol=1e-12, atol=0.0)

    retL = (out["L_bo"], out["L_xr"], out["L_e1"], out["L_e2"], out["L_pl"], out["L_uv"])
    expL = (expected_L_bo, expected_L_xr, expected_L_e1, expected_L_e2, expected_L_pl, expected_L_uv)
    assert_allclose(retL, expL, rtol=1e-12, atol=0.0)


# CalcBandScales

@pytest.mark.parametrize(
    "modern_dict,hist_dict,expected",
    (
        (
            {"F_xr": 1.0, "F_e1": 2.0, "F_e2": 4.0, "F_uv": 8.0, "F_pl": 16.0, "F_bo": 32.0},
            {"F_xr": 2.0, "F_e1": 6.0, "F_e2": 8.0, "F_uv": 4.0, "F_pl": 8.0, "F_bo": 64.0},
            {"Q_xr": 2.0, "Q_e1": 3.0, "Q_e2": 2.0, "Q_uv": 0.5, "Q_pl": 0.5, "Q_bo": 2.0},
        ),
    ),
)
def test_CalcBandScales(modern_dict, hist_dict, expected):
    """
    Relates to synthesis.CalcBandScales():
      for key in spec.bands_limits.keys():
          Q_key = hist["F_key"] / modern["F_key"]
    """
    q = synth.CalcBandScales(modern_dict, hist_dict)
    for k, v in expected.items():
        assert_allclose(q[k], v, rtol=0, atol=0)


# CalcScaledSpectrumFromProps

@pytest.mark.parametrize(
    "wl,fl,expected_mult",
    (
        (
            # includes overlap (11 nm -> ['xr','e1'] -> uses 'xr')
            np.array([1.0, 5.0, 9.0, 11.0, 12.0, 20.0, 31.0, 40.0, 100.0, 500.0]),
            np.ones(10) * 10.0,
            # multipliers per wl:
            # 1,5,9,11,12  -> xr
            # 20,31        -> e1
            # 40           -> e2
            # 100          -> uv
            # 500          -> pl
            np.array([2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 4.0, 5.0, 6.0]),
        ),
    ),
)
def test_CalcScaledSpectrumFromProps_scales_by_first_band(wl, fl, expected_mult):
    modern = spec.Spectrum().LoadDirectly(wl, fl)

    modern_dict = {"F_xr": 1, "F_e1": 1, "F_e2": 1, "F_uv": 1, "F_pl": 1, "F_bo": 1}
    hist_dict   = {"F_xr": 2, "F_e1": 3, "F_e2": 4, "F_uv": 5, "F_pl": 6, "F_bo": 1}

    hist = synth.CalcScaledSpectrumFromProps(modern, modern_dict, hist_dict)

    assert_allclose(hist.wl, modern.wl, rtol=0, atol=0)
    assert_allclose(hist.fl, modern.fl * expected_mult, rtol=0, atol=0)


# FitModernProperties

@pytest.mark.parametrize(
    "age_in,minimize_x,expected",
    (
        # age <= 0 => fit_age False => x0=[1.0], return (x[0], age_in)
        (-1.0, np.array([0.7]), (0.7, -1.0)),
        # age > 0 => fit_age True => x0=[1.0,1000.0], return (x[0], x[1])
        (1000.0, np.array([0.8, 900.0]), (0.8, 900.0)),
    ),
)
def test_FitModernProperties_returns_minimize_solution(monkeypatch, age_in, minimize_x, expected):
    """
    Relates to synthesis.FitModernProperties():

      - Calls modern_spec.CalcBandFluxes()
      - Builds objective _fev() that calls GetProperties()
      - Calls scipy.optimize.minimize(...)
      - Returns best_pctle = result.x[0]
      - Returns best_age   = result.x[1] if fit_age else input age

    Minimize is patched to avoid depending on real stellar models.
    """
    # Make a small valid spectrum (LoadDirectly requires >=10 bins)
    wl = np.linspace(1.0, 900.0, 50)
    fl = np.ones_like(wl)
    modern_spec = spec.Spectrum().LoadDirectly(wl, fl)

    class FakeResult:
        def __init__(self, x):
            self.success = True
            self.x = x

    def fake_minimize(func, x0, method=None):
        # check x0 shape matches code’s logic
        if age_in > 0:
            assert len(x0) == 2
            assert_allclose(x0[0], 1.0, rtol=0, atol=0)
            assert_allclose(x0[1], 1000.0, rtol=0, atol=0)
        else:
            assert len(x0) == 1
            assert_allclose(x0[0], 1.0, rtol=0, atol=0)
        return FakeResult(minimize_x)

    monkeypatch.setattr(synth, "minimize", fake_minimize)

    # Patch GetProperties 
    monkeypatch.setattr(
        synth,
        "GetProperties",
        lambda Mstar, pctle, age: {
            # provide the keys _fev uses
            "F_xr": 1.0, "F_e1": 1.0, "F_e2": 1.0, "F_uv": 1.0
        },
    )

    best_pctle, best_age = synth.FitModernProperties(modern_spec, Mstar=1.0, age=age_in)
    assert_allclose((best_pctle, best_age), expected, rtol=0, atol=0)
