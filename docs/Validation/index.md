# Validation

Each physics source of MORS has at least one `reference_pinned` test that compares the code with a published benchmark, an analytical limit or a self-consistency identity, or pins the output of the code as a regression check. The pages of this tab list these cases, one page per source file, grouped by the process they describe. Each case gives its reference, its tolerance, its test id and the command that runs it.

Tests in the `unit` tier run on every pull request with the track lookups mocked. Tests in the `integration` tier read the real Baraffe et al. (2015) and Spada et al. (2013) tracks from `FWL_DATA` and run in the nightly workflow. See [Testing](../How-to/run_tests.md) for the tiers and the commands.

## Cases by process

| Process | Case | Test id | Reference | Status |
|---|---|---|---|---|
| [Stellar evolution tracks](stellarevo.md) | Solar calibration | `tests/test_stellarevo.py::test_stellarevo_solar_calibration` | Spada et al. (2013) solar-calibrated tracks | integration tier; plot pair |
| [Stellar evolution tracks](stellarevo.md) | Grid compiled from the raw tracks | `tests/test_stellarevo.py::test_grid_compiled_from_raw_tracks_matches_saved_grid` | Spada et al. (2013) raw track files | integration tier |
| [Star model](star.md) | Solar luminosity at the solar age | `tests/test_star.py::test_star_reproduces_solar_luminosity_at_solar_age` | Spada et al. (2013); IAU 2015 nominal solar luminosity | integration tier |
| [Baraffe tracks](baraffe.md) | Baraffe track values | `tests/test_baraffe.py::test_baraffe_track_matches_published_values` | regression pin of the interpolation of the Baraffe et al. (2015) tracks | integration tier |
| [Rotation evolution](rotevo.md) | Forward-Euler step | `tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update` | closed form | unit tier |
| [Activity and habitable zone](physicalmodel.md) | Saturated X-ray ratio | `tests/test_physicalmodel.py::TestXrayRegimes::test_saturated_xray_ratio_matches_johnstone_value` | Johnstone et al. (2020) | unit tier |
| [Activity and habitable zone](physicalmodel.md) | Runaway greenhouse limit, solar analogue | `tests/test_physicalmodel.py::TestHabitableZone::test_solar_runaway_greenhouse_limit` | Kopparapu et al. (2013), Table 3 | unit tier |
| [Activity and habitable zone](physicalmodel.md) | Runaway greenhouse limit, cool star | `tests/test_physicalmodel.py::TestHabitableZone::test_runaway_greenhouse_limit_for_a_cool_star` | Kopparapu et al. (2013), Table 3 | unit tier |
| [Spectrum](spectrum.md) | Band integral of a constant spectrum | `tests/test_spectrum.py::test_Spectrum_CalcBandFluxes_constant_integrand` | closed form | unit tier |
| [Spectral synthesis](synthesis.md) | Flux budget closure | `tests/test_synthesis.py::test_GetProperties_flux_budget` | self-consistency | unit tier |
| [Cluster percentiles](cluster.md) | Percentile of a uniform ramp | `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form` | closed form | unit tier |

## Plots written by the tests

A case with a plot pair shows the tested values against their reference in a light and a dark version. The test writes the pair with the same numbers it asserts, through the `validation_plot` fixture of proteus-mpl. This command writes all pairs to `docs/assets/validation/`:

```console
pytest -m reference_pinned tests --validation-plots
```

Without `--validation-plots` the tests assert and write nothing. The command makes every plot again; commit only the pair of the case you changed, because the bytes match only for the same matplotlib and Pillow versions. The integration cases need `FWL_DATA` with the evolution tracks.
