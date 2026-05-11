# Testing suite

This page describes the current MORS test suite and how to run it. The suite covers the spectral synthesis pipeline in full, the Spectrum class, and regression tests for the Spada and Baraffe stellar evolution tracks with two ODE solvers. The physical model (`physicalmodel.py`), rotational evolution solver (`rotevo.py`), and parameter handling are not yet covered by dedicated tests.

## Running the tests

### Prerequisites

Install MORS with the development dependencies:

```bash
pip install -e .[develop]
```

Download the stellar evolution data (required for Spada and Baraffe track tests):

```bash
export FWL_DATA=/path/to/your/data
mors download all
```

### Run the full suite

```bash
coverage run -m pytest
```

### Run a specific file

```bash
pytest tests/test_spada_RB.py
pytest tests/test_spectrum.py
```

### Run with verbose output

```bash
pytest -v
```

### View coverage report

```bash
coverage run -m pytest
coverage report
```

---

## Current test files

### `test_spada_FE.py`: Spada tracks, Forward Euler solver

Runs four parametrised integration tests using the Forward Euler ODE solver. Each test creates a `mors.Star` at a given mass and initial rotation rate and checks three quantities at a given age against regression values from a known-good run:

| Quantity | Description |
|---|---|
| `Rstar` | Stellar radius (Rsun) |
| `Lbol` | Bolometric luminosity (erg s⁻¹) |
| `Leuv` | Total EUV luminosity (erg s⁻¹) |

Tolerance: `rtol=1e-6`. The test calls `mors.DownloadEvolutionTracks('Spada')` to ensure data are present.

---

### `test_spada_RB.py`: Spada tracks, Rosenbrock solver

Identical structure to `test_spada_FE.py` but uses the default `RosenbrockFixed` solver. The expected values differ from the Forward Euler test because the two solvers produce slightly different numerical results at the same tolerance settings.

---

### `test_baraffe.py`: Baraffe tracks

Runs two parametrised integration tests using Baraffe et al. (2015) tracks. Each test creates a `mors.BaraffeTrack` at a given mass and checks three quantities at a given age against regression values:

| Quantity | Description |
|---|---|
| `BaraffeLuminosity` | Bolometric luminosity (Lsun) |
| `BaraffeStellarRadius` | Stellar radius (Rsun) |
| `BaraffeSolarConstant` | Bolometric flux at given distance (W m⁻²) |

Tolerance: `rtol=1e-5`. Note that Baraffe tracks use time in **years**, not Myr.

---

### `test_spectrum.py`: Spectrum class and helpers

Unit tests for `mors.spectrum`. No stellar evolution data required. Covers:

- `WhichBand`: wavelength-to-band lookup, including overlap regions
- `ScaleToSurf` / `ScaleTo1AU`: round-trip scaling consistency
- `PlanckFunction_surf`: monotonically increasing with temperature, positive values
- `Spectrum.LoadDirectly`: ascending wavelength ordering, NaN/zero flux sanitisation, binwidth length
- `Spectrum.CalcBandFluxes`: band integration with constant flux (analytically verifiable)
- `Spectrum.ExtendShortwave`: extension length, wavelength bounds, constant flux value
- `Spectrum.ExtendPlanck`: extension length, wavelength bounds, positive flux
- TSV round-trip: write and reload with tolerance matching the `%1.4e` format

---

### `test_synthesis.py`: Spectral synthesis

Unit tests for `mors.synthesis`. Uses `monkeypatch` to replace `Value`, `Percentile`, `Lxuv`, `Lbol`, and `PlanckFunction_surf` with lightweight fakes, so no stellar evolution data are required. Covers:

- `GetProperties`: flux budget consistency: $F = L / (4\pi \, \mathrm{AU}^2)$, UV remainder definition, Planck band integral
- `CalcBandScales`: scale factor $Q_k = F_k^\mathrm{hist} / F_k^\mathrm{modern}$ for each band
- `CalcScaledSpectrumFromProps`: correct band scale factor applied per wavelength, including overlap regions
- `FitModernProperties`: correct initial guess shape, correct unpacking of the `minimize` result for both fixed-age and free-age cases

---

## CI matrix

Tests run automatically on every push and pull request to `main` via GitHub Actions:

| OS | Python versions |
|---|---|
| Ubuntu | 3.11, 3.12, 3.13 |
| macOS | 3.11, 3.12, 3.13 |

Coverage is reported in the GitHub Actions summary. A coverage badge is generated from the `ubuntu-latest` + Python 3.12 run on `main`.