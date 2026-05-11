[![MORS CI Test Suite](https://github.com/FormingWorlds/MORS/actions/workflows/tests.yaml/badge.svg)](https://github.com/FormingWorlds/MORS/actions)
![Coverage](https://gist.githubusercontent.com/lsoucasse/a25c37a328839edd00bb32d8527aec30/raw/covbadge.svg)
[![License](https://img.shields.io/github/license/FormingWorlds/MORS?label=License)](https://github.com/FormingWorlds/MORS/blob/main/LICENSE.md)
[![PyPI](https://img.shields.io/pypi/v/fwl-mors?label=PyPI)](https://pypi.org/project/fwl-mors/)


# MODEL FOR ROTATION OF STARS (MORS)

**MORS** is a program designed to model stellar rotation and evolution. The package can be used to calculate evolutionary tracks for stellar rotation and X-ray, EUV, and Ly-alpha emission for stars with masses between 0.1 and 1.25 solar masses. It also allows the user to get basic stellar parameters, such as stellar radius and luminosity, as functions of mass and age using the stellar evolution models of Spada et al. ([2013](Reference/publications.md#bibliography)). 

!!! info "PROTEUS framework"
    MORS is the stellar rotation and XUV evolution model integrated into the PROTEUS framework,  a modular Python framework that simulates the coupled evolution of the atmospheres and interiors of rocky planets and exoplanets. The documentation for PROTEUS can be found [here](https://proteus-framework.org/PROTEUS). 

If you plan to contribute to MORS, please read our [Code of Conduct](Community/CODE_OF_CONDUCT.md). If you are running into problems, please do not hesitate to raise an [Issue](https://github.com/FormingWorlds/MORS/issues).


!!! tip "New to MORS?"
    Go to [getting started](getting_started.md) for a quick path and basic usage. 

## Citation and licence

 When publishing results that were calculated using this code, both the Johnstone et al.  ([2021](Reference/publications.md#mors-publications)) paper and Spada et al. ([2013](Reference/publications.md#bibliography)) should be cited. Please also see the included [license](https://github.com/FormingWorlds/MORS/blob/main/LICENSE.md).