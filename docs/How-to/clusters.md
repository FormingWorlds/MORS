## Cluster evolution calculation (How-to)

### Goal
Compute rotation/activity evolution tracks for a **cluster of stars**, then (a) inspect per-star tracks, (b) evaluate cluster distributions at a given age, and (c) save/reload the cluster to avoid recomputation.

### Prerequisites
Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

> **Units:** `Mstar` in **M☉**, `Age` in **Myr**, `Prot` in **days**, `Omega` in **Ω☉**.

---

### Step 1 — Create a cluster from arrays

Create arrays/lists of masses and rotation rates (same length). If `Age` is omitted, MORS interprets `Omega` as the **initial (~1 Myr)** rotation rate.

```python
import numpy as np
import mors

Mstar = np.array([1.0, 0.5, 0.75])
Omega = np.array([10.0, 10.0, 10.0])

cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)
```

To show progress while tracks are computed, enable `verbose`:

```python
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, verbose=True)
```

---

### Step 2 — Fit tracks through a specified age (optional)

If you provide `Age`, MORS fits tracks so that each star passes through the given rotation rate at that age.

**One age applied to all stars**
```python
import numpy as np
import mors

Mstar = np.array([1.0, 0.5, 0.75])
Omega = np.array([50.0, 30.0, 40.0])

cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, Age=100.0)  # Myr
```

**Different ages for each star**
```python
import numpy as np
import mors

Mstar = np.array([1.0, 0.5, 0.75])
Omega = np.array([50.0, 30.0, 40.0])
Age   = np.array([80.0, 120.0, 100.0])  # Myr; same length as Mstar/Omega

cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, Age=Age)
```

---

### Step 3 — Access per-star tracks

Each star is a `mors.Star` instance stored in `cluster.stars`.

```python
import matplotlib.pyplot as plt

plt.plot(cluster.stars[0].AgeTrack, cluster.stars[0].LxTrack)
plt.plot(cluster.stars[1].AgeTrack, cluster.stars[1].LxTrack)
plt.plot(cluster.stars[2].AgeTrack, cluster.stars[2].LxTrack)
plt.show()
```

Some versions also expose `stars0`, `stars1`, ... as attributes:

```python
plt.plot(cluster.stars0.AgeTrack, cluster.stars0.LxTrack)
```

---

### Step 4 — Get cluster values at a fixed age

Use `Values(Age=..., Quantity=...)` to retrieve an array across the cluster:

```python
Lx = cluster.Values(Age=100.0, Quantity="Lx")
```

Or use the convenience method named after the quantity:

```python
Lx = cluster.Lx(100.0)
```

Plot a distribution (e.g., Lx vs mass) at a given age:

```python
import matplotlib.pyplot as plt
plt.scatter(cluster.Mstar, cluster.Lx(100.0))
plt.xlabel("Mstar [Msun]")
plt.ylabel("Lx [erg/s]")
plt.show()
```

---

### Step 5 — Save and reload (recommended for large clusters)

Cluster calculations can be expensive for many stars, so saving is recommended.

```python
cluster.Save(filename="cluster.pickle")
cluster2 = mors.Load("cluster.pickle")
```

---

### Step 6 — Evolve the built-in “model cluster” (optional)

MORS includes a composite “model cluster” distribution (derived from observed clusters at ~150 Myr evolved back to 1 Myr). You can load it and evolve it like any other cluster:

```python
import mors

Mstar, Omega = mors.ModelCluster()
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)
```

**Citation note:** If you use this model cluster distribution in research, cite the rotation-measurement sources listed in **Johnstone et al. (2020), Table 1** (150 Myr bin), in addition to the MORS model paper(s).

---

### Common pitfalls
- Arrays for `Mstar`, `Omega` (and `Age` if provided) must have matching lengths.
- `Age` is in **Myr**; `Omega` is in **Ω☉**.
- Fitting tracks using `Age` + `Omega` can be unreliable at late ages where tracks converge.
