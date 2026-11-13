# Validation

## What this page checks

Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
Each physics source file of MORS has at least one such `reference_pinned` test. It compares the output with a published benchmark, an analytical limit or a self-consistency identity, or, as a regression pin, with a stored output of the same code.
The pages of this tab list these cases, one page per source file, grouped by physical process.
Each case says why the check exists, what it tests, how we know the right answer and why it matters. A box "Test details" gives its reference, its tolerance, its test id and the command that runs it.
Tests in the `unit` tier run on every pull request, with track lookups mocked.
Tests in the `integration` tier read the Baraffe et al. (2015)[^cite-baraffe2015] and Spada et al. (2013)[^cite-spada2013] tracks from `FWL_DATA`, and run in nightly workflows.
See [Testing](../How-to/run_tests.md) for test tiers and execution commands.

## Cases by process

| Process | Case | Test id | Reference | Status |
|---|---|---|---|---|
| [Stellar evolution tracks](stellarevo.md) | Solar calibration | `tests/test_stellarevo.py::test_stellarevo_solar_calibration` | Spada et al. (2013) solar-calibrated tracks | integration tier; plot pair |
| [Stellar evolution tracks](stellarevo.md) | Grid compiled from the raw tracks | `tests/test_stellarevo.py::test_grid_compiled_from_raw_tracks_matches_saved_grid` | Spada et al. (2013) raw track files | integration tier; plot pair |
| [Star model](star.md) | Solar luminosity at the solar age | `tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age` | Spada et al. (2013); IAU 2015 nominal solar luminosity | integration tier; plot pair |
| [Baraffe tracks](baraffe.md) | Baraffe track values | `tests/test_baraffe.py::test_baraffe_track_matches_published_values` | regression pin of the interpolation of the Baraffe et al. (2015) tracks | integration tier; plot pair |
| [Rotation evolution](rotevo.md) | Forward-Euler step | `tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update` | closed form | unit tier; plot pair |
| [Activity and habitable zone](physicalmodel.md) | Saturated X-ray ratio | `tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value` | Johnstone et al. (2021)[^cite-johnstone2021] | unit tier; plot pair |
| [Activity and habitable zone](physicalmodel.md) | Runaway greenhouse limit, solar analogue | `tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit` | Kopparapu et al. (2013b)[^cite-kopparapu2013b], Table 3 | unit tier; plot pair |
| [Activity and habitable zone](physicalmodel.md) | Runaway greenhouse limit, cool star | `tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star` | Kopparapu et al. (2013b), Table 3 | unit tier; plot pair |
| [Spectrum](spectrum.md) | Band integral of a constant spectrum | `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand` | closed form | unit tier; plot pair |
| [Spectral synthesis](synthesis.md) | Flux budget closure | `tests/test_synthesis.py::test_GetProperties_flux_budget` | self-consistency | unit tier; plot pair |
| [Cluster percentiles](cluster.md) | Percentile of a uniform ramp | `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form` | closed form | unit tier; plot pair |

## Plots written by the tests

A case with a plot pair shows the tested values against their reference, in a light and a dark version. The test writes the pair with the same numbers it asserts, through the `validation_plot` fixture of proteus-mpl. This command writes all pairs to `docs/assets/validation/`:

```console
pytest -m reference_pinned tests --validation-plots
```

Without `--validation-plots` the tests write nothing: each compares the data of its plot with the committed pair, and a missing or stale file fails the test. The integration cases need `FWL_DATA` with the evolution tracks.

[^cite-baraffe2015]: I. Baraffe, D. Homeier, F. Allard, G. Chabrier, *[New evolutionary models for pre-main sequence and main sequence low-mass stars down to the hydrogen-burning limit](https://doi.org/10.1051/0004-6361/201425481)*, Astronomy & Astrophysics, 577, A42, 2015. [SciX](https://scixplorer.org/abs/2015A%26A...577A..42B/abstract).

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The Radius Discrepancy in Low-mass Stars: Single versus Binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...776...87S/abstract).

[^cite-johnstone2021]: C. P. Johnstone, M. Bartel, M. Güdel, *[The active lives of stars: A complete description of the rotation and XUV evolution of F, G, K, and M dwarfs](https://doi.org/10.1051/0004-6361/202038407)*, Astronomy & Astrophysics, 649, A96, 2021. [SciX](https://scixplorer.org/abs/2021A%26A...649A..96J/abstract).

[^cite-kopparapu2013b]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, V. Eymet, T. D. Robinson, S. Mahadevan, R. C. Terrien, S. Domagal-Goldman, V. Meadows, R. Deshpande, *[Erratum: "Habitable Zones around Main-sequence Stars: New Estimates" (2013, ApJ, 765, 131)](https://doi.org/10.1088/0004-637X/770/1/82)*, The Astrophysical Journal, 770, 82, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...770...82K/abstract).
