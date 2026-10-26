# Validation: `src/mors/physicalmodel.py`

## What this page checks

This page checks 2 relations of `mors.physicalmodel`: the X-ray activity of a star and the habitable-zone distance.
The module holds the rotation, activity and high-energy emission relations of the stellar model.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, the X-ray luminosity of the star or the habitable-zone distance is wrong.
Each case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends each case.

## Saturated X-ray ratio

**Why this check exists.** The X-ray activity relation is a broken power law in the Rossby number $Ro$ (the rotation period over the convective turnover time), with a saturated branch for fast rotators. A wrong saturated ratio `Rx_sat`, from which the code derives both branch constants, shifts the X-ray luminosity without an error message.

**What it tests.** `Rx` is the ratio of the X-ray to the bolometric luminosity. The code uses the saturated branch `Rx = C1 * Ro**beta1` for `Ro < Ro_sat` and the unsaturated branch `C2 * Ro**beta2` otherwise. `C1`, `C2` are the branch constants and `beta1`, `beta2` the branch exponents. At the saturation Rossby number `Ro_sat` the 2 branches meet. The test evaluates the relation at `Ro = Ro_sat`, where the code takes the unsaturated branch, and checks `Rx_sat = 5.135e-4`. It also checks that `Rx` is positive and between 1e-4 and 1e-3, and that the X-ray surface flux equals the X-ray luminosity over the stellar surface area. A companion test, `test_fast_rotator_emits_more_xrays_than_slow_rotator`, checks that a star at 0.5 `Ro_sat` has more than 5 times the `Rx` of a star at 10 `Ro_sat`. Other tests of the module check that the emission quantities are positive, that `Lxuv = Lx + Leuv`, the antisymmetry of the torques, and the monotonicity of the saturation.

**How we know the right answer.** `Rx_sat = 5.135e-4` is the saturated ratio of Johnstone et al. (2020), calibrated on the Spada et al. (2013) models; it is the value the rotation-activity model uses (see [High-energy emission and activity](../Explanations/activity.md)).

**Why it matters.** `_Xray` gives the X-ray luminosity along every rotation track (`ExtendedQuantities`, which `rotevo` calls). With the Spada tracks, PROTEUS reads `Lx` and `Leuv` through `Star.Value` to compute the XUV flux at the planet, `F_xuv`.

**Known limit.** The code derives `C1` and `C2` from `Rx_sat` and `Ro_sat`, and the test evaluates at `Ro_sat` itself, so a wrong threshold `Ro_sat` or a wrong exponent `beta1` or `beta2` does not fail this test or its companion; only `Rx_sat` is checked.

??? info "Test details"
    - Reference: Johnstone et al. (2020) saturated `Rx_sat = 5.135e-4`, calibrated on the Spada et al. (2013) [^cite-spada2013] models
    - Tolerance: `rtol=1e-6`
    - Test id: `tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value`
    - Command: `pytest tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value`

## Runaway greenhouse limit, solar analogue

**Why this check exists.** The habitable-zone distance comes from a polynomial in the stellar temperature. A wrong solar coefficient or a wrong form of the distance law moves the boundary without an error message.

**What it tests.** The runaway-greenhouse boundary distance is `aOrb = (Lbol / Seff)**0.5`. Effective stellar flux follows `Seff = Seff_sun + a*T + b*T**2 + c*T**3 + d*T**4` with `T = Teff - 5780`. For a solar analogue with `T = 0`, `Seff = Seff_sun = 1.0385`. Here `Seff` is the effective stellar flux in units of the solar flux at the Earth, `Teff` the effective temperature in K and `Lbol` the bolometric luminosity in solar units. At one solar luminosity this places the boundary at `(1 / 1.0385)**0.5`, about 0.98 AU. A companion test checks the ordering of the 5 boundaries from Recent Venus (innermost) to Early Mars (outermost).

**How we know the right answer.** Kopparapu et al. (2013), Table 3, gives `Seff = 1.0385` for the solar runaway-greenhouse limit.

**Why it matters.** `aOrbHZ` gives the habitable-zone distances that `Star` and `Cluster` store, and `mors` exports it for direct use. PROTEUS does not read it.

??? info "Test details"
    - Reference: Kopparapu et al. (2013) [^cite-kopparapu2013], Table 3, `Seff = 1.0385`
    - Tolerance: `rtol=1e-6`
    - Test id: `tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit`
    - Command: `pytest tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit`

## Runaway greenhouse limit, cool star

**Why this check exists.** The solar case evaluates the polynomial at `T = 0`, where every temperature term vanishes. An error in a temperature coefficient or an exponent cannot show there, but it moves the boundary for any other star.

**What it tests.** At `Teff = 4000` K and `Lbol = 0.1` Lsun (solar luminosities), every temperature term of the `Seff` polynomial is non-zero. The test compares the boundary distance with the polynomial evaluated by hand. It also checks that a cubic term entered as a linear term misses by more than 2 %.

**How we know the right answer.** Kopparapu et al. (2013), Table 3, gives all coefficients of the polynomial.

**Why it matters.** `aOrbHZ` gives the habitable-zone distance of every star that is not a solar analogue through these terms.

??? info "Test details"
    - Reference: Kopparapu et al. (2013) [^cite-kopparapu2013], Table 3 polynomial at Teff = 4000 K
    - Tolerance: `rtol=1e-9`; a linear cubic term must miss by more than 2%
    - Test id: `tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star`
    - Command: `pytest tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star`

## Related code

- `src/mors/physicalmodel.py`: `Lxuv`, `Lx`, `Leuv`, the Rossby and torque helpers, and `aOrbHZ`.
- [High-energy emission and activity](../Explanations/activity.md) and [Habitable zone boundaries](../Explanations/habitablezone.md) describe the full relations and give the complete reference list.

## References

[^cite-kopparapu2013]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, et al., *[Habitable zones around main-sequence stars: new estimates](https://doi.org/10.1088/0004-637X/765/2/131)*, The Astrophysical Journal, 765(2), 131, 2013.

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776(2), 87, 2013.
