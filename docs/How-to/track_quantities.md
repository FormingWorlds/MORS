# Find stellar quantities using evolution tracks

### Goal
Find basic stellar evolution properties (radius, luminosity, convective turnover time, moments of inertia, etc.) as a function of **stellar mass** and **age**, using the Spada et al. (2013) tracks bundled with MORS. Optionally, stellar evolution quantities according to the Baraffe model (Baraffe et al., 2002) can be found.

### Prerequisites
Install MORS and download the required data:

```bash
pip install fwl-mors
mors download all
```

!!! Units
    `Mstar` in **M☉**, `Age` in **Myr**. Output units depend on the quantity (listed below).

## Spada tracks

### Available quantities

- `Rstar` — radius (**R☉**)
- `Lbol` — bolometric luminosity (**L☉**)
- `Teff` — effective temperature (**K**)
- `Itotal` — total moment of inertia (**g cm²**)
- `Icore` — core moment of inertia (**g cm²**)
- `Ienv` — envelope moment of inertia (**g cm²**)
- `Mcore` — core mass (**M☉**)
- `Menv` — envelope mass (**M☉**)
- `Rcore` — core radius (**R☉**)
- `tau` — convective turnover time (**days**)
- `dItotaldt` — d(Itotal)/dt (**g cm² Myr⁻¹**)
- `dIcoredt` — d(Icore)/dt (**g cm² Myr⁻¹**)
- `dIenvdt` — d(Ienv)/dt (**g cm² Myr⁻¹**)
- `dMcoredt` — d(Mcore)/dt (**M☉ Myr⁻¹**)
- `dRcoredt` — d(Rcore)/dt (**R☉ Myr⁻¹**)

**Important definition note:** “core” and “envelope” here follow the rotation model definitions:
- core = everything interior to the outer convective zone
- envelope = the outer convective zone
---

### Option 1: Call a property function directly

Each quantity has a dedicated function. For example, stellar radius:

```python
import mors
Rstar = mors.Rstar(1.0, 1000.0)  # Rsun
print(Rstar)
```

---

### Option 2: Use the generic accessor (`Value`)

If you want to choose the quantity by name at runtime:

```python
import mors
Rstar = mors.Value(1.0, 1000.0, "Rstar")
print(Rstar)
```

---

### Option 3: Vectorized inputs (arrays/lists)

These functions accept lists or NumPy arrays for mass and/or age.

**Multiple masses, one age → 1D array**
```python
import numpy as np
import mors

masses = np.array([0.8, 1.0, 1.2])
R = mors.Rstar(masses, 1000.0)
print(R.shape)  # (3,)
```

**One mass, multiple ages → 1D array**
```python
import numpy as np
import mors

ages = np.array([10.0, 100.0, 1000.0])
L = mors.Lbol(1.0, ages)
print(L.shape)  # (3,)
```

**Multiple masses and multiple ages → 2D array**
```python
import numpy as np
import mors

masses = np.array([0.8, 1.0, 1.2])
ages   = np.array([10.0, 100.0, 1000.0])
T = mors.Teff(masses, ages)
print(T.shape)  # (len(masses), len(ages))
```

**Multiple quantities via `Value`**
```python
import numpy as np
import mors

masses = np.array([0.9, 1.0])
ages   = np.array([100.0, 1000.0])
vals = mors.Value(masses, ages, ["Rstar", "Lbol", "tau"])
# adds an extra dimension for the quantity list
print(vals.shape)
```

---

### Performance tip: pre-load a mass track (`LoadTrack`)

The first time you call one of these functions, MORS loads and caches Spada tracks and writes a cache file (e.g., `SEmodels.pickle`) to speed up future runs. This cache can be deleted safely; it will be regenerated as needed.

If you will query many ages for a particular mass, pre-load that mass track:

```python
import mors
mors.LoadTrack(1.02)
```

If it’s already loaded, this call does nothing.

---

## Baraffe tracks 

MORS also provides access to Baraffe et al. (2002) tracks, which use **different units** than the Spada helpers above.

!!! Baraffe units
    `Mstar` in **M☉** (valid range: ~0.01–1.4), `time` in **years (yr)**.

### Step 1. Load a Baraffe track (with interpolation)
```python
import mors

Mstar = 0.5
baraffe = mors.BaraffeTrack(Mstar)
```

`BaraffeTrack` performs mass interpolation (if needed) and interpolates time onto a fine grid.

### Step 2. Query radius, luminosity, and “solar constant”
```python
time_yr = 1e7  # years

Rstar = baraffe.BaraffeStellarRadius(time_yr)          # Rsun
Lbol  = baraffe.BaraffeLuminosity(time_yr)             # Lsun
Flux  = baraffe.BaraffeSolarConstant(time_yr, 1.0)     # W m^-2 at 1 AU
```

`BaraffeSolarConstant(time, distance)` expects `distance` in **AU**.

---

### Common pitfalls
- Spada helpers use `Age` in **Myr**; Baraffe helpers use `time` in **yr**.
- “core” and “envelope” are defined by the rotation model (not the hydrogen-burning core definition).
- The first Spada call can be slower due to model loading + cache generation.
