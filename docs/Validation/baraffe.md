# Validation: `src/mors/baraffe.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.baraffe` against a published source.

| Test id | Reference | Source page | Scope |
|---|---|---|---|
| `tests/test_baraffe.py::test_baraffe_track_matches_published_values` | Baraffe et al. (2015) [^cite-baraffe2015], A&A 577, A42 | [2015A&A...577A..42B](https://ui.adsabs.harvard.edu/abs/2015A%26A...577A..42B/abstract) | Pins the interpolated luminosity, stellar radius, and orbital insolation at two stellar masses (0.047 and 1.113 Msun) against the Baraffe et al. (2015) evolutionary tracks, and asserts each returned quantity is strictly positive. |

## Re-derivation note

`mors.BaraffeTrack` reads the Baraffe et al. (2015) evolutionary tracks
(downloaded to `FWL_DATA`) for a given stellar mass and interpolates the
bolometric luminosity, stellar radius, and derived orbital insolation as a
function of age. The pinned values are the interpolation output for the two
tabulated masses at the ages listed in the test data.

The two masses span a factor of roughly 24 in stellar mass. At a common age
the interpolated luminosity of the 1.113 Msun track lies more than two orders
of magnitude above the 0.047 Msun track, so a regression that selects the
wrong track index, or that returns a mass-independent value, moves the result
far outside the `rtol=1e-5` tolerance.

## Anchor type

Published benchmark. The Baraffe et al. (2015) tracks are the benchmark; the
pinned test is accompanied by a positivity guard, and a companion
`physics_invariant` test (`test_baraffe_luminosity_increases_with_mass`)
asserts the monotone increase of luminosity with mass at fixed age as the
property-based second-line check.

## Cross-references

- `src/mors/baraffe.py`: loads and interpolates the Baraffe et al. (2015) tracks.
- PROTEUS consumes the Baraffe luminosity and insolation through the MORS
  stellar-evolution step when the Baraffe track set is selected.

## References

[^cite-baraffe2015]: I. Baraffe, D. Homeier, F. Allard, G. Chabrier, *[New evolutionary models for pre-main sequence and main sequence low-mass stars down to the hydrogen-burning limit](https://doi.org/10.1051/0004-6361/201425481)*, Astronomy & Astrophysics, 577, A42, 2015. [ADS](https://ui.adsabs.harvard.edu/abs/2015A%26A...577A..42B/abstract).
