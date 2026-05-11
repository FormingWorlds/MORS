# Find habitable zone boundaries

Compute habitable zone (HZ) boundary orbital distances in AU as a function of stellar mass and age using `mors.aOrbHZ`.

## Prerequisites

Make sure the package and stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).

!!! note "Citation"
    If you use these HZ boundaries in published research, cite Kopparapu et al. (2013) [^kopparapu] for the HZ prescription and Spada et al. (2013) [^spada] for the stellar parameters used.

---

## Step 1: Compute HZ boundaries for a single stellar mass

By default, `aOrbHZ` uses stellar parameters at 5000 Myr if `Age` is not specified:

```python
import mors

hz = mors.aOrbHZ(Mstar=1.0)
```

The returned dictionary contains six boundary distances:

| Key | Description |
|---|---|
| `RecentVenus` | Inner edge (recent Venus limit) |
| `RunawayGreenhouse` | Inner edge (runaway greenhouse) |
| `MoistGreenhouse` | Inner edge (moist greenhouse) |
| `MaximumGreenhouse` | Outer edge (maximum greenhouse) |
| `EarlyMars` | Outer edge (early Mars limit) |
| `HZ` | Midpoint of `MoistGreenhouse` and `MaximumGreenhouse` |

```python
for key, val in hz.items():
    print(f"{key}: {val:.4f} AU")
```

---

## Step 2: Specify a stellar age

```python
import mors

hz = mors.aOrbHZ(Mstar=1.0, Age=1000.0)  # 1 Gyr
print(hz["HZ"])
```

---

## Step 3: Compute HZ boundaries for multiple masses

Pass an array of masses to get arrays back in the dictionary:

```python
import numpy as np
import mors

masses = np.array([0.3, 0.5, 0.8, 1.0])
hz = mors.aOrbHZ(Mstar=masses, Age=5000.0)

print(hz["HZ"])               # array of HZ midpoints in AU
print(hz["RunawayGreenhouse"])
```

---

## Step 4: Access HZ boundaries from a `Star` object

When a `Star` is created, HZ boundaries are automatically computed and stored as `star.aOrbHZ`:

```python
import mors

star = mors.Star(Mstar=1.0, Omega=1.0)
print(star.aOrbHZ["HZ"])
print(star.aOrbHZ["MoistGreenhouse"])
```

---

## Common pitfalls

- `Age` is in **Myr**, not years or Gyr.
- The `HZ` key is the midpoint of `MoistGreenhouse` and `MaximumGreenhouse`, not `RunawayGreenhouse`.
- When passing an array for `Mstar`, each value in the returned dictionary is an array of the same length.

---

[^kopparapu]: Kopparapu, R. K., Ramirez, R., Kasting, J. F., et al. (2013). Habitable zones around main-sequence stars: new estimates. *The Astrophysical Journal, 765*(2), 131. https://doi.org/10.1088/0004-637X/765/2/131

[^spada]: Spada, F., Demarque, P., Kim, Y.-C., & Sills, A. (2013). The radius discrepancy in low-mass stars: single versus binaries. *The Astrophysical Journal, 776*(2), 87. https://doi.org/10.1088/0004-637X/776/2/87