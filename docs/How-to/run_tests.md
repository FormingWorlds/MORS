# Testing suite

This page describes the MORS test suite and how to run it. The suite is
organised into tiers so that fast, mocked tests run on every pull request while
the slower tests that run the real evolutionary-track model run nightly. Every
source file has a companion test file: the spectral synthesis pipeline, the
`Spectrum` class, the rotation, activity, and high-energy emission model, the
rotation-evolution solver, the `Cluster` class, the Baraffe and Spada track
interpolation, the coupled `Star` model, and the command-line, logging, and
data-download utilities.

## Test tiers

Every test file declares a tier marker that decides where and how often it runs:

| Marker | What it tests | Runs |
|---|---|---|
| `unit` | Python logic with the track lookups mocked, under 100 ms each | Every pull request |
| `smoke` | A real track lookup on a single star and age | Every pull request |
| `integration` | The real Baraffe / Spada evolution model | Nightly |
| `slow` | Full physics validation | Nightly |

The `integration` tests download and run the real tracks, so they need
`FWL_DATA` set and take minutes; keeping them in the nightly tier keeps the
pull-request feedback fast.

## Running the tests

### Prerequisites

Install MORS with the development dependencies:

```bash
pip install -e .[develop]
```

Download the stellar evolution data (required for the `integration` tier):

```bash
export FWL_DATA=/path/to/your/data
mors download all
```

### Run the pull-request tiers

```bash
pytest -m "(unit or smoke) and not skip"
```

### Run the full suite (including the real-track tiers)

```bash
pytest -m "(unit or smoke or integration or slow) and not skip"
```

### Run a specific file or tier

```bash
pytest tests/test_spectrum.py
pytest -m unit
pytest -m integration
```

### View coverage

```bash
coverage run -m pytest -m "(unit or smoke or integration or slow) and not skip"
coverage report
```

## Test-quality tooling

Two checks run on every pull request alongside the tests:

```bash
# Confirm every test carries a tier marker
bash tools/validate_test_structure.sh

# Enforce the test-quality rules against a locked baseline
python tools/check_test_quality.py --check
```

The quality check rejects new happy-path tests: each test needs a docstring, an
edge case, more than one meaningful assertion, and, on a physics source, a
physical invariant. Two advisory reports list follow-up work:

```bash
python tools/check_test_quality.py --reference-pinned-status
python tools/check_test_quality.py --physics-invariant-status
```

## Current test files

The suite runs about 270 tests and covers roughly 99% of the source. The mocked
unit tier runs on every pull request; the real-model integration tier runs
nightly.

### Unit tier

- `test_spectrum.py`: the `Spectrum` class and band helpers. Wavelength-to-band
  lookup, surface / 1 AU flux scaling, Planck surface flux, spectrum
  sanitisation, band integration, spectral extensions, and TSV round-trip.
- `test_synthesis.py`: spectral synthesis. Flux-budget closure, band-scale
  factors, per-band rescaling, and the modern-property fit, with the stellar
  model mocked.
- `test_physicalmodel.py`: rotation, activity, and high-energy emission. The
  X-ray, EUV, and Lyman-alpha luminosities, the Rossby number and convective
  turnover time, the core and envelope torques, the mass-loss and escape
  relations, and the habitable-zone boundaries, with the structure model mocked.
- `test_rotevo.py`: rotation-evolution integration. The forward-Euler,
  Runge-Kutta, Runge-Kutta-Fehlberg, and Rosenbrock steppers and the spin-down
  invariants, with the rate law and structure mocked.
- `test_cluster.py`: the `Cluster` orchestration and percentile statistics, with
  the member stars mocked.
- `test_miscellaneous.py`: shared helpers. Index lookups, array loading, the
  activity lifetime, and the integrated-emission fluence.
- `test_data.py`: evolutionary-track download, with the network and filesystem
  mocked.
- `test_cli.py`: the command-line interface, with the downloads mocked.
- `test_logs.py`: the logger setup and the exception hook.

### Integration tier

- `test_baraffe.py`: the Baraffe et al. (2015) track interpolation. Pins
  luminosity, radius, and insolation at two masses and asserts luminosity rises
  with mass. Baraffe tracks use time in **years**, not Myr.
- `test_stellarevo.py`: the Spada et al. (2013) structure-track interpolation.
  Pins the solar calibration and asserts the main-sequence mass-luminosity
  monotonicity.
- `test_star.py`: the coupled `Star` model. Pins the solar luminosity in cgs for
  a solar-mass star at the solar age and the model output for both
  time-integration methods, and exercises the full quantity-getter surface.

## Validation anchors

Each physics source has a validation page naming the published benchmark or
analytical limit that anchors its reference-pinned test:
[Baraffe tracks](../Validation/baraffe.md),
[stellar evolution tracks](../Validation/stellarevo.md),
[Star model](../Validation/star.md),
[rotation evolution](../Validation/rotevo.md),
[activity and habitable zone](../Validation/physicalmodel.md),
[cluster percentiles](../Validation/cluster.md),
[Spectrum](../Validation/spectrum.md), and
[spectral synthesis](../Validation/synthesis.md).

## Continuous integration

| Pipeline | Trigger | What it runs |
|---|---|---|
| Pull-request checks | Every pull request | The `unit` and `smoke` tiers, the marker validator, the test-quality check, and the coverage ratchet guard, under a 10-minute cap |
| Nightly | 03:00 UTC daily | The full suite with coverage, uploaded to [Codecov](https://app.codecov.io/gh/FormingWorlds/MORS) |

Coverage gates move one way: a pull-request check blocks any change that lowers
them, and the thresholds are raised toward the 90% ecosystem target as coverage
improves. The pull-request tier covers the mocked unit surface; the nightly tier
adds the real-track coverage.
