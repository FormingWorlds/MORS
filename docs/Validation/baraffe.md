# Validation: `src/mors/baraffe.py`

## What this page checks

This page checks how MORS reads and interpolates the stellar-evolution tracks of Baraffe et al. (2015).
`BaraffeTrack` in `mors.baraffe` supplies the bolometric luminosity, stellar radius, and orbital insolation as functions of stellar mass and age.
Validation means that a test runs the code on a reference case with known outputs, and checks the result within a stated tolerance.
The pinned values are the output of the interpolation of the Baraffe et al. (2015) tracks, so this is a regression pin.
If this part of the code is wrong, PROTEUS receives the wrong stellar luminosity and radius when the Baraffe tracks are selected.
The atmospheric evolution and planetary climate in coupled runs are then wrong.

## Baraffe track values

**Why this check exists.** The interpolation can select the wrong track file, misplace the age index, or return a mass-independent value, without a warning. A broken lookup could also flip a sign or return zero without an error message.

**What it tests.** `mors.BaraffeTrack` reads the Baraffe et al. (2015) evolutionary tracks from `FWL_DATA` for a given stellar mass. It interpolates bolometric luminosity $L$, stellar radius $R$, and derived orbital insolation $S$ as functions of age. The test evaluates two stellar masses, 0.047 and 1.113 Msun, spanning a factor of roughly 24 in mass. A positivity guard checks that each returned quantity is strictly positive. A companion `physics_invariant` test (`test_baraffe_luminosity_increases_with_mass`) checks the monotone increase of luminosity with mass at fixed age.

**How we know the right answer.** The pinned values are the output of the code interpolation of the Baraffe et al. (2015) tracks. At a common age, the interpolated luminosity of the 1.113 Msun track lies more than two orders of magnitude above the 0.047 Msun track. A regression that selects the wrong track index or returns a mass-independent value, moves the result far outside the `rtol=1e-5` tolerance.

**Why it matters.** PROTEUS consumes the Baraffe luminosity and insolation through the MORS stellar-evolution step when the Baraffe track set is selected.

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
