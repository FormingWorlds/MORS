# Validation: `src/mors/spectrum.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.spectrum` against an analytical limit.

| Test id | Reference | Source page | Scope |
|---|---|---|---|
| `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand` | Analytical limit: integral of a unit integrand over a band equals the band width | closed form | Feeds a constant unit-flux spectrum and pins each band integral (and the bolometric integral) to the exact band width, so a dropped bin width or a wavelength-unit slip fails against a hand-computed value. |

## Cases

### Band integral of a constant spectrum

- Reference: closed form: the band width
- Tolerance: `rtol=1e-12` on each band and the bolometric integral
- Test id: `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`
- Command: `pytest tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand`

## Re-derivation note

`Spectrum.CalcBandFluxes` integrates the loaded spectrum over each emission
band (`xr`, `e1`, `e2`, `uv`, `pl`) and over the full bolometric range (`bo`).
For an integrand that is identically 1, the integral over a band reduces to the
band width in the integration variable:

```
integral_band 1 dlambda = (lambda_hi - lambda_lo)
```

The test builds a flat spectrum whose sample points are placed inside each band
and away from the band-overlap regions, so every band integral must equal the
difference between its upper and lower sample wavelengths, and the bolometric
integral must equal the full sampled span. The expected values are computed
directly from the sample endpoints, independent of the implementation.

Scale: a regression that drops the bin width or measures the grid in the wrong
wavelength unit changes the integral by more than the `rtol=1e-12` tolerance.
For a constant integrand every Riemann sum gives the same total, so this case
does not separate trapezoidal from rectangular weights. The sample points stay
away from the band edges, so a band limit that moves without crossing a sample
point also passes. A positivity guard on every band integral additionally
rejects a sign error.

## Anchor type

Analytical limit. The constant-integrand band integral is a closed-form
identity. Companion `physics_invariant` tests cover the flux-scaling symmetry
(`test_scale_surface_to_1au_roundtrip`), the Planck surface-flux monotonicity
with temperature (`test_planck_surface_flux_increases_with_temperature`), and
the sanitised wavelength ordering with its positive flux floor
(`test_Spectrum_LoadDirectly_sanitizes_and_orders`).

## Cross-references

- `src/mors/spectrum.py`: band-limit table `bands_limits`, `PlanckFunction_surf`,
  `ScaleToSurf` / `ScaleTo1AU`, and the `Spectrum` loader and band integrator.
- PROTEUS consumes the band-integrated stellar fluxes through the MORS
  stellar-evolution step to drive atmospheric heating and escape.
