# Validation: `src/mors/spectrum.py`

## What this page checks

This page checks spectral band integration in `mors.spectrum`.
`Spectrum.CalcBandFluxes` integrates stellar spectra over defined wavelength intervals (X-ray, EUV, UV, Planck, and bolometric).
Validation means that a test runs the integrator on an analytical unit spectrum, and checks the results to a tight tolerance.
If this part of the code is wrong, band-integrated stellar fluxes delivered to the planetary atmosphere are incorrect.
Atmospheric heating rates and photochemical evolution in coupled planetary models are then wrong.

## Band integral of a constant spectrum

**Why this check exists.** Numerical band integration can drop bin widths, misapply wavelength unit conversions, or reverse integration signs. The resulting band fluxes would be scaled incorrectly without an error message.

**What it tests.** For an integrand identically equal to 1, the integral over a wavelength band equals the distance between its first and last sample points: $\int 1 \, \mathrm{d}\lambda = \lambda_\mathrm{last} - \lambda_\mathrm{first}$. The test feeds a flat unit spectrum with samples located inside each band (`xr`, `e1`, `e2`, `uv`, `pl`, `bo`). It checks that each band integral equals the span between its endpoints. Companion `physics_invariant` tests cover flux-scaling roundtrips between stellar surface and 1 AU, Planck surface flux monotonicity with temperature, and sanitized wavelength ordering.

**How we know the right answer.** The integral of a unit function over an interval is an analytical closed-form identity equal to the interval span. A dropped bin width or unit error changes the integral by far more than the `rtol=1e-12` tolerance.

**Why it matters.** `mors.synthesis` and PROTEUS consume these band-integrated stellar fluxes to drive atmospheric heating and photochemical models.

??? info "Test details"
    - Reference: closed form: the span between the first and last sample point in each band
    - Tolerance: `rtol=1e-12` on each band and the bolometric integral
    - Test id: `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`
    - Command: `pytest tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`

## Related code

- `src/mors/spectrum.py`: band-limit table `bands_limits`, `PlanckFunction_surf`, `ScaleToSurf` / `ScaleTo1AU`, and the `Spectrum` loader and band integrator.
- `tests/test_spectrum.py`: `test_Spectrum_CalcBandFluxes_constant_integrand` and flux-scaling invariant tests.
