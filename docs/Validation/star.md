# Validation: `src/mors/star.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.star` against a published source.

| Test id | Reference | Source page | Scope |
|---|---|---|---|
| `tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age` | Spada et al. (2013) [^cite-spada2013] solar-calibrated tracks; IAU 2015 Resolution B3 nominal solar luminosity | [2013ApJ...776...87S](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract) | Checks that a 1 Msun star at the solar age (4.57 Gyr) reproduces the nominal solar luminosity in erg/s to within 15%, validating both the track calibration and the internal Lsun-to-erg/s conversion, with a 0.3 Msun discrimination guard. |

## Re-derivation note

The `Star` class couples the Spada et al. (2013) stellar-structure tracks with a
rotation-and-activity model and exposes `Star.Value(age, key)`. Structural keys
(`Rstar`, `Lbol`) are returned in cgs units: `Lbol` in erg/s, converted from the
tracks' native solar-luminosity units by multiplying by the nominal solar
luminosity. Activity keys (`Leuv`) depend on the rotation history the chosen
time integrator produces.

The Spada et al. (2013) models are solar-calibrated: a 1 Msun star at the solar
age reproduces the Sun. In this implementation the solar-mass track at 4.57 Gyr
returns a bolometric luminosity within roughly 10% of the IAU nominal
`L_sun = 3.828e33 erg/s`. Pinning against that nominal value tests two things
at once: that the track calibration is correct, and that the solar-luminosity
to erg/s unit conversion inside `Star.Value` is applied with the right constant
and exponent.

Scale: a 0.3 Msun main-sequence star is more than a factor of ten fainter than
the Sun, far outside the 15% tolerance, so a regression that read the wrong
mass track or dropped the cgs conversion (a factor of `~4e33`) would fail
loudly. The discrimination guard asserts the 0.3 Msun luminosity is below one
tenth of the solar-mass value.

## Anchor type

Published benchmark. The Spada et al. (2013) solar-calibrated tracks and the
IAU nominal solar luminosity are the benchmark. Companion `physics_invariant`
tests pin `Star.Value` against the model output for both time-integration
methods (`test_star_value_default_integrator`,
`test_star_value_forward_euler_integrator`) and assert positivity of the
radius, bolometric luminosity, and EUV luminosity.

## Cross-references

- `src/mors/star.py`: the `Star` class, `Star.Value`, and the cgs unit
  conversions applied to the track output.
- `src/mors/stellarevo.py`: supplies the underlying structural interpolation;
  see `docs/Validation/stellarevo.md`.
- PROTEUS reads `Star.Value` for the stellar luminosity and EUV history during
  the stellar-evolution step.

## References

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
