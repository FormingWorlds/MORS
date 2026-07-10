# Validation: `src/mors/synthesis.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.synthesis` against a self-consistency identity.

| Test id | Reference | Source page | Scope |
|---|---|---|---|
| `tests/test_synthesis.py::test_GetProperties_flux_budget` | Self-consistency: the band fluxes sum to the bolometric flux | closed form | Pins the band luminosities and fluxes returned by `GetProperties` against a hand-computed budget and asserts the five sub-band fluxes sum exactly to the bolometric flux, because the UV band is defined as the bolometric remainder. |

## Re-derivation note

`synthesis.GetProperties` builds the stellar high-energy budget from the
stellar model: the bolometric luminosity from `Lbol`, the X-ray and EUV
luminosities from `Lxuv`, and the photospheric (`pl`) band from a Planck
integral. The UV band is not measured independently; it is defined as the
bolometric flux minus the X-ray, EUV, and photospheric contributions:

```
F_uv = F_bo - F_xr - F_e1 - F_e2 - F_pl
```

By construction this makes the five sub-band fluxes sum to the bolometric flux
exactly. The test mocks the stellar-model inputs (`Value`, `Percentile`,
`Lxuv`, `Lbol`) and the Planck surface flux with physically plausible constants,
recomputes the expected per-band fluxes and luminosities from the same physical
constants the source uses (`AU`, `LbolSun`), and pins the result. The final
assertion checks the closure `sum(sub-bands) == F_bo` directly.

Scale: a regression that drops a band from the remainder, or that double-counts
a contribution, breaks the closure by more than the `rtol=1e-12` tolerance.

## Anchor type

Self-consistency / conservation closure. The band budget is an internal
identity rather than an external benchmark, so the anchor is the exact
closure of the flux budget. Companion `physics_invariant` tests cover the
constant-Planck band integral (`test_GetProperties_planck_trapezoid_constant`),
the positivity of the band-scale factors (`test_CalcBandScales`), and the
per-band flux rescaling that preserves the wavelength grid
(`test_CalcScaledSpectrumFromProps_scales_by_first_band`).

## Cross-references

- `src/mors/synthesis.py`: `GetProperties`, `CalcBandScales`,
  `CalcScaledSpectrumFromProps`, and `FitModernProperties`.
- `src/mors/spectrum.py`: supplies the band limits and the Planck surface flux
  that the synthesis budget integrates.
