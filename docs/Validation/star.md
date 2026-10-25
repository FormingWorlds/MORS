# Validation: `src/mors/star.py`

## What this page checks

This page checks the high-level `Star` model class in `mors.star`.
The class links the Spada et al. (2013) stellar tracks with rotational spin-down and magnetic activity models.
`Star.Value` provides bolometric luminosity, stellar radius, and high-energy fluxes in cgs units.
We test the coupled star model against a published solar benchmark, and check that outputs match the stated tolerance.
If this part of the code fails, PROTEUS receives incorrect stellar luminosities and high-energy fluxes during planetary runs.

## Solar luminosity at the solar age

**Why this check exists.** `Star.Value` scales bolometric luminosity from native track units ($L_\odot$) into cgs units (erg/s) using the nominal solar luminosity. A bug that selects the wrong mass track, drops the scale factor (about 4e33), or uses an incorrect exponent causes large flux errors.

**What it tests.** The test evaluates a 1 Msun star at the solar age of 4.57 Gyr and asserts that the bolometric luminosity matches the IAU nominal solar luminosity within 15%. It also applies a guard asserting that the luminosity of a 0.3 Msun star is below 0.1 of the 1 Msun value. Companion `physics_invariant` tests check that stellar radius, bolometric luminosity, and EUV luminosity stay positive for both forward-Euler and default solvers.

**How we know the right answer.** The Spada et al. (2013) models are solar-calibrated, and the IAU 2015 Resolution B3 defines the nominal solar luminosity as 3.828e33 erg/s. The solar-mass track at 4.57 Gyr reproduces this benchmark to roughly 10%, inside the `rtol=0.15` band. A 0.3 Msun star is more than a factor of ten fainter, ruling out track-index errors.

**Why it matters.** PROTEUS calls `Star.Value` during each stellar step to obtain bolometric luminosity, radius, and EUV histories. These quantities drive planetary surface climate and atmospheric escape.

??? info "Test details"
    - Reference: Spada et al. (2013) [^cite-spada2013] tracks; IAU 2015 Resolution B3 nominal solar luminosity 3.828e33 erg/s
    - Tolerance: `rtol=0.15` on Lbol in erg/s; the Lbol of a 0.3 Msun star must be below 0.1 of the 1 Msun value
    - Test id: `tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age`
    - Command: `pytest tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age` (needs `FWL_DATA` with the tracks)

## Related code

- `src/mors/star.py`: the `Star` class, `Star.Value`, and the cgs unit scaling applied to track outputs.
- `src/mors/stellarevo.py`: supplies the underlying stellar tracks; see [stellarevo.md](stellarevo.md).
- `tests/test_star.py`: `test_star_reproduces_solar_luminosity_at_solar_age` and companion tests.

## References

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
