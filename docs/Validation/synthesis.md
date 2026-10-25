# Validation: `src/mors/synthesis.py`

## What this page checks

This page checks the stellar high-energy budget calculations in `mors.synthesis`.
`synthesis.GetProperties` builds band luminosities and fluxes for X-ray, EUV, UV, photospheric, and bolometric ranges.
Validation means that a test runs the code on an internal self-consistency closure identity, and checks agreement to a tight tolerance.
If this part of the code is wrong, synthetic historical stellar spectra receive incorrect flux scalings in emission bands.
Atmospheric heating rates and photochemical evolution in coupled planetary models are then wrong.

## Flux budget closure

**Why this check exists.** The UV band flux is defined as the bolometric remainder: $F_\mathrm{uv} = F_\mathrm{bo} - F_\mathrm{xr} - F_\mathrm{e1} - F_\mathrm{e2} - F_\mathrm{pl}$. An arithmetic slip or dropped band in this budget breaks flux conservation in the stellar spectrum.

**What it tests.** The test mocks stellar model inputs (`Value`, `Percentile`, `Lxuv`, `Lbol`) with physically plausible constants. It sets the Planck surface flux to zero and `ScaleTo1AU` to the identity, so `F_pl` is zero in this case. It recomputes the expected per-band fluxes and luminosities from physical constants (`AU`, `LbolSun`), pins each returned value, and checks that the 5 sub-band fluxes sum to the bolometric flux. Companion `physics_invariant` tests verify the constant-Planck band integral (`test_GetProperties_planck_trapezoid_constant`), positivity of band-scale factors (`test_CalcBandScales`), and wavelength grid preservation (`test_CalcScaledSpectrumFromProps_scales_by_first_band`).

**How we know the right answer.** By construction, the sub-band fluxes sum exactly to the bolometric flux. A wrong band flux or luminosity conversion moves individual values outside the `rtol=1e-12` tolerance.

**Why it matters.** `mors.synthesis` reconstructs historical stellar spectra to illuminate planetary atmospheres in PROTEUS coupled runs.

**Known limit.** With `F_pl` set to zero, this case does not check the subtraction of the photospheric term from `F_bo`.

??? info "Test details"
    - Reference: self-consistency: the 5 sub-band fluxes sum to the bolometric flux
    - Tolerance: `rtol=1e-12` on each band flux, each band luminosity and the closure
    - Test id: `tests/test_synthesis.py::test_GetProperties_flux_budget`
    - Command: `pytest tests/test_synthesis.py::test_GetProperties_flux_budget`

## Related code

- `src/mors/synthesis.py`: `GetProperties`, `CalcBandScales`, `CalcScaledSpectrumFromProps`, and `FitModernProperties`.
- `src/mors/spectrum.py`: supplies the band limits and Planck surface flux; see [spectrum.md](spectrum.md).
- `tests/test_synthesis.py`: `test_GetProperties_flux_budget` and companion invariant tests.
