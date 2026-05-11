# MODEL FOR ROTATION OF STARS (MORS)

[![MORS CI Test Suite](https://github.com/FormingWorlds/MORS/actions/workflows/tests.yaml/badge.svg)](https://github.com/FormingWorlds/MORS/actions)
![Coverage](https://gist.githubusercontent.com/lsoucasse/a25c37a328839edd00bb32d8527aec30/raw/covbadge.svg)
[![License](https://img.shields.io/github/license/FormingWorlds/MORS?label=License)](https://github.com/FormingWorlds/MORS/blob/main/LICENSE.md)
[![PyPI](https://img.shields.io/pypi/v/fwl-mors?label=PyPI)](https://pypi.org/project/fwl-mors/)

MORS is a Python package for modelling the rotational spin-down and high-energy (X-ray, EUV, Ly-α) emission evolution of low-mass stars. It implements the model of [Johnstone, Bartel & Güdel (2021)](https://www.aanda.org/articles/aa/abs/2021/05/aa38407-20/aa38407-20.html) and is the stellar evolution model integrated into the [PROTEUS](https://proteus-framework.org/PROTEUS) framework.

**Documentation:** https://proteus-framework.org/MORS/

## Install

```bash
pip install fwl-mors
mors download all
```

## Quickstart

```python
import mors

star = mors.Star(Mstar=1.0, Prot=2.7)  # 1 Msun, initial rotation period at 1 Myr
print(star.Lx(150.0))                  # X-ray luminosity at 150 Myr [erg s-1]
```

## Citation

If you use MORS in published work, please cite:

- [Johnstone, Bartel & Güdel (2021)](https://www.aanda.org/articles/aa/abs/2021/05/aa38407-20/aa38407-20.html), *A&A*, 649, A96 (rotation and XUV evolution model)
- [Spada et al. (2013)](https://iopscience.iop.org/article/10.1088/0004-637X/776/2/87/meta), *ApJ*, 776, 87 (stellar evolution tracks)

If you use the model cluster distribution or percentiles, also cite the rotation-measurement sources in Table 1 of Johnstone et al. (2021).