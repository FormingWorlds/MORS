# MORS

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/docs.yaml?branch=main&label=Docs)](https://proteus-framework.org/MORS/)
[![codecov](https://img.shields.io/codecov/c/github/FormingWorlds/MORS/main?label=coverage&logo=codecov)](https://app.codecov.io/gh/FormingWorlds/MORS)
[![Unit Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/tests.yaml?branch=main&label=Unit%20Tests)](https://github.com/FormingWorlds/MORS/actions/workflows/tests.yaml)
[![Integration Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/nightly.yml?branch=main&label=Integration%20Tests)](https://github.com/FormingWorlds/MORS/actions/workflows/nightly.yml)

**MORS** (Model for Rotation of Stars) is the stellar-evolution module of the [PROTEUS](https://proteus-framework.org/PROTEUS) coupled atmosphere-interior evolution framework. It models the rotational spin-down and high-energy (X-ray, EUV, Lyman-α) emission of low-mass stars over their lifetimes, following the rotation-activity model of [Johnstone, Bartel & Güdel (2021)](https://www.aanda.org/articles/aa/abs/2021/05/aa38407-20/aa38407-20.html).

Given a stellar mass and an initial rotation rate, or an observed rotation percentile, MORS returns the time evolution of the rotation period, the X-ray, EUV and Lyman-α luminosities, and the bolometric luminosity, radius and effective temperature interpolated from stellar-structure tracks. Within PROTEUS it supplies the stellar XUV history that drives atmospheric escape and photochemistry.

## Model

MORS evolves the surface rotation of a low-mass star (0.1-1.25 Msun) with a wind-braking spin-down law calibrated to the rotation distributions of open clusters, then maps rotation to activity through the Rossby-number rotation-activity relation: X-ray luminosity first, then EUV and Lyman-α from empirical band scalings. Structural quantities (bolometric luminosity, radius, effective temperature) are interpolated from [Spada et al. (2013)](https://iopscience.iop.org/article/10.1088/0004-637X/776/2/87/meta) evolutionary tracks by default; Baraffe et al. (2015) tracks (0.01-1.40 Msun, no rotation model) are available as an alternative.

## Documentation

Full documentation is at **[proteus-framework.org/MORS](https://proteus-framework.org/MORS/)**, including:

- [Getting started](https://proteus-framework.org/MORS/getting_started.html): installation and a quick path to a first run.
- [Tutorial](https://proteus-framework.org/MORS/Tutorials/first_run.html): a first stellar-evolution run and how to read its output.
- [How-to guides](https://proteus-framework.org/MORS/How-to/installation.html): install, evolve a star, read tracks and activity quantities, compute habitable-zone boundaries, run the tests.
- [Explanations](https://proteus-framework.org/MORS/Explanations/rotation.html): rotation model, X-ray and EUV activity, stellar structure, spectral synthesis, and coupling to PROTEUS.
- [API reference](https://proteus-framework.org/MORS/Reference/api/index.html) and [validation anchors](https://proteus-framework.org/MORS/Validation/physicalmodel.html): every public function with NumPy-style docstrings, plus the per-source reference-pinned test inventory.

## Installation

```console
pip install fwl-mors
```

Or, for development:

```console
git clone https://github.com/FormingWorlds/MORS.git
cd MORS
pip install -e .[develop,docs]
```

The `docs` extra pulls in [Zensical](https://zensical.org/) so you can build this documentation locally with `zensical serve`.

### Stellar evolution data

MORS ships without the stellar-evolution tracks, which live in the [OSF repository](https://osf.io/9u3fb/). Set the `FWL_DATA` environment variable to the directory where the data should live, then download the tracks:

```console
export FWL_DATA=/your/local/path/FWL_DATA   # add to ~/.bashrc to persist
mors download all
```

## Quick start

```python
import mors

star = mors.Star(Mstar=1.0, Prot=2.7)  # 1 Msun, initial rotation period at 1 Myr
print(star.Lx(150.0))                  # X-ray luminosity at 150 Myr [erg s-1]
```

See the [first-run tutorial](https://proteus-framework.org/MORS/Tutorials/first_run.html) for the full walkthrough.

## Citation

If you use MORS in published work, please cite:

- [Johnstone, Bartel & Güdel (2021)](https://www.aanda.org/articles/aa/abs/2021/05/aa38407-20/aa38407-20.html), *A&A*, 649, A96 (rotation and XUV evolution model)
- [Spada et al. (2013)](https://iopscience.iop.org/article/10.1088/0004-637X/776/2/87/meta), *ApJ*, 776, 87 (stellar evolution tracks)

If you use the model cluster distribution or percentiles, also cite the rotation-measurement sources in Table 1 of Johnstone et al. (2021).

## License

[MIT License](LICENSE.md). MORS is part of the [PROTEUS framework](https://proteus-framework.org/).
