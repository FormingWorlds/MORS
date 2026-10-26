# Validation: `src/mors/star.py`

## What this page checks

This page checks the high-level `Star` model class in `mors.star`.
The class links the Spada et al. (2013) stellar tracks with rotational spin-down and magnetic activity models.
`Star.Value(age, key)` returns stellar quantities from the stored tracks: `Lbol` in erg/s and `Rstar` in solar radii. The conversion of `Lbol` from solar luminosities to erg/s happens in `physicalmodel.py`, when the tracks are built.
Activity keys such as `Leuv` depend on the rotation history that the chosen time integrator produces.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, PROTEUS receives wrong stellar luminosities and high-energy fluxes.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Solar luminosity at the solar age

**Why this check exists.** The bolometric luminosity of a `Star` goes from the solar-luminosity units of the stellar tracks (the tabulated evolution of a star of given mass) to erg/s. A wrong mass track or a dropped conversion factor (about 4e33) gives a large luminosity error without an error message.

**What it tests.** The test evaluates a 1 Msun star at the solar age of 4.57 Gyr and asserts that the bolometric luminosity matches the IAU nominal solar luminosity within 15%. It also applies a guard asserting that the luminosity of a 0.3 Msun star is below 0.1 of the 1 Msun value. Companion tests compare `Star.Value` with stored earlier outputs for both time integrators (`test_star_value_default_integrator`, `test_star_value_forward_euler_integrator`) and check that the radius, the bolometric luminosity and the EUV luminosity are positive.

**How we know the right answer.** The Spada et al. (2013) models are solar-calibrated, and the IAU 2015 Resolution B3 defines the nominal solar luminosity as 3.828e33 erg/s. The solar-mass track at 4.57 Gyr reproduces this benchmark to roughly 10%, inside the `rtol=0.15` band. A 0.3 Msun star is more than 10 times fainter than the Sun, so a test that read the wrong mass track, or dropped the conversion to erg/s, would fail clearly.

**Why it matters.** PROTEUS calls `Star.Value` in its stellar step for the bolometric luminosity, the radius and the X-ray and EUV luminosities. From them it computes the instellation and the XUV flux at the planet.

??? info "Test details"
    - Reference: Spada et al. (2013) [^cite-spada2013] tracks; IAU 2015 Resolution B3 nominal solar luminosity 3.828e33 erg/s
    - Tolerance: `rtol=0.15` on Lbol in erg/s; the Lbol of a 0.3 Msun star must be below 0.1 of the 1 Msun value
    - Test id: `tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age`
    - Command: `pytest tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age` (needs `FWL_DATA` with the tracks)

## Related code

- `src/mors/star.py`: the `Star` class and `Star.Value`.
- `src/mors/physicalmodel.py`: the conversion of `Lbol` to erg/s (`StarEvo.Lbol(...) * const.LbolSun`).
- `src/mors/stellarevo.py`: supplies the underlying stellar tracks; see [stellarevo.md](stellarevo.md).
- `tests/test_star.py`: `test_star_reproduces_solar_luminosity_at_solar_age` and companion tests.

## References

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
