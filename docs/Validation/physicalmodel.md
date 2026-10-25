# Validation: `src/mors/physicalmodel.py`

## What this page checks

This page checks the high-energy emission and habitable-zone relations in `mors.physicalmodel`.
The module calculates stellar magnetic activity, X-ray and EUV luminosities, and planetary insolation boundaries.
Validation means that a test runs the code on published benchmarks and checks the results to stated tolerances.
If this part of the code is wrong, stellar high-energy fluxes and habitable-zone boundaries are computed incorrectly.
Atmospheric escape rates and climate assessments in coupled planetary models are then wrong.
The cases below cover the saturated X-ray ratio and the runaway greenhouse limits for solar analogues and cool stars.

## Saturated X-ray ratio

**Why this check exists.** The X-ray activity relation is a broken power law in Rossby number with a saturated branch for fast rotators. A regression in the saturation constant, or in branch dispatch, shifts stellar X-ray luminosity without an error message.

**What it tests.** At the saturation Rossby number, the broken power law branches meet. The test evaluates the relation at this threshold, and checks the saturated X-ray-to-bolometric ratio `Rx_sat = 5.135e-4`. It asserts positivity, verifies that surface flux matches luminosity divided by area, and checks that companion points on each side follow the branch dispatch. Companion `physics_invariant` tests confirm positivity of emission quantities, band conservation `Lxuv = Lx + Leuv`, torque antisymmetry, and saturation monotonicity.

**How we know the right answer.** Johnstone et al. (2020) calibrate the saturated ratio `Rx_sat = 5.135e-4` using the Spada et al. (2013) models. The value is a published benchmark pinned to `rtol=1e-6`.

**Why it matters.** `mors.physicalmodel.Lxuv` uses this ratio to compute high-energy fluxes for fast rotators. PROTEUS reads these fluxes to drive atmospheric photoevaporation and escape models.

??? info "Test details"
    - Reference: Johnstone et al. (2020) saturated `Rx_sat = 5.135e-4`, calibrated on the Spada et al. (2013) [^cite-spada2013] models
    - Tolerance: `rtol=1e-6`
    - Test id: `tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value`
    - Command: `pytest tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value`

## Runaway greenhouse limit, solar analogue

**Why this check exists.** Habitable-zone boundaries depend on effective stellar flux polynomial coefficients. A misplaced coefficient or sign error shifts the boundary distance, misleading insolation calculations.

**What it tests.** The runaway-greenhouse boundary distance is `aOrb = (Lbol / Seff)**0.5`. Effective stellar flux follows `Seff = Seff_sun + a*T + b*T**2 + c*T**3 + d*T**4` with `T = Teff - 5780`. For a solar analogue with `T = 0`, `Seff = Seff_sun = 1.0385`. At one solar luminosity, this places the boundary at `(1 / 1.0385)**0.5`, giving about 0.98 AU. The test asserts this boundary, while a companion test verifies the ordering of the five habitable-zone boundaries from Recent Venus to Early Mars.

**How we know the right answer.** Kopparapu et al. (2013) Table 3 gives `Seff = 1.0385` for the solar runaway-greenhouse flux. The test pins this published benchmark to `rtol=1e-6`.

**Why it matters.** `mors.physicalmodel.aOrbHZ` provides habitable-zone boundary metrics for coupled planet evolution models.

??? info "Test details"
    - Reference: Kopparapu et al. (2013) [^cite-kopparapu2013], Table 3, `Seff = 1.0385`
    - Tolerance: `rtol=1e-6`
    - Test id: `tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit`
    - Command: `pytest tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit`

## Runaway greenhouse limit, cool star

**Why this check exists.** The solar analogue case evaluates the polynomial at `T = 0`, where higher-order terms vanish. A defect in the temperature-dependent coefficients or exponents is invisible for a solar star, but shifts habitable-zone boundaries for cool stars.

**What it tests.** At `Teff = 4000` K and `Lbol = 0.1` Lsun, all temperature terms of the `Seff` quartic polynomial are non-zero. The test pins the boundary distance against the analytical polynomial evaluation. It verifies that a linear cubic term misses by more than 2%.

**How we know the right answer.** Kopparapu et al. (2013) Table 3 defines the full temperature polynomial coefficients. The test asserts agreement to `rtol=1e-9`.

**Why it matters.** Many planetary targets orbit cool stars, so accurate temperature scaling of insolation limits is essential for habitable-zone calculations.

??? info "Test details"
    - Reference: Kopparapu et al. (2013) [^cite-kopparapu2013], Table 3 polynomial at Teff = 4000 K
    - Tolerance: `rtol=1e-9`; a linear cubic term must miss by more than 2%
    - Test id: `tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star`
    - Command: `pytest tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star`

## Related code

- `src/mors/physicalmodel.py`: `Lxuv`, `Lx`, `Leuv`, the Rossby and torque helpers, and `aOrbHZ`.
- [High-energy emission and activity](../Explanations/activity.md) and [Habitable zone boundaries](../Explanations/habitablezone.md) describe the full relations and carry the complete reference list.

## References

[^cite-kopparapu2013]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, et al., *[Habitable zones around main-sequence stars: new estimates](https://doi.org/10.1088/0004-637X/765/2/131)*, The Astrophysical Journal, 765, 131, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...765..131K/abstract).
[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
