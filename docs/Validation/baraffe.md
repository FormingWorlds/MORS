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

**What it tests.** `mors.BaraffeTrack` reads the Baraffe et al. (2015) evolutionary tracks from `FWL_DATA` for a given stellar mass. It interpolates bolometric luminosity $L$, stellar radius $R$, and derived orbital insolation $S$ as functions of age. The test evaluates 2 tabulated stellar masses, 0.047 and 1.113 Msun (solar masses), a factor of roughly 24 apart, at the ages listed in the test data. It also checks that each returned quantity is positive. A companion test, `test_baraffe_luminosity_increases_with_mass`, checks that the luminosity rises with mass at fixed age.

**How we know the right answer.** The pinned values are the output of the code interpolation of the Baraffe et al. (2015) tracks. At a common age, the interpolated luminosity of the 1.113 Msun track lies more than two orders of magnitude above the 0.047 Msun track. A change that selects the wrong track index or returns a mass-independent value moves the result far outside the `rtol=1e-5` tolerance.

**Why it matters.** PROTEUS uses the Baraffe luminosity and stellar radius (`BaraffeLuminosity`, `BaraffeStellarRadius`) when the Baraffe track set is selected.

**Known limit.** The stored values are not compared with the published tables of Baraffe et al. (2015).

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
