# Find stellar quantities from evolution tracks

Find basic stellar evolution properties (radius, luminosity, convective turnover time, moments of inertia, etc.) as a function of stellar mass and age, using the Spada et al. (2013) [^spada] tracks bundled with MORS. Baraffe et al. (2015) [^baraffe] tracks are also available.

## Prerequisites

Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).

---

## Spada tracks

### Available quantities

| Function | Key for `Value` | Output units |
|---|---|---|
| `mors.Rstar` | `'Rstar'` | R☉ |
| `mors.Lbol` | `'Lbol'` | L☉ |
| `mors.Teff` | `'Teff'` | K |
| `mors.Itotal` | `'Itotal'` | g cm² |
| `mors.Icore` | `'Icore'` | g cm² |
| `mors.Ienv` | `'Ienv'` | g cm² |
| `mors.Mcore` | `'Mcore'` | M☉ |
| `mors.Menv` | `'Menv'` | M☉ |
| `mors.Rcore` | `'Rcore'` | R☉ |
| `mors.tauConv` | `'tauConv'` | days |
| `mors.dItotaldt` | `'dItotaldt'` | g cm² Myr⁻¹ |
| `mors.dIcoredt` | `'dIcoredt'` | g cm² Myr⁻¹ |
| `mors.dIenvdt` | `'dIenvdt'` | g cm² Myr⁻¹ |
| `mors.dMcoredt` | `'dMcoredt'` | M☉ Myr⁻¹ |
| `mors.dRcoredt` | `'dRcoredt'` | R☉ Myr⁻¹ |

!!! info "Core and envelope definitions"
    In MORS, "core" means everything interior to the outer convective zone, and "envelope" means the outer convective zone itself. This follows the rotation model convention and differs from the nuclear-burning core definition used in some other contexts.

---

### Option 1: Call a quantity function directly

Each quantity has a dedicated function:

```python
import mors

Rstar = mors.Rstar(1.0, 1000.0)   # Mstar=1.0 Msun, Age=1000 Myr
print(Rstar)                        # in Rsun
```

---

### Option 2: Use the generic `Value` accessor

Choose the quantity by name at runtime:

```python
import mors

Rstar = mors.Value(1.0, 1000.0, 'Rstar')
print(Rstar)
```

---

### Option 3: Vectorised inputs

All functions accept scalars, lists, or NumPy arrays for mass and age.

**Multiple masses, one age — returns a 1D array:**

```python
import numpy as np
import mors

masses = np.array([0.8, 1.0, 1.2])
R = mors.Rstar(masses, 1000.0)
print(R.shape)  # (3,)
```

**One mass, multiple ages — returns a 1D array:**

```python
import numpy as np
import mors

ages = np.array([10.0, 100.0, 1000.0])
L = mors.Lbol(1.0, ages)
print(L.shape)  # (3,)
```

**Multiple masses and multiple ages — returns a 2D array:**

```python
import numpy as np
import mors

masses = np.array([0.8, 1.0, 1.2])
ages   = np.array([10.0, 100.0, 1000.0])
T = mors.Teff(masses, ages)
print(T.shape)  # (3, 3) — shape (len(masses), len(ages))
```

**Multiple quantities via `Value` — adds a third dimension:**

```python
import numpy as np
import mors

masses = np.array([0.9, 1.0])
ages   = np.array([100.0, 1000.0])
vals = mors.Value(masses, ages, ['Rstar', 'Lbol', 'tauConv'])
print(vals.shape)  # (2, 2, 3) — (masses, ages, quantities)
```

---

### Performance: pre-loading a mass track

On first use, MORS compiles the Spada grid and saves a cache file in the stellar evolution tracks directory. Subsequent runs load from this cache and are faster.

If you will query many ages for a specific mass, pre-load that track to avoid repeated interpolation between mass bins:

```python
import mors

mors.LoadTrack(1.02)  # does nothing if already loaded
```

---

## Baraffe tracks

MORS also provides access to Baraffe et al. (2015) [^baraffe] tracks.

!!! info "Units"
    `Mstar` in **M☉**, but time in **years (yr)** — not Myr.

### Step 1: Load a Baraffe track

```python
import mors

baraffe = mors.BaraffeTrack(Mstar=0.5)
```

`BaraffeTrack` performs mass interpolation if needed.

### Step 2: Query radius, luminosity, and flux

```python
time_yr = 1e7  # years

Rstar = baraffe.BaraffeStellarRadius(time_yr)       # Rsun
Lbol  = baraffe.BaraffeLuminosity(time_yr)          # Lsun
Flux  = baraffe.BaraffeSolarConstant(time_yr, 1.0)  # W m⁻² at 1 AU
```

`BaraffeSolarConstant(time, distance)` takes distance in **AU**.

---

## Common pitfalls

- Spada functions use `Age` in **Myr**; Baraffe functions use time in **yr**.
- The convective turnover time key is `'tauConv'`, not `'tau'`.
- "Core" and "envelope" follow the rotation model convention, not the nuclear-burning core definition.
- The first Spada call may be slower due to cache generation.

---

[^spada]: Spada, F., Demarque, P., Kim, Y.-C., & Sills, A. (2013). The radius discrepancy in low-mass stars: single versus binaries. *The Astrophysical Journal, 776*(2), 87. https://doi.org/10.1088/0004-637X/776/2/87

[^baraffe]: Baraffe, I., Homeier, D., Allard, F., & Chabrier, G. (2015). New evolutionary models for pre-main sequence and main sequence stars down to the hydrogen-burning limit. *Astronomy & Astrophysics, 577*, A42. https://doi.org/10.1051/0004-6361/201425481