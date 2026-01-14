# MODEL FOR ROTATION OF STARS (MORS)

MORS is a Python package (distributed as `fwl-mors`) used in the [PROTEUS framework](https://github.com/FormingWorlds/PROTEUS) to model **stellar rotation** and **high-energy emission (X-ray, EUV, Ly-α)** evolution.  
It implements the model of **Johnstone et al. (2021)** and provides stellar evolution quantities based on **Spada et al. (2013)** (plus optional Baraffe tracks).

> **Note:** This version includes the fix for the EUV1 → EUV2 conversion.

## Install

```bash
pip install fwl-mors
```

### Required data: stellar evolution tracks
Download the stellar evolution tracks (stored on OSF):

```bash
mors download all
mors env
```

By default, data follow the XDG base directory convention. You can override the data root with:

```bash
export FWL_DATA=/path/to/data
```

Or set a per-script directory:

```python
import mors
star_evo = mors.StarEvo(starEvoDir="path/to/evolution-tracks")
```

## Quickstart

```python
import mors
import matplotlib.pyplot as plt

star = mors.Star(Mstar=1.0, Prot=2.7)     # 1 Msun star, initial rotation period in days (at age ~1 Myr)
print(star.Lx(150.0))                    # X-ray luminosity at 150 Myr

plt.plot(star.AgeTrack, star.LxTrack)
plt.xlabel(f"Age [{star.Units['Age']}]")
plt.ylabel(f"Lx [{star.Units['Lx']}]")
plt.show()
```

## Documentation 

You can find the complete documentation [here](https://proteus-framework.org/MORS/). 

## Citation

When publishing results computed with MORS, please cite:
- **Johnstone et al. (2021)** for the rotation/XUV evolution model
- **Spada et al. (2013)** for the stellar evolution tracks used for stellar properties

If you use the model cluster distribution/percentiles, also cite the rotation-measurement sources referenced in **Johnstone et al. (2020)** (Table 1, ~150 Myr bin).
