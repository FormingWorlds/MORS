# Validation: `src/mors/synthesis.py`

## What this page checks

This page checks the stellar high-energy budget calculations in `mors.synthesis`.
`synthesis.GetProperties` builds band luminosities and fluxes for X-ray, EUV, UV, Planck, and bolometric ranges.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance; here the right answer is a self-consistency identity of the band budget.
If this part of the code is wrong, the band scalings of the synthetic stellar spectra of MORS are wrong.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Flux budget closure

**Why this check exists.** The UV band flux is the bolometric remainder: $F_\mathrm{uv} = F_\mathrm{bo} - F_\mathrm{xr} - F_\mathrm{e1} - F_\mathrm{e2} - F_\mathrm{pl}$, with $F$ the flux of each band (bolometric, X-ray, 2 extreme-ultraviolet bands, Planck). A dropped X-ray or extreme-ultraviolet term in this budget, or a wrong conversion of a band flux or luminosity, gives wrong band values without an error message.

**What it tests.** The test replaces the stellar model inputs (`Value`, `Percentile`, `Lxuv`, `Lbol`) with fixed, physically plausible values. It sets the Planck surface flux to zero and `ScaleTo1AU` to the identity, so `F_pl` is zero in this case. It recomputes the expected per-band fluxes and luminosities from physical constants (`AU`, `LbolSun`), pins each returned value, and checks that the 5 sub-band fluxes sum to the bolometric flux. Companion tests check the Planck band integral of a constant (`test_GetProperties_planck_trapezoid_constant`), positive band-scale factors (`test_CalcBandScales`), and that the wavelength grid stays the same (`test_CalcScaledSpectrumFromProps_scales_by_first_band`).

**How we know the right answer.** By the definition of the UV band, the 5 band fluxes must sum to the bolometric flux. The test also computes each band value again with the constants that the source uses (`AU`, `LbolSun`), so a wrong conversion formula moves a value outside the `rtol=1e-12` tolerance. The closure holds by the construction of `F_uv`, so these pins of the single bands do most of the checking.

**Why it matters.** `GetProperties` gives the band properties from which `mors.synthesis` scales a stellar spectrum through time.

**Known limit.** With `F_pl` set to zero, this case does not check the subtraction of the Planck term from `F_bo`; `test_GetProperties_planck_trapezoid_constant` checks the `F_pl` integral, and no test checks its subtraction. The test shares `AU` and `LbolSun` with the source, so a wrong value of these constants does not fail it. It does not check the returned `radius` and `Teff`, nor that `Percentile` feeds `Lxuv`. PROTEUS does not call `GetProperties`: it computes the band properties with its own `get_spada_synthesis_properties` and then calls `CalcScaledSpectrumFromProps`, so this test does not cover the PROTEUS version.

??? info "Test details"
    - Reference: self-consistency: the 5 sub-band fluxes sum to the bolometric flux
    - Tolerance: `rtol=1e-12` on each band flux, each band luminosity and the closure
    - Test id: `tests/test_synthesis.py::test_GetProperties_flux_budget`
    - Command: `pytest tests/test_synthesis.py::test_GetProperties_flux_budget`

## Related code

- `src/mors/synthesis.py`: `GetProperties`, `CalcBandScales`, `CalcScaledSpectrumFromProps`, and `FitModernProperties`.
- `src/mors/spectrum.py`: supplies the band limits and Planck surface flux; see [spectrum.md](spectrum.md).
- `tests/test_synthesis.py`: `test_GetProperties_flux_budget` and companion invariant tests.
