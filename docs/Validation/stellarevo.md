# Validation: `src/mors/stellarevo.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.stellarevo` against a published source.

| Test id | Reference | Source page | Scope |
|---|---|---|---|
| `tests/test_stellarevo.py::test_stellarevo_solar_calibration` | Spada et al. (2013) [^cite-spada2013] solar-calibrated tracks; solar effective temperature 5772 K | [2013ApJ...776...87S](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract) | Checks that the interpolated 1 Msun track at the solar age (4.57 Gyr) returns L within 0.15 Lsun of unity, R within 0.05 Rsun of unity, and Teff within 3% of 5772 K, in the tracks' native units. |

## Re-derivation note

`stellarevo.Value(Mstar, Age, key)` reads the Spada et al. (2013) grid
(24 mass bins from 0.1 to 1.25 Msun, loaded from `FWL_DATA`) and returns
structural quantities by bilinear interpolation in mass and log-age. The native
units are solar luminosities for `Lbol`, solar radii for `Rstar`, and Kelvin for
`Teff`.

The Spada et al. (2013) models are solar-calibrated, so a 1 Msun star at the
solar age reproduces the Sun. In this grid the solar-mass track at 4.57 Gyr
returns roughly 1.08 Lsun, 1.02 Rsun, and 5844 K, all within about 10% of the
solar reference values (unity in the normalised luminosity and radius, 5772 K
in effective temperature). Pinning the interpolation output at the solar point
tests that the correct track is read, that the age unit is Myr, and that the
native units are not accidentally rescaled.

Scale: the mass-luminosity relation on the main sequence is steep, so a wrong
track index moves the luminosity by orders of magnitude. The companion
`physics_invariant` test `test_stellarevo_luminosity_increases_with_mass`
samples masses from 0.3 to 1.2 Msun and asserts a strict monotone increase, with
the lightest and heaviest tracks separated by more than two orders of magnitude.

## Anchor type

Published benchmark. The Spada et al. (2013) solar-calibrated tracks and the
standard solar effective temperature are the benchmark; the solar-calibration
point is the analytical anchor and the mass-luminosity monotonicity is the
property-based second-line check.

## Cross-references

- `src/mors/stellarevo.py`: `Value` and the per-quantity wrappers `Rstar`,
  `Lbol`, `Teff`, and the moment-of-inertia terms.
- `src/mors/star.py`: converts the native track output to cgs units for
  PROTEUS; see `docs/Validation/star.md`.

## References

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776(2), 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
