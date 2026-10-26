# Validation: `src/mors/spectrum.py`

## What this page checks

This page checks spectral band integration in `mors.spectrum`.
`Spectrum.CalcBandFluxes` integrates stellar spectra over defined wavelength intervals (X-ray, EUV, UV, Planck, and bolometric).
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, the band fluxes of the stellar spectrum are wrong, and so is the spectrum that MORS scales from them.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Band integral of a constant spectrum

**Why this check exists.** A band integration can drop the bin width, use the wrong wavelength unit, or reverse the sign of the integral. The band fluxes would then be wrong without an error message.

**What it tests.** For an integrand identically equal to 1, the integral over a wavelength band equals the distance between its first and last sample points: $\int 1 \, \mathrm{d}\lambda = \lambda_\mathrm{last} - \lambda_\mathrm{first}$. The bands are X-ray (`xr`), 2 extreme-ultraviolet bands (`e1`, `e2`), ultraviolet (`uv`), the photospheric band (`pl`) and the full bolometric range (`bo`). The test builds a flat spectrum whose sample points lie inside each band and away from the regions where bands overlap. Each band integral must equal the span between its upper and lower sample wavelengths, and the bolometric integral the full sampled span. The test computes these values from the sample endpoints, independently of the code. It also checks that every band integral is positive, which rejects a sign error.

**How we know the right answer.** The integral of 1 over an interval is the length of the interval. A dropped bin width or a wrong wavelength unit changes the integral by far more than the `rtol=1e-12` tolerance.

**Why it matters.** With the Spada tracks, PROTEUS calls `CalcBandFluxes` on the modern spectrum of the star. In MORS, `FitModernProperties` in `mors.synthesis` calls it too.

**Known limit.** For a constant integrand every way of summing the samples (rectangles or trapezoids) gives the same total, so this case does not test the summation weights. The sample points stay away from the band edges, so a band limit that moves without crossing a sample point also passes.

??? info "Test details"
    - Reference: closed form: the span between the first and last sample point in each band
    - Tolerance: `rtol=1e-12` on each band and the bolometric integral
    - Test id: `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`
    - Command: `pytest tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`

## Related code

- `src/mors/spectrum.py`: band-limit table `bands_limits`, `PlanckFunction_surf`, `ScaleToSurf` / `ScaleTo1AU`, and the `Spectrum` loader and band integrator.
- `tests/test_spectrum.py`: companion tests of the flux scaling between the stellar surface and 1 AU (`test_scale_surface_to_1au_roundtrip`), of the Planck surface flux rising with temperature (`test_planck_surface_flux_increases_with_temperature`), and of the sorted wavelengths with a positive flux floor (`test_Spectrum_LoadDirectly_sanitizes_and_orders`).
