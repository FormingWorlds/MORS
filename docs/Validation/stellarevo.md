# Validation: `src/mors/stellarevo.py`

## What this page checks

This page checks how MORS interpolates and manages the stellar-structure tracks of Spada et al. (2013).
`StarEvo` in `mors.stellarevo` reads stellar evolutionary models and interpolates bolometric luminosity, stellar radius, and effective temperature as functions of stellar mass and age.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, every stellar luminosity, radius and temperature of MORS is wrong, and so are the values that PROTEUS reads.
Each case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends each case.

## Solar calibration

**Why this check exists.** The interpolation can read the wrong track, use the wrong age unit (the code expects Myr), or rescale the native units without an error message. Because the main-sequence mass-luminosity relation is steep, a wrong track index shifts luminosity by orders of magnitude.

**What it tests.** `stellarevo.Value(Mstar, Age, key)` reads the Spada et al. (2013) grid (24 mass bins from 0.1 to 1.25 Msun, loaded from `FWL_DATA`) and returns structural quantities by bilinear interpolation in mass and log-age. The Spada et al. (2013) models are solar-calibrated. At the solar age of 4.57 Gyr, the interpolated 1 Msun track returns roughly 1.08 Lsun, 1.015 Rsun, and 5844 K, agreeing to about 10% with solar reference values (unity in normalized luminosity and radius, 5772 K in effective temperature). The test asserts that L lands inside 0.15 Lsun of unity, R lands inside 0.05 Rsun of unity, and Teff deviates by under 3% from 5772 K. A companion test (`test_stellarevo_luminosity_increases_with_mass`) samples masses from 0.3 to 1.2 Msun and asserts strict monotonic increase, with the lightest and heaviest tracks separated by more than two orders of magnitude.

**How we know the right answer.** The Spada et al. (2013) tracks are solar-calibrated, so a 1 Msun star at the solar age must reproduce the Sun: unity in luminosity and radius in solar units, and the standard solar effective temperature of 5772 K. The companion test adds an independent check on the mass ordering of the tracks.

**Why it matters.** `physicalmodel`, `rotevo` and `star` take the stellar structure from a `StarEvo` grid, and `synthesis` calls `Value` and `Lbol`.

![1 Msun Spada track of L, R and Teff against age, with the Sun and the tolerance at the solar age](../assets/validation/stellarevo_solar_calibration.svg#only-light){ width="80%" }
![1 Msun Spada track of L, R and Teff against age, with the Sun and the tolerance at the solar age](../assets/validation/stellarevo_solar_calibration_dark.svg#only-dark){ width="80%" }

Luminosity, radius and effective temperature of the 1 Msun Spada et al. (2013) track between 100 Myr and 8 Gyr (line). The cross is the track value at 4.57 Gyr that the test asserts; the dot with the error bar is the Sun with the tolerance of each assertion.

**How to read the plot.** The horizontal axis shows stellar age in Myr on a logarithmic scale. The three panels display bolometric luminosity in $L_\odot$, stellar radius in $R_\odot$, and effective temperature in K. The solid line tracks the 1 Msun Spada model, the circle with error bar marks the solar reference value and tolerance, and the cross shows the model output at 4.57 Gyr. A pass means the cross falls on the tolerance bar.

??? info "Test details"
    - Reference: Spada et al. (2013) [^cite-spada2013] solar-calibrated tracks; solar effective temperature 5772 K
    - Tolerance: `atol=0.15` Lsun on L, `atol=0.05` Rsun on R, `rtol=0.03` on Teff at 4.57 Gyr
    - Test id: `tests/test_stellarevo.py::test_stellarevo_solar_calibration`
    - Command: `pytest tests/test_stellarevo.py::test_stellarevo_solar_calibration --validation-plots` (needs `FWL_DATA` with the tracks; without `--validation-plots` the test writes no plot)

## Grid compiled from the raw tracks

**Why this check exists.** Reading the raw `.track1` and `.track2` files can go wrong through a wrong column, a dropped conversion from log to linear values, or a wrong age unit. Each of these moves the solar point of the compiled grid without an error message.

**What it tests.** The test compiles the grid from scratch using raw track files in `FWL_DATA`. It checks that the freshly compiled 1 Msun track satisfies the solar calibration at 4.57 Gyr, and verifies that a second construction yields the same `Lbol` and `Teff`.

**How we know the right answer.** The solar calibration of the Spada et al. (2013) tracks, as in the case above, with wider tolerances. A wrong column or unit moves the solar point outside them. The second construction must give the same values to `rtol=1e-12`.

**Why it matters.** MORS compiles the grid from the raw files when no compiled grid exists, so every later run reads what this step wrote.

**Known limit.** The test checks that a second construction matches the first, but does not check that it reads the cache file.

??? info "Test details"
    - Reference: Spada et al. (2013) [^cite-spada2013] raw track files
    - Tolerance: `atol=0.2` Lsun on L and `atol=0.1` Rsun on R at 4.57 Gyr; `Lbol` and `Teff` at 1 Msun and 4.57 Gyr from a second construction agree with `rtol=1e-12` (the test does not check that this construction reads the cache file)
    - Test id: `tests/test_stellarevo.py::test_grid_compiled_from_raw_tracks_matches_saved_grid`
    - Command: `pytest tests/test_stellarevo.py::test_grid_compiled_from_raw_tracks_matches_saved_grid` (needs `FWL_DATA` with the tracks)

## Related code

- `src/mors/stellarevo.py`: `StarEvo`, `Value`, `Lbol`, `Rstar`, `Teff`, and moment-of-inertia wrappers.
- `src/mors/star.py`: converts native track output to cgs units for PROTEUS; see [star.md](star.md).
- `tests/test_stellarevo.py`: `test_stellarevo_solar_calibration` and `test_grid_compiled_from_raw_tracks_matches_saved_grid`.

## References

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776(2), 87, 2013. [ADS](https://ui.adsabs.harvard.edu/abs/2013ApJ...776...87S/abstract).
