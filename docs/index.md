# MORS

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/docs.yaml?branch=main&label=Docs)](https://proteus-framework.org/MORS/)
[![codecov](https://img.shields.io/codecov/c/github/FormingWorlds/MORS/main?label=coverage&logo=codecov)](https://app.codecov.io/gh/FormingWorlds/MORS)
[![Unit Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/tests.yaml?branch=main&label=Unit%20Tests)](https://github.com/FormingWorlds/MORS/actions/workflows/tests.yaml)
[![Integration Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/nightly.yml?branch=main&label=Integration%20Tests)](https://github.com/FormingWorlds/MORS/actions/workflows/nightly.yml)

**MORS** (Model for Rotation of Stars) is the stellar-evolution module of the [PROTEUS](https://proteus-framework.org/PROTEUS) coupled atmosphere-interior evolution framework. It models the rotational spin-down and high-energy (X-ray, EUV, Lyman-α) emission of low-mass stars (0.1 to 1.25 solar masses) over their lifetimes, following the rotation-activity model of Johnstone, Bartel & Güdel ([2021](Reference/publications.md#mors-publications)). Bolometric luminosity, radius, and effective temperature as functions of mass and age come from the stellar-structure tracks of Spada et al. ([2013](Reference/publications.md#bibliography)).

!!! info "PROTEUS framework"
    MORS is the stellar rotation and XUV evolution model integrated into the PROTEUS framework, a modular Python framework that simulates the coupled evolution of the atmospheres and interiors of rocky planets and exoplanets. Within a coupled run it supplies the stellar radius, effective temperature, bolometric instellation, and the XUV flux history that drives atmospheric heating and escape. See [Coupling to PROTEUS](Explanations/proteus.md) for how it plugs into the framework, and the [PROTEUS documentation](https://proteus-framework.org/PROTEUS) for the wider model.

If you plan to contribute to MORS, please read our [Code of Conduct](Community/CODE_OF_CONDUCT.md). If you are running into problems, please do not hesitate to raise an [Issue](https://github.com/FormingWorlds/MORS/issues).

!!! tip "New to MORS?"
    Go to [getting started](getting_started.md) for a quick path and basic usage.

## Citation and licence

When publishing results calculated using this code, please cite both the Johnstone, Bartel & Güdel ([2021](Reference/publications.md#mors-publications)) rotation and XUV evolution model and the Spada et al. ([2013](Reference/publications.md#bibliography)) stellar-evolution tracks. MORS is released under the [MIT license](https://github.com/FormingWorlds/MORS/blob/main/LICENSE.md).
