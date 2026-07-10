# Testing suite

This page describes the MORS test suite and how to run it. The suite is
organised into tiers so that fast, mocked tests run on every pull request while
the slower tests that run the real evolutionary-track model run nightly. It
covers the spectral synthesis pipeline, the `Spectrum` class, the Baraffe and
Spada track interpolation, and the coupled `Star` model. The high-energy
emission model (`physicalmodel.py`), the rotation-evolution solver
(`rotevo.py`), and the `Cluster` class do not yet have dedicated test files.

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

### `test_spectrum.py`: Spectrum class and helpers (`unit`)

Mocked unit tests for `mors.spectrum`, no stellar evolution data required.
Covers the wavelength-to-band lookup, the surface / 1 AU flux-scaling
round-trip, the Planck surface-flux monotonicity with temperature, the loader's
wavelength ordering and flux floor, the constant-integrand band integral, the
short-wave and Planck extensions, and the TSV round-trip.

### `test_synthesis.py`: spectral synthesis (`unit`)

Mocked unit tests for `mors.synthesis`. Replaces `Value`, `Percentile`, `Lxuv`,
`Lbol`, and `PlanckFunction_surf` with lightweight fakes, so no stellar
evolution data are required. Covers the flux-budget closure, the band-scale
factors, the per-band rescaling, and the modern-property fit.

### `test_baraffe.py`: Baraffe tracks (`integration`)

Runs the Baraffe et al. (2015) track interpolation, pinning luminosity, radius,
and insolation at two stellar masses and asserting luminosity rises with mass.
Baraffe tracks use time in **years**, not Myr.

### `test_stellarevo.py`: Spada structure tracks (`integration`)

Runs the Spada et al. (2013) structure-track interpolation, pinning the solar
calibration (a 1 Msun star at the solar age reproduces the Sun) and asserting
the main-sequence luminosity-mass monotonicity.

### `test_star.py`: coupled Star model (`integration`)

Runs the coupled rotation and activity `Star` model. Pins the solar luminosity
in cgs units for a solar-mass star at the solar age, and pins the model output
for both time-integration methods.

## Validation anchors

Each physics source has a validation page listing the published benchmark,
analytical limit, or self-consistency identity that anchors its
reference-pinned test: [Baraffe tracks](../Validation/baraffe.md),
[stellar evolution tracks](../Validation/stellarevo.md),
[Star model](../Validation/star.md), [Spectrum](../Validation/spectrum.md),
and [spectral synthesis](../Validation/synthesis.md).

## Continuous integration

| Pipeline | Trigger | What it runs |
|---|---|---|
| Pull-request checks | Every pull request | The `unit` and `smoke` tiers, the marker validator, the test-quality check, and the coverage ratchet guard, under a 10-minute cap |
| Nightly | 03:00 UTC daily | The full suite with coverage, uploaded to [Codecov](https://app.codecov.io/gh/FormingWorlds/MORS) |

Coverage gates ratchet upward toward the 90% ecosystem target and are never
lowered. The pull-request tier covers the mocked unit surface; the nightly tier
adds the real-track coverage.
