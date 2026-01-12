# Model distribution and percentiles (How-to)

### Goal
Pick an initial rotation rate from the built-in **model rotation distribution** (Johnstone et al. 2020), inspect a star’s inferred percentile, and convert between **rotation rate and percentile** for a given stellar mass.

### Prerequisites
Make sure MORS and the stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

> **Units:** `Omega` is in units of the current solar rotation rate (**Ω☉**). `Prot` is in **days**. `Mstar` is in **M☉**.

---

### Step 1: Get the built-in “model cluster” distribution

This returns arrays of stellar masses and their **1 Myr** rotation rates (derived by evolving observed cluster distributions back to 1 Myr).

```python
import mors

Mstar_dist, Omega_dist = mors.ModelCluster()
print(Mstar_dist.shape, Omega_dist.shape)
```

**Citation note:** If you use the model cluster distribution directly in research, cite the rotation-measurement sources listed in **Johnstone et al. (2020), Table 1** (150 Myr bin), in addition to the MORS model paper(s).

---

### Step 2: Create a star by percentile

You can set initial rotation using a numeric percentile (0–100) or the strings `'slow'`, `'medium'`, `'fast'` which map to 5th/50th/95th percentiles.

```python
import mors

# numeric percentile
star_p5 = mors.Star(Mstar=1.0, percentile=5.0)

# equivalent string shortcut
star_slow = mors.Star(Mstar=1.0, percentile="slow")
```

---

### Step 3: Read back the star’s inferred percentile

Regardless of how you create the star (Omega/Prot/percentile), MORS stores the inferred percentile after computing tracks:

```python
print(star_slow.percentile)
```

---

### Step 4: Convert a rotation rate (Ω or Prot) to a percentile

**From Ω (Ω☉) to percentile**
```python
import mors
p = mors.Percentile(Mstar=1.0, Omega=10.0)
print(p)
```

**From Prot (days) to percentile**
```python
import mors
p = mors.Percentile(Mstar=1.0, Prot=1.0)
print(p)
```

---

### Step 5: Convert a percentile to a rotation rate

```python
import mors
Omega_p10 = mors.Percentile(Mstar=1.0, percentile=10.0)  # returns Ω in Ω☉
print(Omega_p10)
```

---

### Step 6: Control the mass window used for percentiles (`dMstarPer`)

Percentiles are computed using stars within a mass window around `Mstar`. The width is controlled by `dMstarPer` (default: 0.1 M☉). To change it, modify parameters and pass them into `Star`:

```python
import mors

params = mors.NewParams(dMstarPer=0.05)
star = mors.Star(Mstar=1.0, percentile="medium", params=params)
```

---

### Step 7: Use a custom rotation distribution (optional)

If you have your own mass+rotation distribution (instead of the built-in 1 Myr model distribution), pass it into `Percentile`.

**Using Ω distribution**
```python
import numpy as np
import mors

MstarDist = np.array([1.0, 1.0, 1.0, 0.9, 1.1])
OmegaDist = np.array([2.0, 5.0, 10.0, 3.0, 7.0])

p = mors.Percentile(Mstar=1.0, Omega=6.0, MstarDist=MstarDist, OmegaDist=OmegaDist)
print(p)
```

**Using Prot distribution**
```python
import numpy as np
import mors

MstarDist = np.array([1.0, 1.0, 0.9, 1.1])
ProtDist  = np.array([12.0, 6.0, 9.0, 7.0])  # days

p = mors.Percentile(Mstar=1.0, Prot=8.0, MstarDist=MstarDist, ProtDist=ProtDist)
print(p)
```

---

### Common pitfalls
- Percentiles here refer to the **initial (~1 Myr)** distribution used by the model cluster.
- `Omega` is **Ω☉**, not rad/s. `Prot` is **days**.
- If your custom distribution is sparse or covers a narrow mass range, percentile estimates can become unstable.
