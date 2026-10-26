# Validation: `src/mors/baraffe.py`

## What this page checks

This page checks how MORS reads and interpolates the stellar-evolution tracks of Baraffe et al. (2015).
`BaraffeTrack` in `mors.baraffe` gives the bolometric luminosity, the stellar radius and the orbital insolation as functions of stellar mass and age.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
Here the right answer is a stored output of the same interpolation (a regression pin): the test catches any change of the output, not an error that was there from the start.
If this part of the code changes, PROTEUS receives a different stellar luminosity and radius when the Baraffe tracks are selected.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Baraffe track values

**Why this check exists.** A change in the interpolation can select the wrong track, shift the age index, or return a value that does not depend on mass, without an error message.

**What it tests.** `mors.BaraffeTrack` reads the Baraffe et al. (2015) evolutionary tracks from the data directory `FWL_DATA` for a given stellar mass. It interpolates bolometric luminosity $L$, stellar radius $R$, and derived orbital insolation $S$ (W/m$^2$) as functions of age. The test evaluates 2 tabulated stellar masses, 0.047 and 1.113 Msun (solar masses), a factor of roughly 24 apart: the first at 8.5e7 yr and 0.75 AU, the second at 3.2e9 yr and 1.05 AU. It also checks that each returned quantity is positive. A companion test, `test_baraffe_luminosity_increases_with_mass`, checks that the heavier star at 3.2 Gyr is more than 100 times as luminous as the lighter one. The 0.047 Msun track ends at 0.71 Gyr, so the code clips the lighter star to that age.

**How we know the right answer.** There is no outside reference: the stored values are an earlier output of the same interpolation of the Baraffe et al. (2015) tracks (the tabulated evolution of stars of given mass). In the companion test the 2 luminosities differ by more than 100 times. A change that selects the wrong track index or returns a mass-independent value moves the result far outside the `rtol=1e-5` tolerance.

**Why it matters.** PROTEUS uses the Baraffe luminosity, stellar radius, insolation and effective temperature when the Baraffe track set is selected.

![Luminosity and radius of the 0.047 Msun Baraffe track against age, with the pinned values](../assets/validation/mors_baraffe_0p047.svg#only-light){ width="80%" }
![Luminosity and radius of the 0.047 Msun Baraffe track against age, with the pinned values](../assets/validation/mors_baraffe_0p047_dark.svg#only-dark){ width="80%" }

![Luminosity and radius of the 1.113 Msun Baraffe track against age, with the pinned values](../assets/validation/mors_baraffe_1p113.svg#only-light){ width="80%" }
![Luminosity and radius of the 1.113 Msun Baraffe track against age, with the pinned values](../assets/validation/mors_baraffe_1p113_dark.svg#only-dark){ width="80%" }

**How to read the plot.** There is one plot for each of the 2 cases of the test: 0.047 Msun at 85 Myr and 1.113 Msun at 3.2 Gyr. The lines are `BaraffeLuminosity` and `BaraffeStellarRadius` of the track over its ages and give context. The test asserts the code values (circles) against the pinned values (squares) to a relative 1e-5, too small to see. It also asserts the solar constant of each case, which the plot does not draw. A pass means that each circle sits in its square.

**Known limit.** The stored values are not compared with the published tables of Baraffe et al. (2015), despite the word `published_values` in the test id. The effective temperature (`BaraffeStellarTeff`) has no stored value.

??? info "Test details"
    - Reference: the code's own interpolation of the Baraffe et al. (2015) [^cite-baraffe2015] tracks (regression pin; the values are not compared with the published tables)
    - Tolerance: `rtol=1e-5` on luminosity, radius and insolation at 0.047 and 1.113 Msun
    - Test id: `tests/test_baraffe.py::test_baraffe_track_matches_published_values`
    - Command: `pytest tests/test_baraffe.py::test_baraffe_track_matches_published_values` (needs `FWL_DATA` with the tracks)

## Related code

- `src/mors/baraffe.py`: loads and interpolates the Baraffe et al. (2015) tracks.
- `tests/test_baraffe.py`: `test_baraffe_track_matches_published_values` and `test_baraffe_luminosity_increases_with_mass`.

## References

[^cite-baraffe2015]: I. Baraffe, D. Homeier, F. Allard, G. Chabrier, *[New evolutionary models for pre-main sequence and main sequence low-mass stars down to the hydrogen-burning limit](https://doi.org/10.1051/0004-6361/201425481)*, Astronomy & Astrophysics, 577, A42, 2015. [ADS](https://ui.adsabs.harvard.edu/abs/2015A%26A...577A..42B/abstract).
